"""Scheduler optimizer — finds optimal compute windows based on predictions.

Analyzes prediction history to identify price dip windows and
calculates savings vs naive (always-on) scheduling.
"""

from datetime import datetime, timezone
from typing import Any
import weave

from core.redis_client import get_json, get_redis, store_json


class SchedulerOptimizer:
    """Finds optimal compute windows from prediction data."""

    @weave.op()
    async def get_optimal_windows(
        self, hours_ahead: int = 48
    ) -> dict[str, Any]:
        """Analyze predictions to find the best times to run compute workloads."""
        r = await get_redis()

        # Get recent predictions
        pred_ids = await r.zrevrange("predictions:index", 0, 50)
        predictions = []
        for pid in pred_ids:
            pred = await get_json(f"prediction:{pid}")
            if pred:
                predictions.append(pred)

        if not predictions:
            return {
                "current_price": 1.07,
                "windows": [],
                "recommendation": "No predictions available yet. Run prediction cycles first.",
                "cumulative_savings": {
                    "total_usd": 0.0,
                    "vs_naive_pct": 0.0,
                    "workloads_optimized": 0,
                },
            }

        predictions.sort(key=lambda p: p.get("timestamp", ""))

        # Current price from latest prediction
        latest = predictions[-1]
        current_price = latest.get("current_price", 1.07)

        # Analyze predictions for windows
        windows = []
        for pred in predictions[-10:]:  # Last 10 predictions
            for horizon_pred in pred.get("predictions", []):
                if horizon_pred["direction"] == "down" and horizon_pred["confidence"] > 0.5:
                    price = horizon_pred["predicted_price"]
                    savings_pct = round((current_price - price) / current_price * 100, 1)
                    if savings_pct > 0:
                        windows.append({
                            "start": pred["timestamp"],
                            "end": pred["timestamp"],  # simplified
                            "predicted_avg_price": price,
                            "savings_pct": savings_pct,
                            "confidence": horizon_pred["confidence"],
                        })

        # Sort by savings
        windows.sort(key=lambda w: w["savings_pct"], reverse=True)
        windows = windows[:5]  # Top 5

        # Calculate cumulative savings from evaluated predictions
        eval_ids = await r.zrevrange("evaluations:index", 0, 100)
        total_savings = 0.0
        workloads = 0
        naive_total = 0.0

        for eid in eval_ids:
            ev = await get_json(f"eval:{eid}")
            if ev and ev.get("direction_correct"):
                predicted = ev.get("predicted_price", 0)
                actual = ev.get("actual_price", 0)
                base = ev.get("current_price", actual)
                if predicted < base:
                    savings = base - actual
                    total_savings += abs(savings)
                    workloads += 1
                naive_total += base

        vs_naive_pct = round(total_savings / naive_total * 100, 1) if naive_total > 0 else 0.0

        # Store savings for frontend
        savings_data = {
            "total_usd": round(total_savings, 2),
            "vs_naive_pct": vs_naive_pct,
            "workloads_optimized": workloads,
        }
        await store_json("scheduler:savings", savings_data)

        recommendation = "Run workloads during predicted price dips for optimal savings."
        if windows:
            best = windows[0]
            recommendation = (
                f"Best window: ${best['predicted_avg_price']:.3f}/hr "
                f"({best['savings_pct']}% savings, "
                f"{best['confidence']:.0%} confidence)"
            )

        return {
            "current_price": current_price,
            "windows": windows,
            "recommendation": recommendation,
            "cumulative_savings": savings_data,
        }
