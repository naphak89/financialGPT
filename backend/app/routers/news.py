from fastapi import APIRouter, Depends

from app.db.models import User
from app.deps import get_current_user
from app.schemas.api import NewsRequest, NewsResponse
from app.services.yahoo_rss_news import fetch_yahoo_rss_headlines
from app.services.yfinance_data import fetch_news as fetch_news_yfinance

router = APIRouter(prefix="/news", tags=["news"])


@router.post("/data", response_model=NewsResponse)
def news_data(body: NewsRequest, current: User = Depends(get_current_user)):
    sym = body.symbol.upper().strip()

    articles, yf_warning = fetch_news_yfinance(sym, limit=50)
    source = "yfinance"

    if not articles:
        rss_articles, rss_err = fetch_yahoo_rss_headlines(sym, limit=50)
        if rss_articles:
            articles = rss_articles
            source = "yahoo_rss"
            # RSS worked — do not surface yfinance JSON errors; optional RSS-only message
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
