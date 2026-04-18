import logging
import os

from fastapi import APIRouter, Depends

from app.db.models import User
from app.deps import get_current_user
from app.schemas.api import NewsRequest, NewsResponse
from app.services.chat_on_data import answer_news_question
from app.services.yahoo_rss_news import fetch_yahoo_rss_headlines
from app.services.yfinance_data import fetch_news as fetch_news_yfinance
from app.services.news_summary import summarize_news_headlines

router = APIRouter(prefix="/news", tags=["news"])
_log = logging.getLogger(__name__)


def _build_response(
    sym: str,
    articles: list,
    warning: str | None,
    source: str,
    question: str = "",
) -> NewsResponse:
    summary: str | None = None
    answer: str | None = None
    q = question.strip()
    if articles:
        if q:
            try:
                answer = answer_news_question(sym, source, articles, warning, question)
            except Exception as e:
                _log.warning("news Q&A LLM failed for %s: %s", sym, e)
                extra = f"AI answer unavailable: {e}"
                warning = f"{warning} {extra}" if warning else extra
        else:
            try:
                summary = summarize_news_headlines(sym, articles)
            except Exception as e:
                _log.warning("news summary failed for %s: %s", sym, e)
                extra = f"AI summary unavailable: {e}"
                warning = f"{warning} {extra}" if warning else extra
    return NewsResponse(
        symbol=sym,
        articles=articles,
        warning=warning,
        source=source,
        summary=summary,
        answer=answer,
    )


@router.post("/data", response_model=NewsResponse)
def news_data(body: NewsRequest, current: User = Depends(get_current_user)):
    sym = body.symbol.upper().strip()
    q = body.question

    try:
        # yfinance often breaks on serverless (blocked IP, JSON errors); RSS is reliable there.
        if os.environ.get("VERCEL"):
            rss_articles, rss_err = fetch_yahoo_rss_headlines(sym, limit=50)
            if rss_articles:
                return _build_response(sym, rss_articles, rss_err, "yahoo_rss", q)
            articles, yf_warning = fetch_news_yfinance(sym, limit=50)
            source = "yfinance"
            if not articles:
                parts = [p for p in (yf_warning, rss_err) if p]
                warning = " ".join(parts) if parts else "No headlines found."
                return _build_response(sym, [], warning, "yahoo_rss", q)
            return _build_response(sym, articles, yf_warning, source, q)

        articles, yf_warning = fetch_news_yfinance(sym, limit=50)
        source = "yfinance"

        if not articles:
            rss_articles, rss_err = fetch_yahoo_rss_headlines(sym, limit=50)
            if rss_articles:
                articles = rss_articles
                source = "yahoo_rss"
                warning = rss_err
            else:
                parts = [p for p in (yf_warning, rss_err) if p]
                warning = " ".join(parts) if parts else "No headlines found."
        else:
            warning = yf_warning if yf_warning else None

        return _build_response(sym, articles, warning, source, q)
    except Exception as e:
        _log.exception("news_data failed for %s", sym)
        return _build_response(
            sym,
            [],
            f"News temporarily unavailable: {e}",
            "yahoo_rss",
            q,
        )
