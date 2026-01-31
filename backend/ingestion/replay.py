"""Historical replay engine — bulk backtesting over synthetic data.

Iterates through time in 1h steps, running the full prediction cycle at each step.
Uses synthetic but realistic pricing data from aws_spot.fetch_history().
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any
import weave

from core.redis_client import store_json, get_json, get_redis
from ingestion.aws_spot import AWSSpotSource
from prediction.predictor import PricePredictor
from evaluation.evaluator import PredictionEvaluator
from learning.learner import CausalLearner


class ReplayEngine:
    """Runs the prediction loop over historical data to demonstrate learning."""

    def __init__(self):
        self.aws_source = AWSSpotSource()
        self.predictor = PricePredictor()
        self.evaluator = PredictionEvaluator()
        self.learner = CausalLearner()

    @weave.op()
    async def run_replay(
        self,
        start_date: str,
        end_date: str,
        replay_id: str | None = None,
    ) -> dict[str, Any]:
        """Run a full historical replay."""
        if replay_id is None:
            replay_id = f"replay_{uuid.uuid4().hex[:8]}"

        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

        # Generate all historical data upfront
        historical_data = await self.aws_source.fetch_history(start, end)

        # Group by timestamp hour
        time_buckets: dict[str, list[dict[str, Any]]] = {}
        for item in historical_data:
            ts = datetime.fromisoformat(item["timestamp"])
            bucket_key = ts.strftime("%Y-%m-%dT%H:00:00")
            if bucket_key not in time_buckets:
                time_buckets[bucket_key] = []
            time_buckets[bucket_key].append(item)

        sorted_times = sorted(time_buckets.keys())
        total_steps = len(sorted_times)

        # Store initial replay status
        status = {
            "replay_id": replay_id,
            "status": "running",
            "progress_pct": 0.0,
            "current_date": None,
            "cycles_completed": 0,
            "total_steps": total_steps,
            "current_mae": 0.0,
            "current_directional_accuracy": 0.0,
        }
        await store_json(f"replay:{replay_id}", status)

        previous_prediction_id = None
        previous_signals = None

        r = await get_redis()
        base_cycle = int(await r.get("oracle:cycle_count") or 0)

        for step_idx, time_key in enumerate(sorted_times):
            signals = time_buckets[time_key]
            cycle = base_cycle + step_idx + 1
            await r.set("oracle:cycle_count", cycle)

            # Get the p3.2xlarge us-east-1a price as ground truth
            actual_price = None
            for s in signals:
                if s.get("instance_type") == "p3.2xlarge" and s.get("az") == "us-east-1a":
                    actual_price = s["value"]
                    break

            # Make prediction
            prediction = await self.predictor.predict(
                signals=signals,
                target_instance="p3.2xlarge",
                target_az="us-east-1a",
                cycle=cycle,
            )

            # Evaluate previous prediction if we have ground truth
            if previous_prediction_id and actual_price is not None:
                evaluation = await self.evaluator.evaluate(
                    prediction_id=previous_prediction_id,
                    actual_price=actual_price,
                )

                # Learn from evaluation
                if "error" not in evaluation:
                    await self.learner.learn(
                        evaluation=evaluation,
                        cycle=cycle,
                    )

            previous_prediction_id = prediction["prediction_id"]
            previous_signals = signals

            # Update replay status every 5 steps
            if step_idx % 5 == 0 or step_idx == total_steps - 1:
                metrics = await self.evaluator.compute_metrics()
                status.update({
                    "progress_pct": round((step_idx + 1) / total_steps * 100, 1),
                    "current_date": time_key,
                    "cycles_completed": step_idx + 1,
                    "current_mae": metrics.get("overall_mae", 0.0),
                    "current_directional_accuracy": metrics.get("directional_accuracy", 0.0),
                })
                await store_json(f"replay:{replay_id}", status)

        # Final metrics
        metrics = await self.evaluator.compute_metrics()
        status.update({
            "status": "completed",
            "progress_pct": 100.0,
            "cycles_completed": total_steps,
            "current_mae": metrics.get("overall_mae", 0.0),
            "current_directional_accuracy": metrics.get("directional_accuracy", 0.0),
        })
        await store_json(f"replay:{replay_id}", status)

        return status
