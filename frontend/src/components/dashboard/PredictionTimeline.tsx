"use client";
import { usePredictions, usePredictionHistory } from "@/hooks/usePredictions";
import { Target } from "lucide-react";
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

export function PredictionTimeline() {
  const { data, isLoading } = usePredictions();
  const { data: history } = usePredictionHistory(20);

  if (isLoading || !data) {
    return (
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
        <h2 className="text-sm font-medium text-[var(--muted-foreground)] mb-3 flex items-center gap-2">
          <Target className="h-4 w-4" /> Predictions
        </h2>
        <div className="h-48 bg-[var(--muted)] rounded animate-pulse" />
      </div>
    );
  }

  // Build chart data from history
  const chartData = (history?.predictions ?? [])
    .slice()
    .reverse()
    .map((item) => ({
      cycle: item.cycle,
      predicted: item.predicted_price_1h,
      actual: item.actual_price_1h,
      error: item.error_1h,
      correct: item.direction_correct,
    }));

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-medium text-[var(--muted-foreground)] flex items-center gap-2">
          <Target className="h-4 w-4" /> Predictions
        </h2>
        <span className="text-xs text-[var(--muted-foreground)]">Cycle #{data.cycle}</span>
      </div>
      <div className="mb-3">
        <p className="text-sm">
          <span className="text-[var(--muted-foreground)]">Target:</span>{" "}
          <span className="font-mono">{data.target}</span>
        </p>
        <p className="text-sm">
          <span className="text-[var(--muted-foreground)]">Current:</span>{" "}
          <span className="font-mono font-bold">${data.current_price.toFixed(3)}/hr</span>
        </p>
      </div>
      <div className="space-y-2 mb-4">
        {data.predictions.map((pred) => (
          <div key={pred.horizon} className="flex items-center justify-between p-2 rounded bg-[var(--muted)]">
            <span className="text-sm font-medium">{pred.horizon}</span>
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm">${pred.predicted_price.toFixed(3)}</span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                pred.direction === "down" ? "bg-green-900/30 text-[var(--positive)]" :
                pred.direction === "up" ? "bg-red-900/30 text-[var(--negative)]" :
                "bg-gray-900/30 text-[var(--muted-foreground)]"
              }`}>
                {pred.direction}
              </span>
              <span className="text-xs text-[var(--muted-foreground)]">
                {(pred.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        ))}
      </div>

      {chartData.length > 1 && (
        <div className="h-36 mt-3">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis
                dataKey="cycle"
                tick={{ fill: "#a1a1a1", fontSize: 10 }}
              />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fill: "#a1a1a1", fontSize: 10 }}
                tickFormatter={(v: number) => `$${v.toFixed(2)}`}
              />
              <Tooltip
                contentStyle={{ background: "#1a1a1a", border: "1px solid #262626", borderRadius: "6px", fontSize: 11 }}
                formatter={(value: number, name: string) => [
                  `$${value.toFixed(4)}`,
                  name === "predicted" ? "Predicted" : name === "actual" ? "Actual" : "Error",
                ]}
                labelFormatter={(label) => `Cycle ${label}`}
              />
              <ReferenceLine y={data.current_price} stroke="#6366f1" strokeDasharray="3 3" />
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="#6366f1"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: "#6366f1", r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#ededed"
                strokeWidth={2}
                dot={{ fill: "#ededed", r: 3 }}
                connectNulls={false}
              />
              <Bar
                dataKey="error"
                fill="#ef4444"
                opacity={0.3}
                barSize={8}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      <p className="text-xs text-[var(--muted-foreground)] mt-3 italic">{data.causal_explanation}</p>
    </div>
  );
}
