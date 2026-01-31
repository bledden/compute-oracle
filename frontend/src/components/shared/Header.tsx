"use client";
import { useState } from "react";
import { Activity, Play, Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useSWRConfig } from "swr";

export function Header() {
  const [running, setRunning] = useState(false);
  const [lastResult, setLastResult] = useState<string | null>(null);
  const { mutate } = useSWRConfig();

  const runCycle = async () => {
    setRunning(true);
    setLastResult(null);
    try {
      // Get the latest prediction to provide as previous for evaluation
      let body: Record<string, unknown> = {};
      try {
        const latest = await apiFetch<{ prediction_id: string; current_price: number }>("/predictions/latest");
        if (latest.prediction_id && latest.prediction_id !== "awaiting_first_cycle") {
          // Simulate slight price variation for demo purposes
          const variation = (Math.random() - 0.45) * 0.06;
          body = {
            previous_prediction_id: latest.prediction_id,
            actual_price: Math.round((latest.current_price + variation) * 10000) / 10000,
          };
        }
      } catch {
        // No previous prediction, run without evaluation
      }

      const result = await apiFetch<{ cycle: number; prediction_id: string }>("/cycle/run", {
        method: "POST",
        body: JSON.stringify(body),
      });
      setLastResult(`Cycle #${result.cycle}`);

      // Revalidate all SWR caches
      mutate(() => true);
    } catch (err) {
      setLastResult("Error");
      console.error("Cycle failed:", err);
    } finally {
      setRunning(false);
    }
  };

  return (
    <header className="border-b border-[var(--border)] px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Activity className="h-6 w-6 text-[var(--accent)]" />
        <h1 className="text-xl font-semibold tracking-tight">Compute Oracle</h1>
        <span className="text-xs text-[var(--muted-foreground)] bg-[var(--muted)] px-2 py-0.5 rounded">
          v0.1.0
        </span>
      </div>
      <div className="flex items-center gap-4">
        {lastResult && (
          <span className="text-xs text-[var(--muted-foreground)]">{lastResult}</span>
        )}
        <button
          onClick={runCycle}
          disabled={running}
          className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md bg-[var(--accent)] text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          {running ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Play className="h-3.5 w-3.5" />
          )}
          {running ? "Running..." : "Run Cycle"}
        </button>
        <span className="text-xs text-[var(--muted-foreground)]">WeaveHacks 3</span>
      </div>
    </header>
  );
}
