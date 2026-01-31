"use client"

import { useState } from "react"
import { Activity, Play, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { runCycle } from "@/lib/api"
import { useRevalidateAll, useLearningMetrics } from "@/hooks/use-oracle-data"

export function DashboardHeader() {
  const [isRunning, setIsRunning] = useState(false)
  const revalidateAll = useRevalidateAll()
  const { data: metrics } = useLearningMetrics()

  const handleRunCycle = async () => {
    setIsRunning(true)
    try {
      await runCycle()
      await revalidateAll()
    } catch (error) {
      console.error("[v0] Failed to run cycle:", error)
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-[#0a0a0a]/95 backdrop-blur supports-[backdrop-filter]:bg-[#0a0a0a]/80">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="relative">
              <Activity className="h-6 w-6 text-primary" />
              <span className="absolute -right-0.5 -top-0.5 h-2 w-2 animate-pulse rounded-full bg-green-500" />
            </div>
            <h1 className="text-xl font-semibold text-foreground">Compute Oracle</h1>
          </div>
          <Badge variant="secondary" className="font-mono text-xs">
            v0.1.0
          </Badge>
        </div>

        <div className="flex items-center gap-4">
          <Button
            onClick={handleRunCycle}
            disabled={isRunning}
            className="bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            {isRunning ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            Run Cycle
          </Button>
          {metrics && (
            <Badge variant="outline" className="font-mono">
              {metrics.total_cycles} cycles
            </Badge>
          )}
          <Badge className="bg-amber-500/10 text-amber-500 border-amber-500/20">
            WeaveHacks 3
          </Badge>
        </div>
      </div>
    </header>
  )
}
