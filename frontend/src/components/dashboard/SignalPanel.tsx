"use client";
import { useSignals } from "@/hooks/useSignals";
import { TrendingDown, TrendingUp, Minus, Zap } from "lucide-react";

export function SignalPanel() {
  const { data, error, isLoading } = useSignals();

  if (isLoading) {
    return (
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
        <h2 className="text-sm font-medium text-[var(--muted-foreground)] mb-3 flex items-center gap-2">
          <Zap className="h-4 w-4" /> Live Signals
        </h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-[var(--muted)] rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
        <h2 className="text-sm font-medium text-[var(--negative)]">Signal feed unavailable</h2>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
      <h2 className="text-sm font-medium text-[var(--muted-foreground)] mb-3 flex items-center gap-2">
        <Zap className="h-4 w-4" /> Live Signals
      </h2>
      <div className="space-y-2">
        {data?.signals.map((signal) => {
          const isUp = (signal.change_pct ?? 0) > 0;
          const isDown = (signal.change_pct ?? 0) < 0;
          return (
            <div
              key={`${signal.source}-${signal.name}`}
              className="flex items-center justify-between p-3 rounded bg-[var(--muted)]"
            >
              <div>
                <p className="text-sm font-medium">{signal.name}</p>
                <p className="text-xs text-[var(--muted-foreground)]">{signal.source}</p>
              </div>
              <div className="text-right flex items-center gap-2">
                <div>
                  <p className="text-sm font-mono font-bold">
                    {signal.value.toLocaleString()} <span className="text-xs font-normal text-[var(--muted-foreground)]">{signal.unit}</span>
                  </p>
                  {signal.change_pct !== null && (
                    <p className={`text-xs ${isUp ? "text-[var(--negative)]" : isDown ? "text-[var(--positive)]" : "text-[var(--muted-foreground)]"}`}>
                      {signal.change_pct > 0 ? "+" : ""}{signal.change_pct.toFixed(1)}%
                    </p>
                  )}
                </div>
                {isUp ? <TrendingUp className="h-4 w-4 text-[var(--negative)]" /> :
                 isDown ? <TrendingDown className="h-4 w-4 text-[var(--positive)]" /> :
                 <Minus className="h-4 w-4 text-[var(--muted-foreground)]" />}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
