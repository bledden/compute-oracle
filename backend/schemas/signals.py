from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class SignalSource(str, Enum):
    AWS_SPOT = "aws_spot"
    EIA_ELECTRICITY = "eia_electricity"
    WEATHER = "weather"
    GPU_PRICING = "gpu_pricing"
    NEWS = "news"


class Signal(BaseModel):
    source: SignalSource
    name: str
    value: float
    unit: str
    timestamp: datetime
    change_pct: Optional[float] = None


class SignalsLatestResponse(BaseModel):
    timestamp: datetime
    signals: list[Signal]


class DataPoint(BaseModel):
    timestamp: datetime
    value: float


class SignalHistoryResponse(BaseModel):
    source: SignalSource
    name: str
    data_points: list[DataPoint]


class SourceStatus(BaseModel):
    id: str
    name: str
    status: str  # "active" | "inactive" | "error"
    last_update: Optional[datetime] = None


class SourcesResponse(BaseModel):
    sources: list[SourceStatus]
