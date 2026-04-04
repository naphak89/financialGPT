from typing import Any, Literal

from pydantic import BaseModel, Field


class MarketRequest(BaseModel):
    symbol: str = Field(..., min_length=1, description="Ticker, e.g. AAPL")
    resolution: str = Field("D", description="1,5,15,30,60,D,W,M")
    days: int = Field(30, ge=1, le=365)


class MarketResponse(BaseModel):
    symbol: str
    quote: dict[str, Any]
    candles: dict[str, Any]
    resolution: str
    days: int = Field(..., description="Requested chart span (trading days target)")
    from_ts: int
    to_ts: int
    warning: str | None = None
    data_source: Literal["alpha_vantage"] = "alpha_vantage"


class NewsRequest(BaseModel):
    symbol: str = Field(..., min_length=1)
    days: int = Field(7, ge=1, le=90)


class NewsResponse(BaseModel):
    symbol: str
    articles: list[dict[str, Any]]
    warning: str | None = None
    source: str = "yfinance"


class EducationRequest(BaseModel):
    question: str = Field(..., min_length=1)


class SourceChunk(BaseModel):
    content_preview: str
    score: float
    metadata: dict[str, Any]


class EducationResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    low_confidence: bool


class FeedbackCreate(BaseModel):
    message_id: str = Field(..., min_length=1)
    rating: Literal[1, -1]
    comment: str | None = None


class FeedbackResponse(BaseModel):
    id: int
    ok: bool = True
