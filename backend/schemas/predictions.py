from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HorizonPrediction(BaseModel):
    horizon: str  # "1h", "4h", "24h"
    predicted_price: float
    direction: str  # "up" | "down" | "flat"
    confidence: float  # 0.0 to 1.0


class ContributingFactor(BaseModel):
    factor: str
    contribution: float  # 0.0 to 1.0
    direction: str  # "bullish" | "bearish" | "neutral"


class PredictionResponse(BaseModel):
    prediction_id: str
    cycle: int
    timestamp: datetime
    target: str
    current_price: float
    predictions: list[HorizonPrediction]
    causal_explanation: str
    contributing_factors: list[ContributingFactor]


class PredictionHistoryItem(BaseModel):
    prediction_id: str
    cycle: int
    timestamp: datetime
    predicted_price_1h: float
    actual_price_1h: Optional[float] = None
    error_1h: Optional[float] = None
    direction_correct: Optional[bool] = None


class PredictionHistoryResponse(BaseModel):
    predictions: list[PredictionHistoryItem]
