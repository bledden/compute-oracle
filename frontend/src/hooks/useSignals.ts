"use client";
import useSWR from "swr";
import { apiFetch } from "@/lib/api";
import { POLL_INTERVAL_SIGNALS } from "@/config/constants";
import type { SignalsLatestResponse, SignalHistoryResponse } from "@/lib/types";

export function useSignals() {
  return useSWR<SignalsLatestResponse>(
    "/signals/latest",
    (url: string) => apiFetch<SignalsLatestResponse>(url),
    { refreshInterval: POLL_INTERVAL_SIGNALS }
  );
}

export function useSignalHistory(source: string, name: string, hours = 168) {
  return useSWR<SignalHistoryResponse>(
    `/signals/history?source=${source}&name=${name}&hours=${hours}`,
    (url: string) => apiFetch<SignalHistoryResponse>(url),
    { refreshInterval: POLL_INTERVAL_SIGNALS }
  );
}
