"use client"

import { Skeleton } from "@/components/ui/skeleton"

interface PanelSkeletonProps {
  lines?: number
}

export function PanelSkeleton({ lines = 5 }: PanelSkeletonProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-3/4 bg-muted" />
          <Skeleton className="h-3 w-1/2 bg-muted" />
        </div>
      ))}
    </div>
  )
}

export function ChartSkeleton() {
  return (
    <div className="flex h-48 items-end gap-2 pt-4">
      {Array.from({ length: 12 }).map((_, i) => (
        <Skeleton
          key={i}
          className="flex-1 bg-muted"
          style={{ height: `${30 + Math.random() * 70}%` }}
        />
      ))}
    </div>
  )
}
