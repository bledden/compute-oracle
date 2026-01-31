from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LastImprovement(BaseModel):
    cycle: int
    change: str
    mae_delta: float


class LearningMetricsResponse(BaseModel):
    total_cycles: int
    overall_mae: float
    directional_accuracy: float
    mae_history: list[float]
    directional_accuracy_history: list[float]
    graph_versions: int
    last_improvement: Optional[LastImprovement] = None


class LearningEvent(BaseModel):
    cycle: int
    timestamp: datetime
    type: str  # "edge_weight_update" | "edge_pruned" | "edge_added" | "prediction_evaluated"
    description: str
    mae_before: Optional[float] = None
    mae_after: Optional[float] = None


class LearningLogResponse(BaseModel):
    events: list[LearningEvent]
