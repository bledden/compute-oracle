"use client"

import { Clock, TrendingDown, AlertCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useScheduler } from "@/hooks/use-oracle-data"
import { PanelSkeleton } from "./panel-skeleton"

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  })
}

function formatTimeRange(start: string, end: string): string {
  return `${formatTime(start)} - ${formatTime(end)}`
}

export function SchedulerPanel() {
  const { data, error, isLoading } = useScheduler()

  return (
    <Card className="col-span-6 border-border bg-[#0a0a0a]">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-foreground">
          <Clock className="h-4 w-4 text-primary" />
          Scheduler
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load scheduler</span>
          </div>
        ) : isLoading ? (
          <PanelSkeleton lines={4} />
        ) : (
          <>
            <ScrollArea className="h-[140px] pr-4">
              <div className="space-y-2">
                {data?.windows.map((window, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg border border-border bg-secondary/30 p-3"
                  >
                    <div className="flex items-center gap-3">
                      <TrendingDown className="h-4 w-4 text-green-500" />
                      <div>
                        <p className="font-mono text-sm font-bold text-foreground">
                          ${window.predicted_avg_price.toFixed(3)}/hr
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatTimeRange(window.start, window.end)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-green-500/10 text-green-500">
                        -{window.savings_pct.toFixed(1)}%
                      </Badge>
                      <span className="font-mono text-xs text-muted-foreground">
                        {(window.confidence * 100).toFixed(0)}% conf
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Recommendation */}
            {data?.recommendation && (
              <p className="mt-4 text-sm italic text-muted-foreground">
                {data.recommendation}
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
