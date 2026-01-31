"use client"

import { TrendingUp, AlertCircle } from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useLearningMetrics } from "@/hooks/use-oracle-data"
import { PanelSkeleton, ChartSkeleton } from "./panel-skeleton"

export function LearningCurve() {
  const { data: metrics, error, isLoading } = useLearningMetrics()

  const chartData = metrics?.mae_history.map((mae, index) => ({
    cycle: index + 1,
    mae,
    accuracy: (metrics.directional_accuracy_history[index] || 0) * 100,
  }))

  return (
    <Card className="col-span-5 border-border bg-[#0a0a0a]">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm font-medium text-foreground">
            <TrendingUp className="h-4 w-4 text-primary" />
            Learning Curve
          </CardTitle>
          {metrics && (
            <span className="text-xs text-muted-foreground">
              {metrics.total_cycles} cycles | v{metrics.graph_versions}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load learning metrics</span>
          </div>
        ) : isLoading ? (
          <>
            <PanelSkeleton lines={2} />
            <ChartSkeleton />
          </>
        ) : (
          <>
            {/* Metric Cards */}
            <div className="mb-4 grid grid-cols-2 gap-3">
              <div className="rounded-lg border border-border bg-secondary/30 p-3">
                <p className="text-xs text-muted-foreground">Mean Absolute Error</p>
                <p className="font-mono text-xl font-bold text-foreground">
                  ${metrics?.overall_mae.toFixed(4)}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-secondary/30 p-3">
                <p className="text-xs text-muted-foreground">Directional Accuracy</p>
                <p className="font-mono text-xl font-bold text-foreground">
                  {((metrics?.directional_accuracy || 0) * 100).toFixed(1)}%
                </p>
              </div>
            </div>

            {/* Chart */}
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                  <XAxis
                    dataKey="cycle"
                    tick={{ fill: "#a3a3a3", fontSize: 10 }}
                    tickLine={{ stroke: "#262626" }}
                    axisLine={{ stroke: "#262626" }}
                  />
                  <YAxis
                    yAxisId="left"
                    tick={{ fill: "#a3a3a3", fontSize: 10 }}
                    tickLine={{ stroke: "#262626" }}
                    axisLine={{ stroke: "#262626" }}
                    tickFormatter={(v) => `$${v.toFixed(2)}`}
                    domain={["auto", "auto"]}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fill: "#a3a3a3", fontSize: 10 }}
                    tickLine={{ stroke: "#262626" }}
                    axisLine={{ stroke: "#262626" }}
                    tickFormatter={(v) => `${v}%`}
                    domain={[0, 100]}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#171717",
                      border: "1px solid #262626",
                      borderRadius: "8px",
                    }}
                    labelStyle={{ color: "#fafafa" }}
                    formatter={(value: number, name: string) => [
                      name === "mae" ? `$${value.toFixed(4)}` : `${value.toFixed(1)}%`,
                      name === "mae" ? "MAE" : "Accuracy",
                    ]}
                    labelFormatter={(label) => `Cycle ${label}`}
                  />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="mae"
                    stroke="#ef4444"
                    strokeWidth={2}
                    dot={{ fill: "#ef4444", r: 2 }}
                    name="mae"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="accuracy"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={{ fill: "#22c55e", r: 2 }}
                    name="accuracy"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Legend */}
            <div className="mt-2 flex items-center justify-center gap-4 text-xs">
              <div className="flex items-center gap-1">
                <div className="h-0.5 w-4 bg-red-500" />
                <span className="text-muted-foreground">MAE (lower is better)</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="h-0.5 w-4 bg-green-500" />
                <span className="text-muted-foreground">Accuracy (higher is better)</span>
              </div>
            </div>

            {/* Last Improvement */}
            {metrics?.last_improvement && (
              <p className="mt-3 text-sm italic text-muted-foreground">
                Last improvement (cycle {metrics.last_improvement.cycle}): {metrics.last_improvement.change}
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
