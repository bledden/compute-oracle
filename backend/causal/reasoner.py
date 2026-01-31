import json
from typing import Any
import weave

from core.llm_client import get_llm_client, REASONER_MODEL
from causal.graph import CausalGraph

REASONING_PROMPT = """You are a causal reasoning engine for compute cost prediction.

You analyze real-world signals and determine how they causally influence cloud compute (GPU spot instance) pricing.

## Current Signals
{signals_formatted}

## Current Causal Graph (factor → target, weight)
Higher weight = stronger causal influence (0.0 to 1.0).
{edges_formatted}

## Your Task
Based on the current signals and causal relationships:

1. For each target (spot price), identify which factors are MOST relevant RIGHT NOW
2. Predict the price DIRECTION for each target: "up", "down", or "flat"
3. Provide a confidence score (0.0 to 1.0) for each prediction
4. Explain the causal reasoning in 1-2 sentences

## Key Causal Patterns to Consider
- Higher electricity demand → higher data center operating costs → higher spot prices
- Higher temperature → higher cooling costs → higher electricity demand → higher spot prices
- Night hours (UTC 04:00-12:00) → lower demand → lower spot prices
- Weekends → lower enterprise demand → lower spot prices
- us-east-1 generally has higher demand and prices than us-west-2

Respond in this exact JSON format (no markdown fences, just raw JSON):
{{
  "predictions": [
    {{
      "target": "spot_price_p3_2xlarge",
      "direction": "down",
      "confidence": 0.75,
      "contributing_factors": [
        {{"factor": "electricity_demand_pjm", "contribution": 0.4, "direction": "bearish"}},
        {{"factor": "time_of_day", "contribution": 0.3, "direction": "bearish"}}
      ]
    }}
  ],
  "causal_explanation": "PJM electricity demand is declining as we enter evening hours, which historically correlates with lower us-east-1 spot pricing."
}}"""


class CausalReasoner:
    """LLM-based causal reasoning over signals and the causal graph."""

    def __init__(self):
        self.graph = CausalGraph()

    @weave.op()
    async def reason(
        self, signals: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Use DeepSeek R1 (via W&B Inference) to reason about causal relationships."""
        graph_data = await self.graph.get_graph()

        # Format signals for the prompt
        signals_formatted = self._format_signals(signals)
        edges_formatted = self._format_edges(graph_data)

        prompt = REASONING_PROMPT.format(
            signals_formatted=signals_formatted,
            edges_formatted=edges_formatted,
        )

        client = get_llm_client()
        response = await client.chat.completions.create(
            model=REASONER_MODEL,
            messages=[
                {"role": "system", "content": "You are a quantitative analyst specializing in cloud computing cost prediction. Always respond with valid JSON only, no markdown fences or extra text."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
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
        return result

    def _format_signals(self, signals: list[dict[str, Any]]) -> str:
        lines = []
        for s in signals:
            change = f" ({s.get('change_pct', 'N/A')}%)" if s.get("change_pct") else ""
            lines.append(f"- {s['name']} ({s['source']}): {s['value']} {s.get('unit', '')}{change}")
        return "\n".join(lines) if lines else "No signals available."

    def _format_edges(self, graph: dict[str, Any]) -> str:
        lines = []
        for edge in sorted(
            graph.get("edges", {}).values(),
            key=lambda e: e.get("weight", 0),
            reverse=True,
        ):
            lines.append(
                f"- {edge['from']} → {edge['to']}: "
                f"weight={edge['weight']:.2f}, "
                f"direction={edge['direction']}, "
                f"confidence={edge['confidence']:.2f}"
            )
        return "\n".join(lines) if lines else "No edges yet."
