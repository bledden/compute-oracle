from fastapi import APIRouter
from datetime import datetime, timezone
from schemas.predictions import (
    PredictionResponse,
    HorizonPrediction,
    ContributingFactor,
    PredictionHistoryResponse,
    PredictionHistoryItem,
)
from core.redis_client import get_json, get_redis

router = APIRouter()


@router.get("/latest", response_model=PredictionResponse)
async def get_latest_prediction():
    r = await get_redis()
    latest = await r.zrevrange("predictions:index", 0, 0)

    if latest:
        pred_id = latest[0]
        pred = await get_json(f"prediction:{pred_id}")
        if pred:
            return PredictionResponse(
                prediction_id=pred["prediction_id"],
                cycle=pred.get("cycle", 0),
                timestamp=pred["timestamp"],
                target=pred.get("target", "p3.2xlarge us-east-1a"),
                current_price=pred["current_price"],
                predictions=[
                    HorizonPrediction(**p) for p in pred.get("predictions", [])
                ],
                causal_explanation=pred.get("causal_explanation", ""),
                contributing_factors=[
                    ContributingFactor(**f) for f in pred.get("contributing_factors", [])
                ],
            )

    # Fallback stub
    now = datetime.now(timezone.utc)
    return PredictionResponse(
        prediction_id="awaiting_first_cycle",
        cycle=0,
        timestamp=now,
        target="p3.2xlarge us-east-1a",
        current_price=1.07,
        predictions=[
            HorizonPrediction(horizon="1h", predicted_price=1.07, direction="flat", confidence=0.0),
        ],
        causal_explanation="Awaiting first prediction cycle. Trigger via POST /cycle/run.",
        contributing_factors=[],
    )


@router.get("/history", response_model=PredictionHistoryResponse)
async def get_prediction_history(limit: int = 50):
    r = await get_redis()
    pred_ids = await r.zrevrange("predictions:index", 0, limit - 1)

    items = []
    for pred_id in pred_ids:
        pred = await get_json(f"prediction:{pred_id}")
        ev = await get_json(f"eval:{pred_id}")

        if pred:
            pred_1h = pred["predictions"][0] if pred.get("predictions") else {}
            items.append(PredictionHistoryItem(
                prediction_id=pred["prediction_id"],
                cycle=pred.get("cycle", 0),
                timestamp=pred["timestamp"],
                predicted_price_1h=pred_1h.get("predicted_price", 0.0),
                actual_price_1h=ev.get("actual_price") if ev else None,
                error_1h=ev.get("absolute_error") if ev else None,
                direction_correct=ev.get("direction_correct") if ev else None,
            ))

    return PredictionHistoryResponse(predictions=items)
