from typing import Any, Literal

from pydantic import BaseModel, Field


class MarketRequest(BaseModel):
    symbol: str = Field(..., min_length=1, description="Ticker, e.g. AAPL")
    resolution: str = Field("D", description="1,5,15,30,60,D,W,M")
    days: int = Field(30, ge=1, le=365)
    question: str = Field(
        "",
        max_length=4000,
        description="Optional user message; if set, the API returns an AI answer grounded in the fetched data.",
    )


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
    answer: str | None = None


class NewsRequest(BaseModel):
    symbol: str = Field(..., min_length=1)
    days: int = Field(7, ge=1, le=90)
    question: str = Field(
        "",
        max_length=4000,
        description="Optional user message; if set, the API returns an AI answer grounded in the fetched headlines.",
    )


class NewsResponse(BaseModel):
    symbol: str
    articles: list[dict[str, Any]]
    warning: str | None = None
    source: str = "yfinance"
    summary: str | None = None
    answer: str | None = None


class EducationRequest(BaseModel):
    question: str = Field(..., min_length=1)


class SourceChunk(BaseModel):
    content_preview: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    file_name: str = Field("", description="PDF basename under /textbooks/")
    page: int = Field(1, ge=1, description="1-based page number in the PDF")
    highlight: str = Field(
        "",
        description="Short anchor string for find-in-document in the PDF reader",
    )


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
