"use client";
import { useScheduler } from "@/hooks/useScheduler";
import { DollarSign } from "lucide-react";

export function SavingsTracker() {
  const { data, isLoading } = useScheduler();

  const savings = data?.cumulative_savings;

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
      <h2 className="text-sm font-medium text-[var(--muted-foreground)] mb-3 flex items-center gap-2">
        <DollarSign className="h-4 w-4" /> Savings Tracker
      </h2>
      {isLoading ? (
        <div className="h-24 bg-[var(--muted)] rounded animate-pulse" />
      ) : (
        <>
          <div className="text-center py-4">
            <p className="text-3xl font-bold text-[var(--positive)]">
              ${savings?.total_usd.toFixed(2) ?? "0.00"}
            </p>
            <p className="text-sm text-[var(--muted-foreground)] mt-1">
              {savings?.vs_naive_pct ?? 0}% vs naive scheduling
            </p>
          </div>
          <div className="flex justify-between text-xs text-[var(--muted-foreground)] border-t border-[var(--border)] pt-2">
            <span>{savings?.workloads_optimized ?? 0} workloads optimized</span>
            <span>${data?.current_price.toFixed(3)}/hr current</span>
          </div>
        </>
      )}
    </div>
  );
}
