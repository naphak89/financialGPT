"""
DeepSeek replies using retrieved market or news data as context (same env as RAG).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent
load_dotenv(_BACKEND_ROOT / ".env")
load_dotenv(_REPO_ROOT / "langchain-rag-tutorial" / ".env")

_log = logging.getLogger(__name__)

def _market_prompt(context: str, question: str) -> str:
    return (
        "You are a financial assistant. Answer using ONLY the market data below. "
        "If the question cannot be answered from this data, say what is missing. "
        "Do not invent prices, news, or events. Be concise and clear.\n\n---\n"
        + context
        + "\n---\n\nUser question: "
        + question
        + "\n\nAnswer:"
    )


def _news_prompt(context: str, question: str) -> str:
    return (
        "You are a financial assistant. Answer using ONLY the headlines list below. "
        "If the question cannot be answered from them, say so briefly. "
        "Do not invent stories or facts not supported by the headlines. Be concise.\n\n---\n"
        + context
        + "\n---\n\nUser question: "
        + question
        + "\n\nAnswer:"
    )


def _invoke(prompt: str) -> str:
    model = ChatDeepSeek(model="deepseek-chat")
    out = model.invoke(prompt)
    text = (out.content or "").strip()
    if not text:
        raise RuntimeError("Empty reply from model")
    return text


def format_market_context(
    symbol: str,
    days: int,
    quote: dict[str, Any],
    candles: dict[str, Any],
    warning: str | None,
) -> str:
    lines = [
        f"Ticker: {symbol.upper().strip()}",
        f"Requested lookback (calendar days target): {days} (daily bars).",
    ]
    if warning:
        lines.append(f"Data note: {warning}")
    o = quote.get("o")
    h = quote.get("h")
    low = quote.get("l")
    c = quote.get("c")
    lines.append(
        f"Most recent session in series — OHLC (close is last): "
        f"open={o}, high={h}, low={low}, close={c}"
    )
    t_list = candles.get("t") or []
    c_list = candles.get("c") or []
    if not t_list or not c_list or len(t_list) != len(c_list):
        lines.append("No usable time series in this response.")
        return "\n".join(lines)

    n = len(c_list)
    lines.append(f"Number of daily bars returned: {n}.")
    if n >= 2:
        c0, c1 = c_list[0], c_list[-1]
        try:
            pct = (float(c1) - float(c0)) / float(c0) * 100.0
            lines.append(
                f"Approx total return over this window: {pct:.2f}% (first close in window {float(c0):.4f} → last {float(c1):.4f})."
            )
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    tail = min(8, n)
    lines.append("Recent daily closes (oldest → newest in sample):")
    for i in range(n - tail, n):
        ts = int(t_list[i])
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        lines.append(f"  {dt}: close={float(c_list[i]):.4f}")

    return "\n".join(lines)


def format_news_context(
    symbol: str,
    source: str,
    articles: list[dict[str, Any]],
    warning: str | None,
    max_items: int = 40,
) -> str:
    lines = [
        f"Ticker: {symbol.upper().strip()}",
        f"Headlines source: {source}",
    ]
    if warning:
        lines.append(f"Feed note: {warning}")
    lines.append(f"Article count: {len(articles)}.")
    lines.append("Headlines:")
    for i, a in enumerate(articles[:max_items], start=1):
        hl = str(a.get("headline") or "").strip() or "Untitled"
        src = str(a.get("source") or "").strip()
        suf = f" ({src})" if src else ""
        lines.append(f"  {i}.{suf} {hl}")
    if len(articles) > max_items:
        lines.append(f"(…{len(articles) - max_items} more not shown)")
    return "\n".join(lines)


def answer_market_question(
    symbol: str,
    days: int,
    quote: dict[str, Any],
    candles: dict[str, Any],
    warning: str | None,
    question: str,
) -> str:
    q = question.strip()
    if not q:
        raise ValueError("question must be non-empty")
    ctx = format_market_context(symbol, days, quote, candles, warning)
    prompt = _market_prompt(ctx, q)
    try:
        return _invoke(prompt)
    except Exception as e:
        _log.warning("answer_market_question failed: %s", e)
        raise


def answer_news_question(
    symbol: str,
    source: str,
    articles: list[dict[str, Any]],
    warning: str | None,
    question: str,
) -> str:
    q = question.strip()
    if not q:
        raise ValueError("question must be non-empty")
    ctx = format_news_context(symbol, source, articles, warning)
    prompt = _news_prompt(ctx, q)
    try:
        return _invoke(prompt)
    except Exception as e:
        _log.warning("answer_news_question failed: %s", e)
        raise
