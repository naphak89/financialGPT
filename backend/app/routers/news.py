import logging
import os

from fastapi import APIRouter, Depends

from app.db.models import User
from app.deps import get_current_user
from app.schemas.api import NewsRequest, NewsResponse
from app.services.yahoo_rss_news import fetch_yahoo_rss_headlines
from app.services.yfinance_data import fetch_news as fetch_news_yfinance

router = APIRouter(prefix="/news", tags=["news"])
_log = logging.getLogger(__name__)


@router.post("/data", response_model=NewsResponse)
def news_data(body: NewsRequest, current: User = Depends(get_current_user)):
    sym = body.symbol.upper().strip()

    try:
        # yfinance often breaks on serverless (blocked IP, JSON errors); RSS is reliable there.
        if os.environ.get("VERCEL"):
            rss_articles, rss_err = fetch_yahoo_rss_headlines(sym, limit=50)
            if rss_articles:
                return NewsResponse(
                    symbol=sym,
                    articles=rss_articles,
                    warning=rss_err,
                    source="yahoo_rss",
                )
            articles, yf_warning = fetch_news_yfinance(sym, limit=50)
            source = "yfinance"
            if not articles:
                parts = [p for p in (yf_warning, rss_err) if p]
                warning = " ".join(parts) if parts else "No headlines found."
                return NewsResponse(
                    symbol=sym,
                    articles=[],
                    warning=warning,
                    source="yahoo_rss",
                )
            return NewsResponse(
                symbol=sym,
                articles=articles,
                warning=yf_warning,
                source=source,
            )

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

        return NewsResponse(
            symbol=sym,
            articles=articles,
            warning=warning,
            source=source,
        )
    except Exception as e:
        _log.exception("news_data failed for %s", sym)
        return NewsResponse(
            symbol=sym,
            articles=[],
            warning=f"News temporarily unavailable: {e}",
            source="yahoo_rss",
        )
