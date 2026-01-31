from fastapi import APIRouter
from datetime import datetime, timezone
from schemas.causal import (
    CausalGraphResponse,
    CausalNode,
    CausalEdge,
    GraphMetadata,
    FactorsResponse,
    FactorDetail,
)
from causal.graph import CausalGraph

router = APIRouter()
_graph = CausalGraph()


@router.get("/graph", response_model=CausalGraphResponse)
async def get_causal_graph():
    graph_data = await _graph.get_graph()

    nodes = [
        CausalNode(id=n["id"], label=n["label"], type=n["type"], source=n["source"])
        for n in graph_data.get("nodes", [])
    ]

    edges = [
        CausalEdge(**{
            "from": e["from"],
            "to": e["to"],
            "weight": e["weight"],
            "confidence": e["confidence"],
            "direction": e["direction"],
            "last_updated": e["last_updated"],
        })
        for e in graph_data.get("edges", {}).values()
    ]

    now = graph_data.get("last_updated", datetime.now(timezone.utc).isoformat())
    return CausalGraphResponse(
        nodes=nodes,
        edges=edges,
        metadata=GraphMetadata(
            total_nodes=len(nodes),
            total_edges=len(edges),
            last_updated=now,
            version=graph_data.get("version", 0),
        ),
    )


@router.get("/factors", response_model=FactorsResponse)
async def get_factors():
    graph_data = await _graph.get_graph()
    edges = graph_data.get("edges", {})

    # Group edges by target, sort by weight
    factor_weights: dict[str, list[float]] = {}
    factor_directions: dict[str, str] = {}

    for edge in edges.values():
        fid = edge["from"]
        if fid not in factor_weights:
            factor_weights[fid] = []
            factor_directions[fid] = edge["direction"]
        factor_weights[fid].append(edge["weight"])

    # Rank by average weight
    factors = []
    ranked = sorted(
        factor_weights.items(),
        key=lambda x: sum(x[1]) / len(x[1]),
        reverse=True,
    )
    for rank, (fid, weights) in enumerate(ranked, 1):
        avg_weight = sum(weights) / len(weights)
        factors.append(FactorDetail(
            id=fid,
            current_weight=round(avg_weight, 4),
            weight_history=[round(avg_weight, 4)],  # Will grow with learning
            contribution_rank=rank,
            direction=factor_directions.get(fid, "positive"),
        ))

    return FactorsResponse(factors=factors)
