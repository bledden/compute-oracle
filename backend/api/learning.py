from fastapi import APIRouter
from schemas.learning import (
    LearningMetricsResponse,
    LearningLogResponse,
    LearningEvent,
    LastImprovement,
)
from evaluation.evaluator import PredictionEvaluator
from core.redis_client import get_list

router = APIRouter()
_evaluator = PredictionEvaluator()


@router.get("/metrics", response_model=LearningMetricsResponse)
async def get_learning_metrics():
    metrics = await _evaluator.compute_metrics()

    # Find last improvement from log
    events = await get_list("learning:log", limit=5)
    last_improvement = None
    for ev in events:
        if ev.get("type") == "edge_weight_update":
            last_improvement = LastImprovement(
                cycle=ev.get("cycle", 0),
                change=ev.get("description", ""),
                mae_delta=round(
                    (ev.get("mae_after", 0) - ev.get("mae_before", 0)),
                    6,
                ),
            )
            break

    # Count graph versions
    all_events = await get_list("learning:log", limit=1000)
    seen_cycles = set()
    for ev in all_events:
        seen_cycles.add(ev.get("cycle", 0))
    graph_versions = len(seen_cycles)

    return LearningMetricsResponse(
        total_cycles=metrics["total_cycles"],
        overall_mae=metrics["overall_mae"],
        directional_accuracy=metrics["directional_accuracy"],
        mae_history=metrics["mae_history"],
        directional_accuracy_history=metrics["directional_accuracy_history"],
        graph_versions=graph_versions,
        last_improvement=last_improvement,
    )


@router.get("/log", response_model=LearningLogResponse)
async def get_learning_log(limit: int = 20):
    raw_events = await get_list("learning:log", limit=limit)

    events = [
        LearningEvent(
            cycle=ev.get("cycle", 0),
            timestamp=ev.get("timestamp", ""),
            type=ev.get("type", "unknown"),
            description=ev.get("description", ""),
            mae_before=ev.get("mae_before"),
            mae_after=ev.get("mae_after"),
        )
        for ev in raw_events
    ]

    return LearningLogResponse(events=events)
