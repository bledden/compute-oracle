"use client";
import { useScheduler } from "@/hooks/useScheduler";
import { Clock, ArrowDown } from "lucide-react";

export function SchedulerView() {
  const { data, isLoading } = useScheduler();

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
      <h2 className="text-sm font-medium text-[var(--muted-foreground)] mb-3 flex items-center gap-2">
        <Clock className="h-4 w-4" /> Scheduler
      </h2>
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-[var(--muted)] rounded animate-pulse" />
          ))}
        </div>
      ) : data && data.windows.length > 0 ? (
        <>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {data.windows.map((window, i) => (
              <div key={i} className="flex items-center justify-between p-2 rounded bg-[var(--muted)]">
                <div className="flex items-center gap-2">
                  <ArrowDown className="h-3.5 w-3.5 text-[var(--positive)]" />
                  <span className="font-mono text-sm">${window.predicted_avg_price.toFixed(3)}/hr</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs px-2 py-0.5 rounded bg-green-900/30 text-[var(--positive)]">
                    -{window.savings_pct}%
                  </span>
                  <span className="text-xs text-[var(--muted-foreground)]">
                    {(window.confidence * 100).toFixed(0)}% conf
                  </span>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-[var(--muted-foreground)] mt-3 italic">
            {data.recommendation}
          </p>
        </>
      ) : (
        <p className="text-sm text-[var(--muted-foreground)] py-8 text-center">
          Run prediction cycles to generate scheduling recommendations.
        </p>
      )}
    </div>
  );
}
