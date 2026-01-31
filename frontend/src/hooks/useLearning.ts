"use client";
import useSWR from "swr";
import { apiFetch } from "@/lib/api";
import { POLL_INTERVAL_LEARNING } from "@/config/constants";
import type { LearningMetricsResponse, LearningLogResponse } from "@/lib/types";

export function useLearningMetrics() {
  return useSWR<LearningMetricsResponse>(
    "/learning/metrics",
    (url: string) => apiFetch<LearningMetricsResponse>(url),
    { refreshInterval: POLL_INTERVAL_LEARNING }
  );
}

export function useLearningLog(limit = 20) {
  return useSWR<LearningLogResponse>(
    `/learning/log?limit=${limit}`,
    (url: string) => apiFetch<LearningLogResponse>(url),
    { refreshInterval: POLL_INTERVAL_LEARNING }
  );
}
