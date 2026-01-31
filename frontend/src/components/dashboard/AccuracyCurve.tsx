"use client";
import { useLearningMetrics } from "@/hooks/useLearning";
import { TrendingUp } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export function AccuracyCurve() {
  const { data, isLoading } = useLearningMetrics();

  if (isLoading || !data) {
    return (
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
        <h2 className="text-sm font-medium text-[var(--muted-foreground)] mb-3 flex items-center gap-2">
          <TrendingUp className="h-4 w-4" /> Learning Curve
        </h2>
        <div className="h-48 bg-[var(--muted)] rounded animate-pulse" />
      </div>
    );
  }

  const hasCycles = data.total_cycles > 0;

  // Build chart data from history arrays
  const chartData = data.mae_history.map((mae, i) => ({
    cycle: i + 1,
    mae: mae,
    accuracy: data.directional_accuracy_history[i] * 100,
  }));

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-medium text-[var(--muted-foreground)] flex items-center gap-2">
          <TrendingUp className="h-4 w-4" /> Learning Curve
        </h2>
        <span className="text-xs text-[var(--muted-foreground)]">
          {data.total_cycles} cycles | v{data.graph_versions}
        </span>
      </div>
      {hasCycles ? (
        <>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="text-center p-2 rounded bg-[var(--muted)]">
              <p className="text-xs text-[var(--muted-foreground)]">MAE</p>
              <p className="text-lg font-bold font-mono">${data.overall_mae.toFixed(4)}</p>
            </div>
            <div className="text-center p-2 rounded bg-[var(--muted)]">
              <p className="text-xs text-[var(--muted-foreground)]">Directional Accuracy</p>
              <p className="text-lg font-bold font-mono">{(data.directional_accuracy * 100).toFixed(1)}%</p>
            </div>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis
                  dataKey="cycle"
                  tick={{ fill: "#a1a1a1", fontSize: 11 }}
                  label={{ value: "Cycle", position: "insideBottomRight", offset: -5, fill: "#a1a1a1", fontSize: 11 }}
                />
                <YAxis
                  yAxisId="left"
                  tick={{ fill: "#a1a1a1", fontSize: 11 }}
                  label={{ value: "MAE ($)", angle: -90, position: "insideLeft", offset: 15, fill: "#a1a1a1", fontSize: 11 }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  domain={[0, 100]}
                  tick={{ fill: "#a1a1a1", fontSize: 11 }}
                  label={{ value: "Accuracy %", angle: 90, position: "insideRight", offset: 15, fill: "#a1a1a1", fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{ background: "#1a1a1a", border: "1px solid #262626", borderRadius: "6px", fontSize: 12 }}
                  labelStyle={{ color: "#a1a1a1" }}
                  formatter={(value: number, name: string) =>
                    name === "mae" ? [`$${value.toFixed(4)}`, "MAE"] : [`${value.toFixed(1)}%`, "Accuracy"]
                  }
                  labelFormatter={(label) => `Cycle ${label}`}
                />
                <Legend
                  wrapperStyle={{ fontSize: 11, color: "#a1a1a1" }}
                  formatter={(value) => (value === "mae" ? "MAE" : "Directional Accuracy")}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="mae"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={{ fill: "#ef4444", r: 3 }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={{ fill: "#22c55e", r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          {data.last_improvement && (
            <p className="text-xs text-[var(--muted-foreground)] mt-2 italic">
              Last: {data.last_improvement.change}
            </p>
          )}
        </>
      ) : (
        <div className="h-48 flex items-center justify-center text-[var(--muted-foreground)] text-sm">
          Awaiting prediction cycles to display learning curve...
        </div>
      )}
    </div>
  );
}
