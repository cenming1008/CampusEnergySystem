import request from '@/utils/request'

export interface AnalysisOverviewParams {
  start_time?: string
  end_time?: string
  location_id?: number
  energy_type?: string
  top_n?: number
}

export interface AnalysisTimeWindow {
  start_time: string
  end_time: string
  granularity: string
}

export interface AnalysisScope {
  location_id: number | null
  location_type: string | null
  location_counts: Record<string, number>
  campus_entity_count: number
  energy_categories: string[]
  sub_items: string[]
}

export interface AnalysisSummary {
  total_consumption: number
  avg_load: number
  device_count: number
  active_device_count: number
  covered_energy_type_count: number
  covered_sub_item_count: number
  anomaly_count: number
  consumption_stat_basis: string
}

export interface AnalysisTrendItem {
  timestamp: string
  total_consumption: number
  total_load: number
  energy_breakdown: Record<string, number>
}

export interface AnalysisTrend {
  items: AnalysisTrendItem[]
  peak_load: AnalysisTrendItem | null
  peak_consumption: AnalysisTrendItem | null
  consumption_stat_basis: string
}

export interface AnalysisComparisonPeriod {
  current_total_consumption: number
  previous_total_consumption: number
  delta_consumption: number
  change_rate: number | null
  consumption_stat_basis: string
}

export interface AnalysisEnergyCategoryComparisonItem {
  energy_category: string
  label: string
  total_consumption: number
  avg_load: number
  ratio: number
}

export interface AnalysisSubItemComparisonItem {
  sub_item: string
  label: string
  total_consumption: number
  avg_load: number
  device_count: number
  energy_categories: string[]
}

export interface AnalysisComparison {
  period_over_period: AnalysisComparisonPeriod
  energy_categories: AnalysisEnergyCategoryComparisonItem[]
  sub_items: AnalysisSubItemComparisonItem[]
}

export interface AnalysisLocationRankingItem {
  location_id: number
  name: string
  location_type: string
  full_path: string | null
  total_consumption: number
  avg_load: number
  energy_breakdown: Record<string, number>
}

export interface AnalysisDeviceRankingItem {
  device_id: number
  name: string
  device_type: string
  device_category: string
  energy_type: string
  location: string | null
  total_consumption: number
  avg_load: number
}

export interface AnalysisRanking {
  areas: AnalysisLocationRankingItem[]
  buildings: AnalysisLocationRankingItem[]
  devices: AnalysisDeviceRankingItem[]
}

export interface AnalysisAnomalySummary {
  total_count: number
  data_gap_count: number
  ingestion_failure_count: number
  active_alarm_count: number
}

export interface AnalysisAnomalyItem {
  kind: string
  severity: string
  device_id: number
  device_name: string
  device_type: string
  energy_type: string
  location: string | null
  message: string
  detected_at: string | null
}

export interface AnalysisAnomaly {
  boundary: string
  summary: AnalysisAnomalySummary
  items: AnalysisAnomalyItem[]
}

export interface AnalysisInsightItem {
  title: string
  detail: string
  severity: string
  dimension: string
}

export interface AnalysisOverview {
  time_window: AnalysisTimeWindow
  scope: AnalysisScope
  summary: AnalysisSummary
  trend: AnalysisTrend
  comparison: AnalysisComparison
  ranking: AnalysisRanking
  anomaly: AnalysisAnomaly
  insights: AnalysisInsightItem[]
}

export function getAnalysisOverview(params?: AnalysisOverviewParams) {
  return request.get<never, AnalysisOverview>('/analysis/overview', { params })
}
