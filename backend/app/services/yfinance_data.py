"""
Headlines via yfinance (no API key). Yahoo Finance public data; respect their terms.
Uses a browser-like User-Agent — Yahoo often blocks bare clients.
"""

from __future__ import annotations

from typing import Any

import requests
import yfinance as yf

_HTTP = requests.Session()
_HTTP.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
)


def _json_safe(v: Any) -> Any:
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if hasattr(v, "item"):  # numpy scalar
        try:
            return v.item()
        except Exception:
            return str(v)
    return str(v)


def fetch_news(symbol: str, limit: int = 50) -> tuple[list[dict[str, Any]], str | None]:
    sym = symbol.upper().strip()
    try:
        ticker = yf.Ticker(sym, session=_HTTP)
        raw = ticker.news
    except Exception as e:
        return [], f"yfinance news failed: {e}"

    if not raw:
        return [], "No news returned for this symbol."

    articles: list[dict[str, Any]] = []
    try:
        seq = list(raw)[:limit] if raw is not None else []
    except Exception as e:
        return [], f"yfinance news failed: {e}"

    for item in seq:
        if not isinstance(item, dict):
            continue
        articles.append(
            {
                "headline": str(item.get("title") or "Untitled"),
                "url": str(item.get("link") or "#"),
                "source": str(item.get("publisher") or "Yahoo Finance"),
                "datetime": _json_safe(item.get("providerPublishTime")),
            }
        )

    return articles, None
