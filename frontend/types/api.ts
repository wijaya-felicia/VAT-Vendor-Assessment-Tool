export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: number
  email: string
  full_name?: string
}

export interface UserProfile {
  user_id: number
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
}

export interface UploadResponse {
  session_id: string
  status: number
  message: string
  row_count: number
  columns: string[]
  data_sample: Record<string, any>
}

export interface VendorStats {
  vendor_name: string
  transaction_count: number
  total_spending: number
  average_spending: number
  price_discrepancy_mean: number
  price_discrepancy_std: number
  delay_mean: number
  delay_std: number
}

export interface DashboardMetrics {
  session_id: string
  total_transactions: number
  total_spending: number
  average_transaction_value: number
  vendor_count: number
  price_discrepancy_mean: number
  price_discrepancy_std: number
  delay_mean: number
  delay_std: number
  vendors: VendorStats[]
}

export interface VendorBHMScore {
  vendor_name: string
  vendor_id?: string
  price_accuracy_score: number
  price_accuracy_ci_lower: number
  price_accuracy_ci_upper: number
  timeliness_score: number
  timeliness_ci_lower: number
  timeliness_ci_upper: number
  combined_rank_score: number
  rank: number
  transaction_count: number
}

export interface BHMRankingsResponse {
  session_id: string
  model_type: string
  convergence_status: string
  convergence_warnings: string[]
  mcmc_iterations: number
  mcmc_chains: number
  rankings: VendorBHMScore[]
  model_timestamp: string
  posterior_version?: string
}

export interface BHMDiagnostics {
  metric_name: string
  r_hat: number
  effective_sample_size: number
  has_divergences: boolean
  rhat_status: string
}

export interface BHMVendorDetailResponse {
  session_id: string
  vendor_name: string
  vendor_id?: string
  combined_rank_score: number
  rank: number
  price_accuracy_mean: number
  price_accuracy_ci_lower: number
  price_accuracy_ci_upper: number
  timeliness_mean: number
  timeliness_ci_lower: number
  timeliness_ci_upper: number
  diagnostics: BHMDiagnostics[]
  transaction_count: number
  confidence: string
}

export interface ModelLockResponse {
  status: string
  model_year: string
  locked_at: string
  vendor_count: number
  summary: string
}

export interface PriceTrendData {
  vendor_name: string
  mean: number
  min: number
  max: number
}

export interface PerformanceMatrixData {
  vendor_name: string
  price_accuracy: number
  timeliness: number
  transaction_count: number
}
