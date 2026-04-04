"""
Yahoo Finance RSS headlines — no API key; works when yfinance JSON endpoints fail.
"""

from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any


def fetch_yahoo_rss_headlines(symbol: str, limit: int = 50) -> tuple[list[dict[str, Any]], str | None]:
    sym = symbol.upper().strip()
    q = urllib.parse.quote(sym)
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={q}&region=US&lang=en-US"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read()
    except Exception as e:
        return [], f"Yahoo RSS failed: {e}"

    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        return [], f"Yahoo RSS parse error: {e}"

    # RSS 2.0: channel/item
    items = root.findall(".//item")
    articles: list[dict[str, Any]] = []
    for it in items[:limit]:
        title_el = it.find("title")
        link_el = it.find("link")
        pub_el = it.find("pubDate")
        title = (title_el.text or "Untitled").strip() if title_el is not None else "Untitled"
        link = (link_el.text or "#").strip() if link_el is not None else "#"
        pub = pub_el.text if pub_el is not None else None
        articles.append(
            {
                "headline": title,
                "url": link,
                "source": "Yahoo Finance (RSS)",
                "datetime": pub,
            }
        )

    if not articles:
        return [], "Yahoo RSS returned no items for this symbol."

    return articles, None
