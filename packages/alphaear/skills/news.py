"""News aggregation skill — multi-source financial news scanner."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class NewsRequest(BaseModel):
    query: str
    sources: list[str] | None = None
    max_results: int = 10


class NewsItem(BaseModel):
    title: str
    source: str
    url: str
    published: str
    relevance: float


class NewsResponse(BaseModel):
    status: str = "stub"
    query: str
    items: list[NewsItem] = []


@router.post("/scan", response_model=NewsResponse)
async def scan(req: NewsRequest) -> NewsResponse:
    """Scan financial news sources. Returns stub until APIs are wired."""
    # TODO: wire to NewsAPI, Polygon.io, RSS feeds
    return NewsResponse(
        status="stub",
        query=req.query,
        items=[],
    )
