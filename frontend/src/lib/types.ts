export interface Signal {
  source: string
  name: string
  value: number
  unit: string
  timestamp: string
  change_pct: number | null
}

export interface SignalsLatestResponse {
  signals: Signal[]
}

export interface Prediction {
  horizon: string
  predicted_price: number
  direction: "up" | "down" | "flat"
  confidence: number
}

export interface ContributingFactor {
  factor: string
  contribution: number
  direction: string
}

export interface PredictionResponse {
  prediction_id: string
  cycle: number
  timestamp: string
  target: string
  current_price: number
  predictions: Prediction[]
  contributing_factors: ContributingFactor[]
  causal_explanation: string
}

export interface PredictionHistoryItem {
  prediction_id: string
  cycle: number
  timestamp: string
  predicted_price_1h: number
  actual_price_1h: number | null
  error_1h: number | null
  direction_correct: boolean | null
}

export interface PredictionHistoryResponse {
  predictions: PredictionHistoryItem[]
}

export interface CausalNode {
  id: string
  label: string
  type: "signal" | "derived" | "target"
}

export interface CausalEdge {
  from: string
  to: string
  weight: number
  direction: string
  confidence: number
}

export interface CausalGraphResponse {
  nodes: CausalNode[]
  edges: CausalEdge[]
  metadata: {
    version: number
    total_nodes: number
    total_edges: number
    last_updated: string
  }
}

export interface LastImprovement {
  cycle: number
  change: string
  mae_delta: number
}

export interface LearningMetricsResponse {
  total_cycles: number
  overall_mae: number
  directional_accuracy: number
  mae_history: number[]
  directional_accuracy_history: number[]
  graph_versions: number
  last_improvement: LastImprovement | null
}

export interface LearningEvent {
  cycle: number
  timestamp: string
  type: string
  description: string
  mae_before: number
  mae_after: number
}

export interface LearningLogResponse {
  events: LearningEvent[]
}

export interface SchedulerWindow {
  start: string
  end: string
  predicted_avg_price: number
  savings_pct: number
  confidence: number
}

export interface CumulativeSavings {
  total_usd: number
  vs_naive_pct: number
  workloads_optimized: number
}

export interface SchedulerResponse {
  current_price: number
  windows: SchedulerWindow[]
  recommendation: string
  cumulative_savings: CumulativeSavings
}
