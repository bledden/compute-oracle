"use client";
import { Header } from "@/components/shared/Header";
import { SignalPanel } from "@/components/dashboard/SignalPanel";
import { CausalGraph } from "@/components/dashboard/CausalGraph";
import { PredictionTimeline } from "@/components/dashboard/PredictionTimeline";
import { AccuracyCurve } from "@/components/dashboard/AccuracyCurve";
import { SavingsTracker } from "@/components/dashboard/SavingsTracker";
import { LearningLog } from "@/components/dashboard/LearningLog";
import { SchedulerView } from "@/components/dashboard/SchedulerView";

export default function Dashboard() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 p-6">
        <div className="grid grid-cols-12 gap-4">
          {/* Top row: Signals + Savings */}
          <div className="col-span-4">
            <SignalPanel />
          </div>
          <div className="col-span-5">
            <PredictionTimeline />
          </div>
          <div className="col-span-3">
            <SavingsTracker />
          </div>

          {/* Middle row: Causal Graph + Accuracy */}
          <div className="col-span-7">
            <CausalGraph />
          </div>
          <div className="col-span-5">
            <AccuracyCurve />
          </div>

          {/* Bottom row: Learning Log + Scheduler */}
          <div className="col-span-6">
            <LearningLog />
          </div>
          <div className="col-span-6">
            <SchedulerView />
          </div>
        </div>
      </main>
    </div>
  );
}
