"""Time-series forecasting skill — Kronos stub."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class TimeseriesRequest(BaseModel):
    ticker: str
    horizon_days: int = 7
    history: list[float] | None = None


class TimeseriesResponse(BaseModel):
    status: str = "stub"
    ticker: str
    forecast: list[float] = []
    model: str = "kronos"


@router.post("/forecast", response_model=TimeseriesResponse)
async def forecast(req: TimeseriesRequest) -> TimeseriesResponse:
    """Forecast price series. Returns stub until Kronos is loaded."""
    # TODO: load amazon-science/chronos-forecasting, run inference
    return TimeseriesResponse(
        status="stub",
        ticker=req.ticker,
        forecast=[],
        model="kronos",
    )
