from pydantic import BaseModel
from datetime import datetime


class PriceWindow(BaseModel):
    start: datetime
    end: datetime
    predicted_avg_price: float
    savings_pct: float
    confidence: float


class CumulativeSavings(BaseModel):
    total_usd: float
    vs_naive_pct: float
    workloads_optimized: int


class SchedulerResponse(BaseModel):
    current_price: float
    windows: list[PriceWindow]
    recommendation: str
    cumulative_savings: CumulativeSavings
