"""
AlphaEar — FastAPI sidecar for financial ML skills.
Port 8100. Provides sentiment, time-series, and news aggregation endpoints.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from skills.sentiment import router as sentiment_router
from skills.timeseries import router as timeseries_router
from skills.news import router as news_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks for model loading."""
    # TODO: load FinBERT, Kronos weights here
    yield
    # TODO: cleanup


app = FastAPI(
    title="AlphaEar",
    description="Financial ML skill sidecar for Mekong CLI",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(sentiment_router, prefix="/skills/sentiment", tags=["sentiment"])
app.include_router(timeseries_router, prefix="/skills/timeseries", tags=["timeseries"])
app.include_router(news_router, prefix="/skills/news", tags=["news"])


@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "service": "alphaear",
        "version": "0.1.0",
        "skills": ["sentiment", "timeseries", "news"],
    }


@app.get("/skills")
async def list_skills() -> dict:
    return {
        "skills": [
            {
                "name": "sentiment",
                "model": "FinBERT",
                "status": "stub",
                "endpoint": "/skills/sentiment/analyze",
            },
            {
                "name": "timeseries",
                "model": "Kronos",
                "status": "stub",
                "endpoint": "/skills/timeseries/forecast",
            },
            {
                "name": "news",
                "model": "aggregator",
                "status": "stub",
                "endpoint": "/skills/news/scan",
            },
        ]
    }
