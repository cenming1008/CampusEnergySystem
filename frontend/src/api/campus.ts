import request from '@/utils/request'

export interface TimeWindow {
  start_time: string
  end_time: string
  granularity?: string
}

export interface CampusEntity {
  id: number
  name: string
  location_type: string
  code?: string | null
  full_path?: string | null
}

export interface AnalysisSummary {
  time_window: TimeWindow
  total_consumption: number
  realtime_load: number
  active_alarm_count: number
  device_count: number
  meter_count: number
  building_count: number
  estimated_carbon: number
}

export interface EnergyCategorySummaryItem {
  energy_category: string
  label: string
  total_consumption: number
  avg_load: number
  ratio: number
  estimated_carbon: number
}

export interface SubItemStatisticsItem {
  sub_item: string
  label: string
  total_consumption: number
  avg_load: number
  device_count: number
  energy_categories: string[]
}

export interface LocationRankingItem {
  location_id: number
  name: string
  location_type: string
  full_path?: string | null
  total_consumption: number
  avg_load: number
  energy_breakdown: Record<string, number>
}

export interface RealtimeLoadTrendItem {
  timestamp: string
  total_load: number
  total_consumption: number
}

export interface AlarmLatestItem {
  id: number
  device_id: number
  message: string
  severity: string
  category: string
  timestamp: string
  is_resolved: boolean
}

export interface AlarmLocationItem {
  location_id: number
  name: string
  location_type: string
  alarm_count: number
}

export interface AlarmSummary {
  time_window?: TimeWindow | null
  total_count: number
  unresolved_count: number
  resolved_count: number
  by_severity: Record<string, number>
  top_locations: AlarmLocationItem[]
  latest: AlarmLatestItem[]
}

export interface HierarchySummary {
  location_counts: Record<string, number>
  device_count: number
  active_device_count: number
  meter_count: number
}

export interface CampusOverview {
  campus_entities: CampusEntity[]
  hierarchy_summary: HierarchySummary
  analysis_summary: AnalysisSummary
  energy_category_summary: EnergyCategorySummaryItem[]
  subitem_statistics: SubItemStatisticsItem[]
  location_rankings: Record<string, LocationRankingItem[]>
  realtime_load_trend: RealtimeLoadTrendItem[]
  alarm_summary: AlarmSummary
}

export interface LocationEnergyStatisticsResponse {
  dimension: string
  time_window: TimeWindow
  items: LocationRankingItem[]
}

export interface RealtimeLoadTrendResponse {
  time_window: TimeWindow
  items: RealtimeLoadTrendItem[]
}

interface TimeRangeParams {
  start_time?: string
  end_time?: string
}

export function getCampusOverview(params: TimeRangeParams = {}) {
  return request.get<never, CampusOverview>('/campus/overview', { params })
}

export function getCampusAlarmSummary(params: TimeRangeParams = {}) {
  return request.get<never, AlarmSummary>('/campus/alarms/summary', { params })
}

export function getCampusEnergyStatistics(
  params: TimeRangeParams & { dimension?: 'area' | 'building' } = {}
) {
  return request.get<never, LocationEnergyStatisticsResponse>('/campus/energy-statistics', { params })
}

export function getCampusRealtimeLoadTrend(params: TimeRangeParams = {}) {
  return request.get<never, RealtimeLoadTrendResponse>('/campus/realtime-load-trend', { params })
}
