#!/usr/bin/env python3
"""
Integration smoke test for the Financial GPT API.

Usage (API must be running):
  cd backend
  python scripts/smoke_test.py

Environment:
  BASE_URL  default http://127.0.0.1:8000
  STRICT=1  exit 1 if market/news/education/feedback also fail (default: only auth failures exit 1)

Market needs ALPHA_VANTAGE_API_KEY on the server. News uses yfinance (optional RSS fallback). RAG/education needs NVIDIA/DeepSeek keys in the server env.

Exit code 1 if health or auth fails; otherwise 0 (optional routes may print warnings).
"""

from __future__ import annotations

import json
import os
import random
import string
import sys
import urllib.error
import urllib.request


def _json_req(
    method: str,
    url: str,
    body: dict | None = None,
    token: str | None = None,
) -> tuple[int, object]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            if not raw:
                return resp.status, {}
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode() or "{}"
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        return e.code, parsed
    except urllib.error.URLError as e:
        print(f"FAIL: request error: {e}", file=sys.stderr)
        return 0, {"error": str(e)}


def main() -> int:
    base = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    strict = os.environ.get("STRICT", "").lower() in ("1", "true", "yes")

    print("GET /health ...")
    code, data = _json_req("GET", f"{base}/health")
    if code != 200 or not (isinstance(data, dict) and data.get("status") == "ok"):
        print(f"FAIL: health {code} {data}")
        return 1
    print("  ok")

    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    email = f"smoke_{suffix}@example.com"
    password = "smoke-test-9"

    print(f"POST /auth/register ({email}) ...")
    code, data = _json_req(
        "POST",
        f"{base}/auth/register",
        {"email": email, "password": password},
    )
    if code != 200:
        print(f"FAIL: register {code} {data}")
        return 1
    if not isinstance(data, dict) or not data.get("access_token"):
        print(f"FAIL: no token {data}")
        return 1
    token = str(data["access_token"])
    print("  ok")

    print("GET /auth/me ...")
    code, data = _json_req("GET", f"{base}/auth/me", token=token)
    if code != 200 or not isinstance(data, dict) or data.get("email") != email:
        print(f"FAIL: me {code} {data}")
        return 1
    print("  ok")

    print("POST /auth/login ...")
    code, data = _json_req(
        "POST",
        f"{base}/auth/login",
        {"email": email, "password": password},
    )
    if code != 200 or not isinstance(data, dict) or not data.get("access_token"):
        print(f"FAIL: login {code} {data}")
        return 1
    token = str(data["access_token"])
    print("  ok")

    optional_failed = False

    print("POST /market/data ...")
    code, data = _json_req(
        "POST",
        f"{base}/market/data",
        {"symbol": "AAPL", "resolution": "D", "days": 7},
        token=token,
    )
    if code != 200:
        print(f"  warn: market {code} {data}")
        optional_failed = True
    else:
        print("  ok")

    print("POST /news/data ...")
    code, data = _json_req(
        "POST",
        f"{base}/news/data",
        {"symbol": "AAPL", "days": 7},
        token=token,
    )
    if code != 200:
        print(f"  warn: news {code} {data}")
        optional_failed = True
    else:
        print("  ok")

    print("POST /education/ask ...")
    code, data = _json_req(
        "POST",
        f"{base}/education/ask",
        {"question": "What is this document about?"},
        token=token,
    )
    if code != 200:
        print(f"  warn: education {code} {data}")
        optional_failed = True
    else:
        print("  ok")

    print("POST /feedback ...")
    code, data = _json_req(
        "POST",
        f"{base}/feedback",
        {"message_id": "smoke-msg-1", "rating": 1},
        token=token,
    )
    if code != 200:
        print(f"  warn: feedback {code} {data}")
        optional_failed = True
    else:
        print("  ok")

    if optional_failed and strict:
        print("\nSTRICT: optional route failed.", file=sys.stderr)
        return 1
    if optional_failed:
        print("\nAuth OK. Some optional routes failed (Alpha Vantage market, news, Chroma/RAG, or network).")
    else:
        print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
