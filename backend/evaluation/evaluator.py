from datetime import datetime, timezone
from typing import Any
import weave

from core.redis_client import get_json, store_json, get_redis


class PredictionEvaluator:
    """Evaluates predictions against ground truth."""

    @weave.op()
    async def evaluate(
        self,
        prediction_id: str,
        actual_price: float,
    ) -> dict[str, Any]:
        """Compare a prediction against the actual price."""
        prediction = await get_json(f"prediction:{prediction_id}")
        if prediction is None:
            return {"error": f"Prediction {prediction_id} not found"}

        # Find the 1h prediction (primary evaluation target)
        pred_1h = None
        for p in prediction.get("predictions", []):
            if p["horizon"] == "1h":
                pred_1h = p
                break

        if pred_1h is None:
            return {"error": "No 1h prediction found"}

        predicted_price = pred_1h["predicted_price"]
        predicted_direction = pred_1h["direction"]

        # Calculate metrics
        absolute_error = abs(predicted_price - actual_price)
        pct_error = absolute_error / actual_price if actual_price > 0 else 0

        # Direction accuracy
        actual_direction = "up" if actual_price > prediction["current_price"] else (
            "down" if actual_price < prediction["current_price"] else "flat"
        )
        direction_correct = predicted_direction == actual_direction

        evaluation = {
            "prediction_id": prediction_id,
            "cycle": prediction.get("cycle", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": prediction.get("target", ""),
            "predicted_price": predicted_price,
            "actual_price": actual_price,
            "current_price": prediction["current_price"],
            "absolute_error": round(absolute_error, 6),
            "pct_error": round(pct_error, 6),
            "predicted_direction": predicted_direction,
            "actual_direction": actual_direction,
            "direction_correct": direction_correct,
            "contributing_factors": prediction.get("contributing_factors", []),
        }

        # Store evaluation
        await store_json(f"eval:{prediction_id}", evaluation)

        # Update prediction history
        r = await get_redis()
        await r.zadd("evaluations:index", {prediction_id: evaluation["cycle"]})

        return evaluation

    async def get_all_evaluations(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get all evaluations ordered by cycle."""
        r = await get_redis()
        pred_ids = await r.zrevrange("evaluations:index", 0, limit - 1)

        evals = []
        for pid in pred_ids:
            ev = await get_json(f"eval:{pid}")
            if ev:
                evals.append(ev)

        return evals

    async def compute_metrics(self, window: int | None = None) -> dict[str, Any]:
        """Compute aggregate metrics over all (or recent N) evaluations."""
        all_evals = await self.get_all_evaluations()

        if window:
            all_evals = all_evals[:window]

        if not all_evals:
            return {
                "total_cycles": 0,
                "overall_mae": 0.0,
                "directional_accuracy": 0.0,
                "mae_history": [],
                "directional_accuracy_history": [],
            }

        # Sort by cycle
        all_evals.sort(key=lambda e: e.get("cycle", 0))

        mae_history = []
        da_history = []
        running_errors = []
        running_correct = []

        for ev in all_evals:
            running_errors.append(ev["absolute_error"])
            running_correct.append(1 if ev["direction_correct"] else 0)
            mae_history.append(round(sum(running_errors) / len(running_errors), 6))
            da_history.append(round(sum(running_correct) / len(running_correct), 4))

        return {
            "total_cycles": len(all_evals),
            "overall_mae": mae_history[-1] if mae_history else 0.0,
            "directional_accuracy": da_history[-1] if da_history else 0.0,
            "mae_history": mae_history,
            "directional_accuracy_history": da_history,
        }
