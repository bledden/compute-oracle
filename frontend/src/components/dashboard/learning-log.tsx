"use client"

import { ScrollText, AlertCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useLearningLog } from "@/hooks/use-oracle-data"
import { PanelSkeleton } from "./panel-skeleton"
import { cn } from "@/lib/utils"

export function LearningLog() {
  const { data, error, isLoading } = useLearningLog()

  return (
    <Card className="col-span-6 border-border bg-[#0a0a0a]">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-foreground">
          <ScrollText className="h-4 w-4 text-primary" />
          Learning Events
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load learning log</span>
          </div>
        ) : isLoading ? (
          <PanelSkeleton lines={5} />
        ) : (
          <ScrollArea className="h-[200px] pr-4">
            <div className="space-y-3">
              {data?.events.map((event, index) => {
                const isImprovement = event.mae_after < event.mae_before
                const isRegression = event.type === "regression"

                return (
                  <div
                    key={`${event.cycle}-${index}`}
                    className={cn(
                      "rounded-lg border p-3",
                      isRegression
                        ? "border-red-500/30 bg-red-500/5"
                        : isImprovement
                          ? "border-green-500/30 bg-green-500/5"
                          : "border-border bg-secondary/50"
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-xs">
                          #{event.cycle}
                        </Badge>
                        <Badge
                          className={cn(
                            "text-xs",
                            event.type === "edge_weight_update"
                              ? "bg-primary/10 text-primary"
                              : event.type === "node_added"
                                ? "bg-amber-500/10 text-amber-500"
                                : event.type === "edge_pruned"
                                  ? "bg-blue-500/10 text-blue-500"
                                  : "bg-red-500/10 text-red-500"
                          )}
                        >
                          {event.type.replace(/_/g, " ")}
                        </Badge>
                      </div>
                      <span
                        className={cn(
                          "font-mono text-xs",
                          isImprovement ? "text-green-400" : "text-red-400"
                        )}
                      >
                        {isImprovement ? "-" : "+"}
                        {Math.abs(event.mae_after - event.mae_before).toFixed(4)}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">{event.description}</p>
                  </div>
                )
              })}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}
