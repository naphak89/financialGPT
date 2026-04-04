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


def fetch_news(symbol: str, limit: int = 50) -> tuple[list[dict[str, Any]], str | None]:
    sym = symbol.upper().strip()
    ticker = yf.Ticker(sym, session=_HTTP)
    try:
        raw = ticker.news
    except Exception as e:
        return [], f"yfinance news failed: {e}"

    if not raw:
        return [], "No news returned for this symbol."

    articles: list[dict[str, Any]] = []
    for item in raw[:limit]:
        articles.append(
            {
                "headline": item.get("title") or "Untitled",
                "url": item.get("link") or "#",
                "source": item.get("publisher") or "Yahoo Finance",
                "datetime": item.get("providerPublishTime"),
            }
        )

    return articles, None
