"use client"

import useSWR from "swr"
import { endpoints, fetcher, refreshIntervals } from "@/lib/api"
import type {
  SignalsLatestResponse,
  PredictionResponse,
  PredictionHistoryResponse,
  CausalGraphResponse,
  LearningMetricsResponse,
  LearningLogResponse,
  SchedulerResponse,
} from "@/lib/types"

export function useSignals() {
  return useSWR<SignalsLatestResponse>(
    endpoints.signals,
    fetcher,
    { refreshInterval: refreshIntervals.signals }
  )
}

export function usePredictions() {
  return useSWR<PredictionResponse>(
    endpoints.predictions,
    fetcher,
    { refreshInterval: refreshIntervals.predictions }
  )
}

export function usePredictionHistory(limit = 20) {
  return useSWR<PredictionHistoryResponse>(
    `${endpoints.predictionHistory}?limit=${limit}`,
    fetcher,
    { refreshInterval: refreshIntervals.predictions }
  )
}

export function useCausalGraph() {
  return useSWR<CausalGraphResponse>(
    endpoints.causalGraph,
    fetcher,
    { refreshInterval: refreshIntervals.causal }
  )
}

export function useLearningMetrics() {
  return useSWR<LearningMetricsResponse>(
    endpoints.learningMetrics,
    fetcher,
    { refreshInterval: refreshIntervals.learning }
  )
}

export function useLearningLog(limit = 50) {
  return useSWR<LearningLogResponse>(
    `${endpoints.learningLog}?limit=${limit}`,
    fetcher,
    { refreshInterval: refreshIntervals.learning }
  )
}

export function useScheduler() {
  return useSWR<SchedulerResponse>(
    endpoints.schedulerWindows,
    fetcher,
    { refreshInterval: refreshIntervals.predictions }
  )
}

export function useRevalidateAll() {
  const { mutate: mutateSignals } = useSignals()
  const { mutate: mutatePredictions } = usePredictions()
  const { mutate: mutatePredictionHistory } = usePredictionHistory()
  const { mutate: mutateCausalGraph } = useCausalGraph()
  const { mutate: mutateLearningMetrics } = useLearningMetrics()
  const { mutate: mutateLearningLog } = useLearningLog()
  const { mutate: mutateScheduler } = useScheduler()

  return async () => {
    await Promise.all([
      mutateSignals(),
      mutatePredictions(),
      mutatePredictionHistory(),
      mutateCausalGraph(),
      mutateLearningMetrics(),
      mutateLearningLog(),
      mutateScheduler(),
    ])
  }
}
