from fastapi import APIRouter
from api import signals, predictions, causal, learning, scheduler, replay, cycle

router = APIRouter()

router.include_router(signals.router, prefix="/signals", tags=["signals"])
router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
router.include_router(causal.router, prefix="/causal", tags=["causal"])
router.include_router(learning.router, prefix="/learning", tags=["learning"])
router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
router.include_router(replay.router, prefix="/replay", tags=["replay"])
router.include_router(cycle.router, prefix="/cycle", tags=["cycle"])
