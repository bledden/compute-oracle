from datetime import datetime, timezone
from typing import Any
from core.redis_client import store_json, get_json
from causal.factors import get_initial_graph

GRAPH_KEY = "causal_graph"


class CausalGraph:
    """Causal factor graph stored in Redis JSON.

    Nodes represent signals/factors and targets.
    Edges represent causal relationships with learned weights.
    """

    async def get_graph(self) -> dict[str, Any]:
        """Load the causal graph from Redis, or create the initial one."""
        graph = await get_json(GRAPH_KEY)
        if graph is None:
            graph = get_initial_graph()
            await store_json(GRAPH_KEY, graph)
        return graph

    async def update_edge(
        self,
        from_id: str,
        to_id: str,
        new_weight: float,
        new_confidence: float | None = None,
        new_direction: str | None = None,
    ) -> dict[str, Any]:
        """Update an edge's weight (and optionally confidence/direction)."""
        graph = await self.get_graph()
        edge_key = f"{from_id}->{to_id}"

        if edge_key in graph["edges"]:
            edge = graph["edges"][edge_key]
            edge["weight"] = max(0.0, min(1.0, new_weight))
            edge["update_count"] += 1
            edge["last_updated"] = datetime.now(timezone.utc).isoformat()
            if new_confidence is not None:
                edge["confidence"] = max(0.0, min(1.0, new_confidence))
            if new_direction is not None:
                edge["direction"] = new_direction

        graph["last_updated"] = datetime.now(timezone.utc).isoformat()
        await store_json(GRAPH_KEY, graph)
        return graph

    async def prune_edge(self, from_id: str, to_id: str) -> dict[str, Any]:
        """Remove an edge that has become irrelevant."""
        graph = await self.get_graph()
        edge_key = f"{from_id}->{to_id}"
        graph["edges"].pop(edge_key, None)
        graph["last_updated"] = datetime.now(timezone.utc).isoformat()
        await store_json(GRAPH_KEY, graph)
        return graph

    async def add_edge(
        self,
        from_id: str,
        to_id: str,
        weight: float = 0.3,
        direction: str = "positive",
    ) -> dict[str, Any]:
        """Add a new edge (discovered correlation)."""
        graph = await self.get_graph()
        edge_key = f"{from_id}->{to_id}"

        if edge_key not in graph["edges"]:
            graph["edges"][edge_key] = {
                "from": from_id,
                "to": to_id,
                "weight": weight,
                "confidence": 0.3,
                "direction": direction,
                "update_count": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        graph["last_updated"] = datetime.now(timezone.utc).isoformat()
        await store_json(GRAPH_KEY, graph)
        return graph

    async def increment_version(self) -> int:
        """Increment the graph version (called after learning updates)."""
        graph = await self.get_graph()
        graph["version"] = graph.get("version", 0) + 1
        graph["last_updated"] = datetime.now(timezone.utc).isoformat()
        await store_json(GRAPH_KEY, graph)
        return graph["version"]

    async def get_edges_for_target(self, target_id: str) -> list[dict[str, Any]]:
        """Get all edges pointing to a specific target."""
        graph = await self.get_graph()
        return [
            edge for edge in graph["edges"].values()
            if edge["to"] == target_id
        ]

    async def get_top_factors(self, target_id: str, n: int = 5) -> list[dict[str, Any]]:
        """Get the top N factors by weight for a target."""
        edges = await self.get_edges_for_target(target_id)
        return sorted(edges, key=lambda e: e["weight"], reverse=True)[:n]
