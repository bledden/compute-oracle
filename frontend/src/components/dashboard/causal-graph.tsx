"use client"

import { useCallback, useMemo } from "react"
import { GitBranch, AlertCircle, ZoomIn, ZoomOut } from "lucide-react"
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  MarkerType,
  type Node,
  type Edge,
  type NodeProps,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useCausalGraph } from "@/hooks/use-oracle-data"
import { PanelSkeleton } from "./panel-skeleton"
import { cn } from "@/lib/utils"

interface CustomNodeData extends Record<string, unknown> {
  label: string
  nodeType: "signal" | "derived" | "target"
}

function CustomNode({ data }: NodeProps<Node<CustomNodeData>>) {
  const borderColor =
    data.nodeType === "target"
      ? "border-amber-500"
      : data.nodeType === "signal"
        ? "border-primary"
        : "border-muted-foreground"

  return (
    <div
      className={cn(
        "rounded-lg border-2 bg-[#171717] px-3 py-2 shadow-lg",
        borderColor
      )}
    >
      <Handle type="target" position={Position.Left} className="!bg-muted-foreground" />
      <p className="text-xs font-medium text-foreground">{data.label}</p>
      <Handle type="source" position={Position.Right} className="!bg-muted-foreground" />
    </div>
  )
}

const nodeTypes = {
  custom: CustomNode,
}

export function CausalGraph() {
  const { data: graphData, error, isLoading } = useCausalGraph()

  const { initialNodes, initialEdges } = useMemo(() => {
    if (!graphData) return { initialNodes: [], initialEdges: [] }

    const signalNodes = graphData.nodes.filter((n) => n.type === "signal" || n.type === "derived")
    const targetNodes = graphData.nodes.filter((n) => n.type === "target")

    const nodes: Node<CustomNodeData>[] = [
      ...signalNodes.map((node, index) => ({
        id: node.id,
        type: "custom",
        position: { x: 50, y: 40 + index * 60 },
        data: { label: node.label, nodeType: node.type },
      })),
      ...targetNodes.map((node, index) => ({
        id: node.id,
        type: "custom",
        position: { x: 350, y: 80 + index * 80 },
        data: { label: node.label, nodeType: node.type },
      })),
    ]

    const edges: Edge[] = graphData.edges.map((edge, index) => ({
      id: `e-${index}`,
      source: edge.from,
      target: edge.to,
      type: "default",
      animated: edge.weight > 0.7,
      style: {
        stroke: edge.direction === "positive" ? "#22c55e" : "#ef4444",
        strokeWidth: Math.max(1, edge.weight * 4),
        opacity: 0.3 + edge.weight * 0.7,
      },
      label: edge.weight.toFixed(2),
      labelStyle: {
        fill: "#a3a3a3",
        fontSize: 9,
        fontFamily: "monospace",
      },
      labelBgStyle: {
        fill: "#171717",
        fillOpacity: 0.8,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: edge.direction === "positive" ? "#22c55e" : "#ef4444",
      },
    }))

    return { initialNodes: nodes, initialEdges: edges }
  }, [graphData])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Update nodes/edges when data changes
  useMemo(() => {
    if (initialNodes.length > 0) {
      setNodes(initialNodes)
      setEdges(initialEdges)
    }
  }, [initialNodes, initialEdges, setNodes, setEdges])

  return (
    <Card className="col-span-7 border-border bg-[#0a0a0a]">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm font-medium text-foreground">
            <GitBranch className="h-4 w-4 text-primary" />
            Causal Graph
          </CardTitle>
          {graphData && (
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-mono text-xs">
                v{graphData.metadata.version}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {graphData.metadata.total_nodes} nodes / {graphData.metadata.total_edges} edges
              </span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load causal graph</span>
          </div>
        ) : isLoading ? (
          <PanelSkeleton lines={8} />
        ) : (
          <div className="h-[340px] rounded-lg border border-border bg-[#0a0a0a]">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              fitView
              fitViewOptions={{ padding: 0.2 }}
              proOptions={{ hideAttribution: true }}
              minZoom={0.5}
              maxZoom={1.5}
            >
              <Background color="#262626" gap={16} />
              <Controls
                showInteractive={false}
                className="!bg-secondary !border-border [&>button]:!bg-secondary [&>button]:!border-border [&>button]:!text-foreground [&>button:hover]:!bg-muted"
              />
            </ReactFlow>
          </div>
        )}
        {/* Legend */}
        <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="h-2 w-4 rounded bg-green-500" />
            <span>Positive</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-2 w-4 rounded bg-red-500" />
            <span>Negative</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-3 w-3 rounded border-2 border-primary" />
            <span>Signal</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-3 w-3 rounded border-2 border-amber-500" />
            <span>Target</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
