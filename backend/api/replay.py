import asyncio
import uuid
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from ingestion.replay import ReplayEngine
from core.redis_client import get_json

router = APIRouter()
_engine = ReplayEngine()


class ReplayStartRequest(BaseModel):
    start_date: str = "2025-11-01T00:00:00"
    end_date: str = "2025-11-04T00:00:00"


class ReplayStartResponse(BaseModel):
    replay_id: str
    status: str
    estimated_cycles: int


class ReplayStatusResponse(BaseModel):
    replay_id: str
    status: str
    progress_pct: float
    current_date: str | None = None
    cycles_completed: int
    current_mae: float
    current_directional_accuracy: float


async def _run_replay_task(replay_id: str, start_date: str, end_date: str):
    """Background task to run replay."""
    try:
        await _engine.run_replay(
            start_date=start_date,
            end_date=end_date,
            replay_id=replay_id,
        )
    except Exception as e:
        from core.redis_client import store_json
        await store_json(f"replay:{replay_id}", {
            "replay_id": replay_id,
            "status": f"error: {str(e)}",
            "progress_pct": 0.0,
            "cycles_completed": 0,
            "current_mae": 0.0,
            "current_directional_accuracy": 0.0,
        })


@router.post("/start", response_model=ReplayStartResponse)
async def start_replay(request: ReplayStartRequest, background_tasks: BackgroundTasks):
    replay_id = f"replay_{uuid.uuid4().hex[:8]}"

    # Estimate cycles (1 per hour between start and end)
    from datetime import datetime, timezone
    start = datetime.fromisoformat(request.start_date).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(request.end_date).replace(tzinfo=timezone.utc)
    estimated_cycles = int((end - start).total_seconds() / 3600)

    # Launch in background
    background_tasks.add_task(_run_replay_task, replay_id, request.start_date, request.end_date)

    return ReplayStartResponse(
        replay_id=replay_id,
        status="started",
        estimated_cycles=estimated_cycles,
    )


@router.get("/status/{replay_id}", response_model=ReplayStatusResponse)
async def get_replay_status(replay_id: str):
    status = await get_json(f"replay:{replay_id}")
    if status is None:
        return ReplayStatusResponse(
            replay_id=replay_id,
            status="not_found",
            progress_pct=0.0,
            current_date=None,
            cycles_completed=0,
            current_mae=0.0,
            current_directional_accuracy=0.0,
        )

    return ReplayStatusResponse(
        replay_id=status["replay_id"],
        status=status["status"],
        progress_pct=status["progress_pct"],
        current_date=status.get("current_date"),
        cycles_completed=status["cycles_completed"],
        current_mae=status["current_mae"],
        current_directional_accuracy=status["current_directional_accuracy"],
    )
