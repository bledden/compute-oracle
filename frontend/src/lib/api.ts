export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const endpoints = {
  signals: `${API_BASE_URL}/signals/latest`,
  predictions: `${API_BASE_URL}/predictions/latest`,
  predictionHistory: `${API_BASE_URL}/predictions/history`,
  causalGraph: `${API_BASE_URL}/causal/graph`,
  learningMetrics: `${API_BASE_URL}/learning/metrics`,
  learningLog: `${API_BASE_URL}/learning/log`,
  schedulerWindows: `${API_BASE_URL}/scheduler/windows`,
  runCycle: `${API_BASE_URL}/cycle/run`,
}

export const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  return res.json()
}

export const runCycle = async () => {
  const res = await fetch(endpoints.runCycle, {
    method: "POST",
  })
  if (!res.ok) {
    throw new Error(`Failed to run cycle: ${res.status}`)
  }
  return res.json()
}

// SWR refresh intervals (in milliseconds)
export const refreshIntervals = {
  signals: 30000, // 30 seconds
  predictions: 60000, // 60 seconds
  causal: 60000, // 60 seconds
  learning: 30000, // 30 seconds
}
