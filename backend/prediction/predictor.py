import json
import uuid
from datetime import datetime, timezone
from typing import Any
import weave

from core.llm_client import get_llm_client, PREDICTOR_MODEL
from core.redis_client import store_json, get_redis
from causal.graph import CausalGraph

PREDICTION_PROMPT = """You are a compute pricing prediction engine.

## Current Causal Graph Weights
Higher weight = stronger causal influence on pricing.
{edges_formatted}

## Current Signal Values
{signals_formatted}

## Target
Predict the spot price of {target_instance} in {target_az}.
Current price: ${current_price}/hr

## Instructions
Predict the price at 3 horizons: 1h, 4h, 24h.
For each horizon provide: predicted_price (USD), direction (up/down/flat), confidence (0.0-1.0).
Also list the top contributing factors and a brief causal explanation.

Lower confidence for longer horizons. Higher confidence when multiple causal factors agree.

Respond in this exact JSON format (no markdown fences, just raw JSON):
{{
  "predictions": [
    {{"horizon": "1h", "predicted_price": 1.05, "direction": "down", "confidence": 0.80}},
    {{"horizon": "4h", "predicted_price": 1.02, "direction": "down", "confidence": 0.65}},
    {{"horizon": "24h", "predicted_price": 1.10, "direction": "up", "confidence": 0.45}}
  ],
  "contributing_factors": [
    {{"factor": "electricity_demand_pjm", "contribution": 0.4, "direction": "bearish"}},
    {{"factor": "time_of_day", "contribution": 0.3, "direction": "bearish"}}
  ],
  "causal_explanation": "Brief 1-2 sentence explanation of the causal chain."
}}"""


class PricePredictor:
    """Generates price forecasts using Qwen3 (via W&B Inference) with causal graph context."""

    def __init__(self):
        self.graph = CausalGraph()

    @weave.op()
    async def predict(
        self,
        signals: list[dict[str, Any]],
        target_instance: str = "p3.2xlarge",
        target_az: str = "us-east-1a",
        cycle: int = 0,
    ) -> dict[str, Any]:
        """Generate a price prediction for the target instance."""
        graph_data = await self.graph.get_graph()

        # Find current price for target
        current_price = None
        for s in signals:
            if s.get("instance_type") == target_instance or target_instance in s.get("name", ""):
                if target_az in s.get("name", "") or target_az in s.get("az", ""):
                    current_price = s["value"]
                    break

        if current_price is None:
            current_price = 1.07

        # Format for prompt
        edges_formatted = self._format_edges(graph_data, f"spot_price_{target_instance.replace('.', '_')}")
        signals_formatted = self._format_signals(signals)

        prompt = PREDICTION_PROMPT.format(
            edges_formatted=edges_formatted,
            signals_formatted=signals_formatted,
            target_instance=target_instance,
            target_az=target_az,
            current_price=f"{current_price:.4f}",
        )

        client = get_llm_client()
        response = await client.chat.completions.create(
            model=PREDICTOR_MODEL,
            messages=[
                {"role": "system", "content": "You are a quantitative pricing prediction engine. Be precise with numbers. Always respond with valid JSON only, no markdown fences or extra text."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )

        text = response.choices[0].message.content
        # Strip any markdown fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        result = json.loads(text)

        # Build full prediction record
        prediction_id = f"pred_{uuid.uuid4().hex[:8]}"
        prediction = {
            "prediction_id": prediction_id,
            "cycle": cycle,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": f"{target_instance} {target_az}",
            "current_price": current_price,
            "predictions": result.get("predictions", []),
            "contributing_factors": result.get("contributing_factors", []),
            "causal_explanation": result.get("causal_explanation", ""),
        }

        # Store prediction in Redis
        await store_json(f"prediction:{prediction_id}", prediction)

        # Add to sorted index
        r = await get_redis()
        ts = datetime.now(timezone.utc).timestamp()
        await r.zadd("predictions:index", {prediction_id: ts})

        return prediction

    def _format_edges(self, graph: dict, target_id: str) -> str:
        lines = []
        for edge in sorted(
            graph.get("edges", {}).values(),
            key=lambda e: e.get("weight", 0),
            reverse=True,
        ):
            if edge["to"] == target_id or True:  # Show all for context
                lines.append(
                    f"- {edge['from']} → {edge['to']}: "
                    f"weight={edge['weight']:.2f}, direction={edge['direction']}"
                )
        return "\n".join(lines[:15]) if lines else "No edges."

    def _format_signals(self, signals: list[dict[str, Any]]) -> str:
        lines = []
        for s in signals:
            lines.append(f"- {s.get('name', 'unknown')}: {s['value']} {s.get('unit', '')}")

        # Add derived signals
        now = datetime.now(timezone.utc)
        lines.append(f"- Time of day: {now.hour}:00 UTC")
        lines.append(f"- Day of week: {now.strftime('%A')} ({'weekend' if now.weekday() >= 5 else 'weekday'})")

        return "\n".join(lines)
