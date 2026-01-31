"use client"

import { Target, TrendingUp, TrendingDown, Minus, AlertCircle } from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  ErrorBar,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { usePredictions, usePredictionHistory } from "@/hooks/use-oracle-data"
import { PanelSkeleton, ChartSkeleton } from "./panel-skeleton"
import { cn } from "@/lib/utils"

export function PredictionPanel() {
  const { data: prediction, error: predictionError, isLoading: predictionLoading } = usePredictions()
  const { data: history, error: historyError, isLoading: historyLoading } = usePredictionHistory()

  const error = predictionError || historyError
  const isLoading = predictionLoading || historyLoading

  const chartData = history?.predictions
    .slice()
    .reverse()
    .map((p, idx) => ({
      cycle: p.cycle,
      predicted: p.predicted_price_1h,
      actual: p.actual_price_1h,
      error: p.error_1h ? [p.error_1h * 0.5, p.error_1h * 0.5] : undefined,
    }))

  return (
    <Card className="col-span-5 border-border bg-[#0a0a0a]">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-foreground">
          <Target className="h-4 w-4 text-primary" />
          Predictions
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load predictions</span>
          </div>
        ) : isLoading ? (
          <>
            <PanelSkeleton lines={3} />
            <ChartSkeleton />
          </>
        ) : (
          <>
            {/* Target Info */}
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Target Instance</p>
                <p className="font-medium text-foreground">{prediction?.target}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Current Price</p>
                <p className="font-mono text-lg font-bold text-foreground">
                  ${prediction?.current_price.toFixed(3)}
                </p>
              </div>
            </div>

            {/* Prediction Horizons */}
            <div className="mb-4 space-y-2">
              {prediction?.predictions.map((pred) => (
                <div
                  key={pred.horizon}
                  className="flex items-center justify-between rounded-lg border border-border bg-secondary/30 p-3"
                >
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="font-mono text-xs">
                      {pred.horizon}
                    </Badge>
                    <span className="font-mono text-sm font-bold text-foreground">
                      ${pred.predicted_price.toFixed(3)}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge
                      className={cn(
                        "flex items-center gap-1",
                        pred.direction === "down"
                          ? "bg-green-500/10 text-green-500"
                          : pred.direction === "up"
                            ? "bg-red-500/10 text-red-500"
                            : "bg-muted text-muted-foreground"
                      )}
                    >
                      {pred.direction === "down" ? (
                        <TrendingDown className="h-3 w-3" />
                      ) : pred.direction === "up" ? (
                        <TrendingUp className="h-3 w-3" />
                      ) : (
                        <Minus className="h-3 w-3" />
                      )}
                      {pred.direction}
                    </Badge>
                    <span className="font-mono text-xs text-muted-foreground">
                      {(pred.confidence * 100).toFixed(0)}% conf
                    </span>
                  </div>
                </div>
              ))}
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
                    tick={{ fill: "#a3a3a3", fontSize: 10 }}
                    tickLine={{ stroke: "#262626" }}
                    axisLine={{ stroke: "#262626" }}
                    tickFormatter={(v) => `$${v.toFixed(2)}`}
                    domain={["auto", "auto"]}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#171717",
                      border: "1px solid #262626",
                      borderRadius: "8px",
                    }}
                    labelStyle={{ color: "#fafafa" }}
                    itemStyle={{ color: "#a3a3a3" }}
                    formatter={(value: number) => [`$${value?.toFixed(3) || "N/A"}`, ""]}
                  />
                  {prediction && (
                    <ReferenceLine
                      y={prediction.current_price}
                      stroke="#6366f1"
                      strokeDasharray="5 5"
                      strokeOpacity={0.5}
                    />
                  )}
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="#6366f1"
                    strokeDasharray="5 5"
                    strokeWidth={2}
                    dot={{ fill: "#6366f1", r: 3 }}
                    name="Predicted"
                  />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    stroke="#fafafa"
                    strokeWidth={2}
                    dot={{ fill: "#fafafa", r: 3 }}
                    name="Actual"
                    connectNulls={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Causal Explanation */}
            {prediction?.causal_explanation && (
              <p className="mt-4 text-sm italic text-muted-foreground">
                {prediction.causal_explanation}
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
