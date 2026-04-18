"""
Summarize fetched headlines with DeepSeek (same env as education RAG).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent
load_dotenv(_BACKEND_ROOT / ".env")
load_dotenv(_REPO_ROOT / "langchain-rag-tutorial" / ".env")

_log = logging.getLogger(__name__)

MAX_HEADLINES = 45

SUMMARY_PROMPT = """You are a concise financial news assistant.

The user asked for recent headlines related to stock ticker {symbol}.

Below is a numbered list of news headlines (with source labels). Write ONE cohesive summary (3–6 short paragraphs, or clear bullet themes) that:
- Captures the main themes and what investors might care about
- Notes when several headlines repeat the same story
- Does not invent facts not implied by the headlines
- Mentions the ticker {symbol} where relevant

Headlines:
{headlines}

Summary:"""


def summarize_news_headlines(symbol: str, articles: list[dict[str, Any]]) -> str:
    sym = symbol.upper().strip()
    lines: list[str] = []
    for i, a in enumerate(articles[:MAX_HEADLINES], start=1):
        hl = str(a.get("headline") or "").strip() or "Untitled"
        src = str(a.get("source") or "").strip()
        suffix = f" [{src}]" if src else ""
        lines.append(f"{i}.{suffix} {hl}")
    headlines = "\n".join(lines)
    prompt = SUMMARY_PROMPT.format(symbol=sym, headlines=headlines)
    model = ChatDeepSeek(model="deepseek-chat")
    out = model.invoke(prompt)
    text = (out.content or "").strip()
    if not text:
        raise RuntimeError("Empty summary from model")
    return text
