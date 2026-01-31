from fastapi import APIRouter
from schemas.scheduler import (
    SchedulerResponse,
    PriceWindow,
    CumulativeSavings,
)
from scheduler.optimizer import SchedulerOptimizer

router = APIRouter()
_optimizer = SchedulerOptimizer()


@router.get("/windows", response_model=SchedulerResponse)
async def get_scheduler_windows(hours: int = 48):
    result = await _optimizer.get_optimal_windows(hours_ahead=hours)

    return SchedulerResponse(
        current_price=result["current_price"],
        windows=[PriceWindow(**w) for w in result["windows"]],
        recommendation=result["recommendation"],
        cumulative_savings=CumulativeSavings(**result["cumulative_savings"]),
    )
