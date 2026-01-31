"use client";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export function MetricCard({ title, value, subtitle, trend, className }: MetricCardProps) {
  return (
    <div className={cn("rounded-lg border border-[var(--border)] bg-[var(--card)] p-4", className)}>
      <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wide">{title}</p>
      <p className={cn(
        "text-2xl font-bold mt-1",
        trend === "up" && "text-[var(--positive)]",
        trend === "down" && "text-[var(--negative)]",
      )}>
        {value}
      </p>
      {subtitle && (
        <p className="text-xs text-[var(--muted-foreground)] mt-1">{subtitle}</p>
      )}
    </div>
  );
}
