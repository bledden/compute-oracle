"use client"

import { DashboardHeader } from "@/components/dashboard/header"
import { SignalPanel } from "@/components/dashboard/signal-panel"
import { PredictionPanel } from "@/components/dashboard/prediction-panel"
import { SavingsTracker } from "@/components/dashboard/savings-tracker"
import { CausalGraph } from "@/components/dashboard/causal-graph"
import { LearningCurve } from "@/components/dashboard/learning-curve"
import { LearningLog } from "@/components/dashboard/learning-log"
import { SchedulerPanel } from "@/components/dashboard/scheduler-panel"

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <DashboardHeader />
      <main className="p-6">
        <div className="grid grid-cols-12 gap-4">
          {/* Row 1 */}
          <SignalPanel />
          <PredictionPanel />
          <SavingsTracker />

          {/* Row 2 */}
          <CausalGraph />
          <LearningCurve />

          {/* Row 3 */}
          <LearningLog />
          <SchedulerPanel />
        </div>
      </main>
    </div>
  )
}
