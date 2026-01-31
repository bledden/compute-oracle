from pydantic import BaseModel, Field
from datetime import datetime


class CausalNode(BaseModel):
    id: str
    label: str
    type: str  # "signal" | "target" | "derived"
    source: str


class CausalEdge(BaseModel):
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    weight: float  # 0.0 to 1.0
    confidence: float
    direction: str  # "positive" | "negative"
    last_updated: datetime

    model_config = {"populate_by_name": True}


class GraphMetadata(BaseModel):
    total_nodes: int
    total_edges: int
    last_updated: datetime
    version: int


class CausalGraphResponse(BaseModel):
    nodes: list[CausalNode]
    edges: list[CausalEdge]
    metadata: GraphMetadata


class FactorDetail(BaseModel):
    id: str
    current_weight: float
    weight_history: list[float]
    contribution_rank: int
    direction: str


class FactorsResponse(BaseModel):
    factors: list[FactorDetail]
