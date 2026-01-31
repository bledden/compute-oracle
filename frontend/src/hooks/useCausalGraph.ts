"use client";
import useSWR from "swr";
import { apiFetch } from "@/lib/api";
import { POLL_INTERVAL_CAUSAL } from "@/config/constants";
import type { CausalGraphResponse, FactorsResponse } from "@/lib/types";

export function useCausalGraph() {
  return useSWR<CausalGraphResponse>(
    "/causal/graph",
    (url: string) => apiFetch<CausalGraphResponse>(url),
    { refreshInterval: POLL_INTERVAL_CAUSAL }
  );
}

export function useFactors() {
  return useSWR<FactorsResponse>(
    "/causal/factors",
    (url: string) => apiFetch<FactorsResponse>(url),
    { refreshInterval: POLL_INTERVAL_CAUSAL }
  );
}
