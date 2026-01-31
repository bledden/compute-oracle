"use client"

import { Zap, TrendingUp, TrendingDown, AlertCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useSignals } from "@/hooks/use-oracle-data"
import { PanelSkeleton } from "./panel-skeleton"
import { cn } from "@/lib/utils"

export function SignalPanel() {
  const { data, error, isLoading } = useSignals()

  return (
    <Card className="col-span-4 border-border bg-[#0a0a0a]">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-foreground">
          <Zap className="h-4 w-4 text-primary" />
          Live Signals
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load signals</span>
          </div>
        ) : isLoading ? (
          <PanelSkeleton lines={6} />
        ) : (
          <ScrollArea className="h-[320px] pr-4">
            <div className="space-y-3">
              {data?.signals.map((signal, index) => (
                <div
                  key={`${signal.source}-${signal.name}-${index}`}
                  className="rounded-lg border border-border bg-secondary/50 p-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-foreground">
                        {signal.name}
                      </p>
                      <Badge variant="outline" className="mt-1 text-xs text-muted-foreground">
                        {signal.source}
                      </Badge>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-sm font-bold text-foreground">
                        {formatValue(signal.value, signal.unit)}
                      </p>
                      {signal.change_pct !== null && (
                        <div
                          className={cn(
                            "mt-1 flex items-center justify-end gap-1 text-xs",
                            signal.change_pct >= 0 ? "text-red-400" : "text-green-400"
                          )}
                        >
                          {signal.change_pct >= 0 ? (
                            <TrendingUp className="h-3 w-3" />
                          ) : (
                            <TrendingDown className="h-3 w-3" />
                          )}
                          <span className="font-mono">
                            {signal.change_pct >= 0 ? "+" : ""}
                            {signal.change_pct.toFixed(1)}%
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}

function formatValue(value: number, unit: string): string {
  if (unit === "USD/hr") {
    return `$${value.toFixed(3)} ${unit}`
  }
  if (unit === "MW") {
    return `${value.toLocaleString()} ${unit}`
  }
  if (unit === "°F") {
    return `${value}${unit}`
  }
  return `${value} ${unit}`
}
