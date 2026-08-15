"""Sentiment analysis skill — FinBERT stub."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SentimentRequest(BaseModel):
    text: str
    ticker: str | None = None


class SentimentResponse(BaseModel):
    status: str = "stub"
    label: str = "neutral"
    score: float = 0.0
    model: str = "finbert"


@router.post("/analyze", response_model=SentimentResponse)
async def analyze(req: SentimentRequest) -> SentimentResponse:
    """Analyze financial text sentiment. Returns stub until FinBERT is loaded."""
    # TODO: load ProsusAI/finbert, run inference
    return SentimentResponse(
        status="stub",
        label="neutral",
        score=0.0,
        model="finbert",
    )
