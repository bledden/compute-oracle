"use client";
import useSWR from "swr";
import { apiFetch } from "@/lib/api";
import { POLL_INTERVAL_PREDICTIONS } from "@/config/constants";
import type { SchedulerResponse } from "@/lib/types";

export function useScheduler() {
  return useSWR<SchedulerResponse>(
    "/scheduler/windows",
    (url: string) => apiFetch<SchedulerResponse>(url),
    { refreshInterval: POLL_INTERVAL_PREDICTIONS }
  );
}
