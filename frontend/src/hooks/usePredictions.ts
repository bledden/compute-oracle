"use client";
import useSWR from "swr";
import { apiFetch } from "@/lib/api";
import { POLL_INTERVAL_PREDICTIONS } from "@/config/constants";
import type { PredictionResponse, PredictionHistoryResponse } from "@/lib/types";

export function usePredictions() {
  return useSWR<PredictionResponse>(
    "/predictions/latest",
    (url: string) => apiFetch<PredictionResponse>(url),
    { refreshInterval: POLL_INTERVAL_PREDICTIONS }
  );
}

export function usePredictionHistory(limit = 50) {
  return useSWR<PredictionHistoryResponse>(
    `/predictions/history?limit=${limit}`,
    (url: string) => apiFetch<PredictionHistoryResponse>(url),
    { refreshInterval: POLL_INTERVAL_PREDICTIONS }
  );
}
