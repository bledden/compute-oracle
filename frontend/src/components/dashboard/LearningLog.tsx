"use client";
import { useLearningLog } from "@/hooks/useLearning";
import { BookOpen } from "lucide-react";

export function LearningLog() {
  const { data, isLoading } = useLearningLog();

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
      <h2 className="text-sm font-medium text-[var(--muted-foreground)] mb-3 flex items-center gap-2">
        <BookOpen className="h-4 w-4" /> Learning Log
      </h2>
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 bg-[var(--muted)] rounded animate-pulse" />
          ))}
        </div>
      ) : data && data.events.length > 0 ? (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {data.events.map((event, i) => (
            <div key={i} className="p-2 rounded bg-[var(--muted)] text-sm">
              <div className="flex items-center gap-2">
                <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--accent)]/20 text-[var(--accent)]">
                  #{event.cycle}
                </span>
                <span className="text-xs text-[var(--muted-foreground)]">{event.type}</span>
              </div>
              <p className="text-xs mt-1">{event.description}</p>
              {event.mae_before !== null && event.mae_after !== null && (
                <p className={`text-xs mt-0.5 ${
                  event.mae_after < event.mae_before ? "text-[var(--positive)]" : "text-[var(--negative)]"
                }`}>
                  MAE: {event.mae_before.toFixed(4)} → {event.mae_after.toFixed(4)}
                </p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-[var(--muted-foreground)] py-8 text-center">
          No learning events yet. Run prediction cycles to start learning.
        </p>
      )}
    </div>
  );
}
