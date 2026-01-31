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

    def _extract_target_price(
        self, signals: list[dict[str, Any]],
        instance: str = "p3.2xlarge", az: str = "us-east-1a",
    ) -> float | None:
        """Extract the current price for the target instance from fresh signals."""
        for s in signals:
            if instance in s.get("name", "") and az in s.get("name", ""):
                return s["value"]
            if s.get("instance_type") == instance and s.get("az") == az:
                return s["value"]
        return None

    async def _get_previous_prediction_id(self) -> str | None:
        """Get the most recent prediction ID from Redis."""
        r = await get_redis()
        ids = await r.zrevrange("predictions:index", 0, 0)
        if ids:
            return ids[0] if isinstance(ids[0], str) else ids[0].decode()
        return None

    @weave.op()
    async def run_cycle(
        self,
        signals: list[dict[str, Any]] | None = None,
        actual_price: float | None = None,
        previous_prediction_id: str | None = None,
    ) -> dict[str, Any]:
        """Run one complete prediction cycle.

        In live mode: signals are fetched fresh, the current spot price
        serves as ground truth for the previous prediction.
        In replay mode: signals and actual_price are provided directly.
        """
        cycle = await self._increment_cycle()
        results: dict[str, Any] = {"cycle": cycle, "timestamp": datetime.now(timezone.utc).isoformat()}

        # Step 1: Ingest fresh signals
        if signals is None:
            await self.aws_source.ingest()
            signals = await get_latest_signals()
            if not signals:
                signals = []
        results["signal_count"] = len(signals)

        # Step 2: In live mode, use the freshly ingested current price
        # as ground truth for the previous prediction
        if previous_prediction_id is None and actual_price is None:
            previous_prediction_id = await self._get_previous_prediction_id()
            if previous_prediction_id:
                actual_price = self._extract_target_price(signals)

        # Step 3: Make prediction
        prediction = await self.predictor.predict(
            signals=signals,
            target_instance="p3.2xlarge",
            target_az="us-east-1a",
            cycle=cycle,
        )
        results["prediction_id"] = prediction["prediction_id"]
        results["predicted_price_1h"] = prediction["predictions"][0]["predicted_price"] if prediction["predictions"] else None

        # Step 4: Evaluate previous prediction (if we have ground truth)
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

            # Step 5: Learn from evaluation
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
