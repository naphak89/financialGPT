import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.db.models import User
from app.deps import get_current_user
from app.schemas.api import MarketRequest, MarketResponse
from app.services.alpha_vantage_market import fetch_daily_ohlcv
from app.services.chat_on_data import answer_market_question

router = APIRouter(prefix="/market", tags=["market"])
_log = logging.getLogger(__name__)

ALLOWED_RESOLUTIONS = {"1", "5", "15", "30", "60", "D", "W", "M"}


@router.post("/data", response_model=MarketResponse)
def market_data(body: MarketRequest, current: User = Depends(get_current_user)):
    if body.resolution not in ALLOWED_RESOLUTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"resolution must be one of {sorted(ALLOWED_RESOLUTIONS)}",
        )
    sym = body.symbol.upper().strip()
    to_ts = int(time.time())
    from_ts = to_ts - body.days * 86400

    key = get_settings().alpha_vantage_api_key.strip()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Market prices require ALPHA_VANTAGE_API_KEY in backend/.env (free at alphavantage.co).",
        )

    quote, candles, warning = fetch_daily_ohlcv(sym, key, body.days)

    answer = None
    q = body.question.strip()
    if q:
        try:
            answer = answer_market_question(
                sym, body.days, quote, candles, warning, body.question
            )
        except Exception as e:
            _log.warning("market answer LLM failed for %s: %s", sym, e)
            extra = f"AI answer unavailable: {e}"
            warning = f"{warning} {extra}" if warning else extra

    return MarketResponse(
        symbol=sym,
        quote=quote,
        candles=candles,
        resolution=body.resolution,
        days=body.days,
        from_ts=from_ts,
        to_ts=to_ts,
        warning=warning,
        data_source="alpha_vantage",
        answer=answer,
    )
