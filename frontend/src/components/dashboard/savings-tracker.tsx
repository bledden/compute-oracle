"use client"

import { DollarSign, AlertCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useScheduler, usePredictions } from "@/hooks/use-oracle-data"
import { PanelSkeleton } from "./panel-skeleton"

export function SavingsTracker() {
  const { data: scheduler, error: schedulerError, isLoading: schedulerLoading } = useScheduler()
  const { data: predictions, error: predictionsError, isLoading: predictionsLoading } = usePredictions()

  const error = schedulerError || predictionsError
  const isLoading = schedulerLoading || predictionsLoading

  return (
    <Card className="col-span-3 border-border bg-[#0a0a0a]">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-foreground">
          <DollarSign className="h-4 w-4 text-green-500" />
          Savings
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load savings</span>
          </div>
        ) : isLoading ? (
          <PanelSkeleton lines={3} />
        ) : (
          <div className="flex flex-col items-center justify-center py-4">
            <p className="font-mono text-4xl font-bold text-green-500">
              ${scheduler?.cumulative_savings.total_usd.toFixed(2)}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {scheduler?.cumulative_savings.vs_naive_pct.toFixed(1)}% vs naive scheduling
            </p>
            <div className="mt-6 grid w-full grid-cols-2 gap-4 border-t border-border pt-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-foreground">
                  {scheduler?.cumulative_savings.workloads_optimized}
                </p>
                <p className="text-xs text-muted-foreground">Workloads Optimized</p>
              </div>
              <div className="text-center">
                <p className="font-mono text-2xl font-bold text-foreground">
                  ${predictions?.current_price.toFixed(3)}
                </p>
                <p className="text-xs text-muted-foreground">Current Price/hr</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
