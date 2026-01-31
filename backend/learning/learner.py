from datetime import datetime, timezone
from typing import Any
import weave

from causal.graph import CausalGraph
from core.redis_client import push_to_list
from learning.strategies import exponential_weight_update, adaptive_alpha


class CausalLearner:
    """Updates the causal graph based on prediction evaluation results.

    This is THE self-improvement engine — the core differentiator.
    After each evaluation, it strengthens factors that predicted correctly
    and weakens factors that predicted incorrectly.
    """

    def __init__(self):
        self.graph = CausalGraph()

    @weave.op()
    async def learn(
        self,
        evaluation: dict[str, Any],
        cycle: int,
    ) -> dict[str, Any]:
        """Update causal graph edge weights based on evaluation results."""
        graph_data = await self.graph.get_graph()
        contributing_factors = evaluation.get("contributing_factors", [])
        direction_correct = evaluation.get("direction_correct", False)
        mae_before = evaluation.get("absolute_error", 0.0)

        alpha = adaptive_alpha(cycle)
        events = []

        for factor_info in contributing_factors:
            factor_id = factor_info["factor"]
            factor_direction = factor_info.get("direction", "neutral")

            # Find all edges from this factor
            for edge_key, edge in graph_data.get("edges", {}).items():
                if edge["from"] != factor_id:
                    continue

                old_weight = edge["weight"]

                # Determine if this factor's contribution was helpful
                # If factor said "bearish" and price actually went down → correct
                # If factor said "bullish" and price actually went up → correct
                actual_direction = evaluation.get("actual_direction", "flat")
                factor_was_correct = (
                    (factor_direction == "bearish" and actual_direction == "down") or
                    (factor_direction == "bullish" and actual_direction == "up") or
                    (factor_direction == "neutral" and actual_direction == "flat")
                )

                # If overall direction was correct, boost all contributing factors
                # If overall direction was wrong, weaken factors proportional to contribution
                if direction_correct:
                    new_weight = exponential_weight_update(old_weight, True, alpha)
                    event_type = "edge_weight_update"
                    desc = (f"Strengthened {factor_id} → {edge['to']}: "
                            f"{old_weight:.3f} → {new_weight:.3f} "
                            f"(prediction correct, factor was {factor_direction})")
                elif factor_was_correct:
                    # Factor was right but overall was wrong — small boost
                    new_weight = exponential_weight_update(old_weight, True, alpha * 0.3)
                    event_type = "edge_weight_update"
                    desc = (f"Slightly strengthened {factor_id} → {edge['to']}: "
                            f"{old_weight:.3f} → {new_weight:.3f} "
                            f"(factor was correct but overall prediction missed)")
                else:
                    new_weight = exponential_weight_update(old_weight, False, alpha)
                    event_type = "edge_weight_update"
                    desc = (f"Weakened {factor_id} → {edge['to']}: "
                            f"{old_weight:.3f} → {new_weight:.3f} "
                            f"(prediction incorrect, factor was {factor_direction})")

                # Prune edges that fall below threshold
                if new_weight < 0.05:
                    event_type = "edge_pruned"
                    desc = (f"Pruned {factor_id} → {edge['to']} "
                            f"(weight fell to {new_weight:.3f} after incorrect predictions)")
                    await self.graph.prune_edge(factor_id, edge["to"])
                else:
                    await self.graph.update_edge(factor_id, edge["to"], new_weight)

                events.append({
                    "cycle": cycle,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "type": event_type,
                    "description": desc,
                    "mae_before": round(mae_before, 6),
                    "mae_after": round(evaluation.get("absolute_error", 0.0), 6),
                    "old_weight": round(old_weight, 4),
                    "new_weight": round(new_weight, 4),
                    "factor": factor_id,
                })

        # Increment graph version
        new_version = await self.graph.increment_version()

        # Log all learning events
        for event in events:
            await push_to_list("learning:log", event)

        return {
            "cycle": cycle,
            "events": events,
            "graph_version": new_version,
            "direction_correct": direction_correct,
        }
