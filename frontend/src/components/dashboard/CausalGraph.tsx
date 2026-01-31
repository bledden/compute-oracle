"use client";
import { useMemo, useCallback } from "react";
import { useCausalGraph } from "@/hooks/useCausalGraph";
import { GitBranch } from "lucide-react";
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  Position,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

function weightToColor(weight: number, direction: string): string {
  if (direction === "negative") {
    const intensity = Math.round(80 + weight * 175);
    return `rgb(${intensity}, 60, 60)`;
  }
  const intensity = Math.round(80 + weight * 175);
  return `rgb(60, ${intensity}, 60)`;
}

export function CausalGraph() {
  const { data, isLoading } = useCausalGraph();

  const { nodes, edges } = useMemo(() => {
    if (!data) return { nodes: [], edges: [] };

    const signalNodes = data.nodes.filter((n) => n.type === "signal" || n.type === "derived");
    const targetNodes = data.nodes.filter((n) => n.type === "target");

    const flowNodes: Node[] = [];

    // Signal nodes on the left
    signalNodes.forEach((node, i) => {
      flowNodes.push({
        id: node.id,
        data: { label: node.label },
        position: { x: 20, y: 30 + i * 70 },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        style: {
          background: "#1a1a1a",
          color: "#ededed",
          border: "1px solid #6366f1",
          borderRadius: "8px",
          padding: "8px 12px",
          fontSize: "11px",
          fontFamily: "monospace",
          width: 160,
        },
      });
    });

    // Target nodes on the right
    targetNodes.forEach((node, i) => {
      const centerY = (signalNodes.length * 70) / 2 - (targetNodes.length * 70) / 2;
      flowNodes.push({
        id: node.id,
        data: { label: node.label },
        position: { x: 400, y: centerY + i * 80 },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        style: {
          background: "#1a1a1a",
          color: "#ededed",
          border: "2px solid #eab308",
          borderRadius: "8px",
          padding: "8px 12px",
          fontSize: "11px",
          fontFamily: "monospace",
          width: 160,
        },
      });
    });

    const flowEdges: Edge[] = data.edges.map((edge, i) => ({
      id: `e-${i}`,
      source: edge.from,
      target: edge.to,
      animated: edge.weight > 0.7,
      style: {
        stroke: weightToColor(edge.weight, edge.direction),
        strokeWidth: Math.max(1, edge.weight * 4),
        opacity: Math.max(0.2, edge.weight),
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: weightToColor(edge.weight, edge.direction),
        width: 15,
        height: 15,
      },
      label: edge.weight.toFixed(2),
      labelStyle: {
        fill: "#a1a1a1",
        fontSize: 9,
        fontFamily: "monospace",
      },
      labelBgStyle: {
        fill: "#0a0a0a",
        fillOpacity: 0.8,
      },
    }));

    return { nodes: flowNodes, edges: flowEdges };
  }, [data]);

  const onInit = useCallback(() => {}, []);

  if (isLoading || !data) {
    return (
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 h-full">
        <h2 className="text-sm font-medium text-[var(--muted-foreground)] mb-3 flex items-center gap-2">
          <GitBranch className="h-4 w-4" /> Causal Graph
        </h2>
        <div className="h-64 bg-[var(--muted)] rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-medium text-[var(--muted-foreground)] flex items-center gap-2">
          <GitBranch className="h-4 w-4" /> Causal Graph
        </h2>
        <span className="text-xs text-[var(--muted-foreground)]">
          v{data.metadata.version} | {data.metadata.total_nodes} nodes, {data.metadata.total_edges} edges
        </span>
      </div>
      <div className="h-[400px] rounded overflow-hidden" style={{ background: "#0a0a0a" }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onInit={onInit}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          nodesDraggable={true}
          nodesConnectable={false}
          elementsSelectable={true}
          minZoom={0.3}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#262626" gap={20} />
          <Controls
            showInteractive={false}
            style={{ background: "#1a1a1a", border: "1px solid #262626", borderRadius: "6px" }}
          />
        </ReactFlow>
      </div>
    </div>
  );
}
