// Signal types
export type SignalSourceType =
  | "aws_spot"
  | "eia_electricity"
  | "weather"
  | "gpu_pricing"
  | "news";

export interface Signal {
  source: SignalSourceType;
  name: string;
  value: number;
  unit: string;
  timestamp: string;
  change_pct: number | null;
}

export interface SignalsLatestResponse {
  timestamp: string;
  signals: Signal[];
}

export interface DataPoint {
  timestamp: string;
  value: number;
}

export interface SignalHistoryResponse {
  source: SignalSourceType;
  name: string;
  data_points: DataPoint[];
}

export interface SourceStatus {
  id: string;
  name: string;
  status: "active" | "inactive" | "error";
  last_update: string | null;
}

export interface SourcesResponse {
  sources: SourceStatus[];
}

// Prediction types
export interface HorizonPrediction {
  horizon: string;
  predicted_price: number;
  direction: "up" | "down" | "flat";
  confidence: number;
}

export interface ContributingFactor {
  factor: string;
  contribution: number;
  direction: "bullish" | "bearish" | "neutral";
}

export interface PredictionResponse {
  prediction_id: string;
  cycle: number;
  timestamp: string;
  target: string;
  current_price: number;
  predictions: HorizonPrediction[];
  causal_explanation: string;
  contributing_factors: ContributingFactor[];
}

export interface PredictionHistoryItem {
  prediction_id: string;
  cycle: number;
  timestamp: string;
  predicted_price_1h: number;
  actual_price_1h: number | null;
  error_1h: number | null;
  direction_correct: boolean | null;
}

export interface PredictionHistoryResponse {
  predictions: PredictionHistoryItem[];
}

// Causal graph types
export interface CausalNode {
  id: string;
  label: string;
  type: "signal" | "target" | "derived";
  source: string;
}

export interface CausalEdge {
  from: string;
  to: string;
  weight: number;
  confidence: number;
  direction: "positive" | "negative";
  last_updated: string;
}

export interface GraphMetadata {
  total_nodes: number;
  total_edges: number;
  last_updated: string;
  version: number;
}

export interface CausalGraphResponse {
  nodes: CausalNode[];
  edges: CausalEdge[];
  metadata: GraphMetadata;
}

export interface FactorDetail {
  id: string;
  current_weight: number;
  weight_history: number[];
  contribution_rank: number;
  direction: string;
}

export interface FactorsResponse {
  factors: FactorDetail[];
}

// Learning types
export interface LastImprovement {
  cycle: number;
  change: string;
  mae_delta: number;
}

export interface LearningMetricsResponse {
  total_cycles: number;
  overall_mae: number;
  directional_accuracy: number;
  mae_history: number[];
  directional_accuracy_history: number[];
  graph_versions: number;
  last_improvement: LastImprovement | null;
}

export interface LearningEvent {
  cycle: number;
  timestamp: string;
  type: string;
  description: string;
  mae_before: number | null;
  mae_after: number | null;
}

export interface LearningLogResponse {
  events: LearningEvent[];
}

// Scheduler types
export interface PriceWindow {
  start: string;
  end: string;
  predicted_avg_price: number;
  savings_pct: number;
  confidence: number;
}

export interface CumulativeSavings {
  total_usd: number;
  vs_naive_pct: number;
  workloads_optimized: number;
}

export interface SchedulerResponse {
  current_price: number;
  windows: PriceWindow[];
  recommendation: string;
  cumulative_savings: CumulativeSavings;
}

// Health
export interface HealthResponse {
  status: string;
  redis: string;
}
