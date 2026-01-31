"""The core prediction cycle orchestrator.

This runs the complete self-improvement loop:
  ingest signals → load causal graph → predict → evaluate → learn → repeat
"""

from datetime import datetime, timezone
from typing import Any
import weave

from core.redis_client import get_latest_signals, get_redis, store_json, get_json
from ingestion.aws_spot import AWSSpotSource
from ingestion.eia_electricity import EIAElectricitySource
from ingestion.weather import WeatherSource
from causal.reasoner import CausalReasoner
from prediction.predictor import PricePredictor
from evaluation.evaluator import PredictionEvaluator
from learning.learner import CausalLearner


class OracleOrchestrator:
    """Orchestrates the full predict → evaluate → learn cycle."""

    def __init__(self):
        self.aws_source = AWSSpotSource()
        self.eia_source = EIAElectricitySource()
        self.weather_source = WeatherSource()
        self.reasoner = CausalReasoner()
        self.predictor = PricePredictor()
        self.evaluator = PredictionEvaluator()
        self.learner = CausalLearner()

    async def _get_cycle_count(self) -> int:
        r = await get_redis()
        count = await r.get("oracle:cycle_count")
        return int(count) if count else 0

    async def _increment_cycle(self) -> int:
        r = await get_redis()
        return await r.incr("oracle:cycle_count")

    @weave.op()
    async def run_cycle(
        self,
        signals: list[dict[str, Any]] | None = None,
        actual_price: float | None = None,
        previous_prediction_id: str | None = None,
    ) -> dict[str, Any]:
        """Run one complete prediction cycle.

        In live mode: signals are fetched fresh, actual_price comes later.
        In replay mode: signals and actual_price are provided directly.
        """
        cycle = await self._increment_cycle()
        results: dict[str, Any] = {"cycle": cycle, "timestamp": datetime.now(timezone.utc).isoformat()}

        # Step 1: Get signals (if not provided)
        if signals is None:
            signals = await get_latest_signals()
            if not signals:
                # Fetch fresh if Redis is empty
                await self.aws_source.ingest()
                signals = await get_latest_signals()
        results["signal_count"] = len(signals)

        # Step 2: Make prediction
        prediction = await self.predictor.predict(
            signals=signals,
            target_instance="p3.2xlarge",
            target_az="us-east-1a",
            cycle=cycle,
        )
        results["prediction_id"] = prediction["prediction_id"]
        results["predicted_price_1h"] = prediction["predictions"][0]["predicted_price"] if prediction["predictions"] else None

        # Step 3: Evaluate previous prediction (if we have ground truth)
        if previous_prediction_id and actual_price is not None:
            evaluation = await self.evaluator.evaluate(
                prediction_id=previous_prediction_id,
                actual_price=actual_price,
            )
            results["evaluation"] = {
                "previous_prediction_id": previous_prediction_id,
                "absolute_error": evaluation.get("absolute_error"),
                "direction_correct": evaluation.get("direction_correct"),
            }

            # Step 4: Learn from evaluation
            learn_result = await self.learner.learn(
                evaluation=evaluation,
                cycle=cycle,
            )
            results["learning"] = {
                "events_count": len(learn_result.get("events", [])),
                "graph_version": learn_result.get("graph_version"),
                "direction_correct": learn_result.get("direction_correct"),
            }

        # Store cycle result
        await store_json(f"cycle:{cycle}", results)

        return results

    @weave.op()
    async def run_replay_cycle(
        self,
        signals: list[dict[str, Any]],
        actual_price_1h: float,
        previous_prediction_id: str | None,
    ) -> dict[str, Any]:
        """Run a cycle in replay/backtest mode where ground truth is known."""
        return await self.run_cycle(
            signals=signals,
            actual_price=actual_price_1h,
            previous_prediction_id=previous_prediction_id,
        )
