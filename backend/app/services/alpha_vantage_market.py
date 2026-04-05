"""
Daily OHLC from Alpha Vantage TIME_SERIES_DAILY (free key: https://www.alphavantage.co/support/#api-key).
Free tier: ~25 requests/day.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

_AV_URL = "https://www.alphavantage.co/query"


def fetch_daily_ohlcv(
    symbol: str,
    api_key: str,
    days: int,
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    """
    Returns (quote, candles, warning). Warning is set only on failure or rate limit.
    """
    sym = symbol.upper().strip()
    # compact ≈ last 100 points; full needed when user asks for > ~100 trading days
    outputsize = "full" if days > 100 else "compact"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": sym,
        "outputsize": outputsize,
        "apikey": api_key,
    }
    try:
        r = requests.get(_AV_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return (
            {"c": None, "h": None, "l": None, "o": None},
            {"s": "no_data", "t": [], "o": [], "h": [], "l": [], "c": [], "v": []},
            f"Alpha Vantage request failed: {e}",
        )

    if "Note" in data:
        return (
            {"c": None, "h": None, "l": None, "o": None},
            {"s": "no_data", "t": [], "o": [], "h": [], "l": [], "c": [], "v": []},
            "Alpha Vantage rate limit — wait a minute or upgrade key. " + str(data.get("Note", "")),
        )
    if "Error Message" in data:
        return (
            {"c": None, "h": None, "l": None, "o": None},
            {"s": "no_data", "t": [], "o": [], "h": [], "l": [], "c": [], "v": []},
            str(data["Error Message"]),
        )

    series = data.get("Time Series (Daily)")
    if not series:
        return (
            {"c": None, "h": None, "l": None, "o": None},
            {"s": "no_data", "t": [], "o": [], "h": [], "l": [], "c": [], "v": []},
            "Alpha Vantage returned no daily series.",
        )

    dates = sorted(series.keys())[-max(days, 5) :]

    t_list: list[int] = []
    o, h, l_, c, v = [], [], [], [], []
    for d in dates:
        row = series[d]
        ts = int(
            datetime.strptime(d, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
        t_list.append(ts)
        o.append(float(row["1. open"]))
        h.append(float(row["2. high"]))
        l_.append(float(row["3. low"]))
        c.append(float(row["4. close"]))
        v.append(float(row.get("5. volume", 0) or 0))

    last = series[dates[-1]]
    quote = {
        "o": float(last["1. open"]),
        "h": float(last["2. high"]),
        "l": float(last["3. low"]),
        "c": float(last["4. close"]),
    }

    candles = {
        "s": "ok",
        "t": t_list,
        "o": o,
        "h": h,
        "l": l_,
        "c": c,
        "v": v,
    }
    return quote, candles, None
