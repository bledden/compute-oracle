from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator import OracleOrchestrator

router = APIRouter()
_orchestrator = OracleOrchestrator()


class CycleRunRequest(BaseModel):
    actual_price: float | None = None
    previous_prediction_id: str | None = None


@router.post("/run")
async def run_cycle(request: CycleRunRequest | None = None):
    """Run one complete prediction cycle.

    Optionally provide actual_price and previous_prediction_id
    to evaluate the previous prediction and learn from it.
    """
    req = request or CycleRunRequest()
    result = await _orchestrator.run_cycle(
        actual_price=req.actual_price,
        previous_prediction_id=req.previous_prediction_id,
    )
    return result
