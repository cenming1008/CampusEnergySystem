import type { CampusOverview, LocationRankingItem } from '@/api/campus'
import type { Alarm } from '@/api/alarm'
import type { Device } from '@/api/device'
import type { DeviceIngestionHealthItem } from '@/api/deviceMonitor'

interface TrendPoint { t: string; v: number }

export type FallbackTrend = Record<string, TrendPoint[]>

const nowIso = '2026-05-14T12:00:00'

function hourlyWave(base: number, amplitude: number, offset = 0): TrendPoint[] {
  return Array.from({ length: 24 }, (_, hour) => {
    const dayCurve = Math.sin(((hour - 7) / 24) * Math.PI)
    const eveningPeak = Math.exp(-Math.pow(hour - 19, 2) / 18)
    const value = base + Math.max(0, dayCurve) * amplitude + eveningPeak * amplitude * 0.45 + offset
    return {
      t: `${String(hour).padStart(2, '0')}:00`,
      v: Math.round(value * 10) / 10,
    }
  })
}

export const FALLBACK_TREND: FallbackTrend = {
  electricity: hourlyWave(460, 360),
  cooling: hourlyWave(120, 140, 20),
  heat: hourlyWave(70, 80, 8),
  water: hourlyWave(38, 35, 4),
  gas: hourlyWave(26, 28, 2),
}

function scaleTrend(source: FallbackTrend, factor: number, offset = 0): FallbackTrend {
  return Object.fromEntries(Object.entries(source).map(([key, points]) => [
    key,
    points.map((point, index) => ({
      t: point.t,
      v: Math.max(0, Math.round((point.v * factor + Math.sin((index + offset) / 3) * 12) * 10) / 10),
    })),
  ])) as FallbackTrend
}

export const FALLBACK_TREND_BY_RANGE = {
  today: FALLBACK_TREND,
  yest: scaleTrend(FALLBACK_TREND, 0.93, 1),
  week: scaleTrend(FALLBACK_TREND, 1.08, 3),
  month: scaleTrend(FALLBACK_TREND, 0.98, 6),
}

export const FALLBACK_RANKING: LocationRankingItem[] = [
  { location_id: 1, name: 'A 座研发楼', location_type: 'building', full_path: '滨海科技园 / A 座研发楼', total_consumption: 4280, avg_load: 620, energy_breakdown: { electricity: 3560, cooling: 520, water: 200 } },
  { location_id: 2, name: 'B 座办公楼', location_type: 'building', full_path: '滨海科技园 / B 座办公楼', total_consumption: 3910, avg_load: 540, energy_breakdown: { electricity: 3180, cooling: 470, water: 260 } },
  { location_id: 3, name: '动力中心', location_type: 'building', full_path: '滨海科技园 / 动力中心', total_consumption: 3360, avg_load: 480, energy_breakdown: { electricity: 2100, cooling: 820, heat: 440 } },
  { location_id: 4, name: '综合服务楼', location_type: 'building', full_path: '滨海科技园 / 综合服务楼', total_consumption: 2620, avg_load: 360, energy_breakdown: { electricity: 1880, gas: 340, water: 400 } },
  { location_id: 5, name: '实验中试区', location_type: 'area', full_path: '滨海科技园 / 实验中试区', total_consumption: 2140, avg_load: 300, energy_breakdown: { electricity: 1740, heat: 240, water: 160 } },
  { location_id: 6, name: '停车及充电区', location_type: 'area', full_path: '滨海科技园 / 停车及充电区', total_consumption: 1680, avg_load: 220, energy_breakdown: { electricity: 1680 } },
]

export const FALLBACK_OVERVIEW: CampusOverview = {
  campus_entities: [{ id: 1, name: '滨海科技园 · 一期', location_type: 'campus', full_path: '滨海科技园 · 一期' }],
  hierarchy_summary: {
    location_counts: { campus: 1, area: 4, building: 8 },
    device_count: 128,
    active_device_count: 121,
    meter_count: 96,
  },
  analysis_summary: {
    time_window: { start_time: '2026-05-14T00:00:00', end_time: nowIso, granularity: 'day' },
    total_consumption: 17990,
    realtime_load: 1860,
    active_alarm_count: 3,
    device_count: 128,
    meter_count: 96,
    building_count: 8,
    estimated_carbon: 10850,
  },
  energy_category_summary: [
    { energy_category: 'electricity', label: '电', total_consumption: 12640, avg_load: 1320, ratio: 0.702, estimated_carbon: 8420 },
    { energy_category: 'cooling', label: '冷', total_consumption: 2460, avg_load: 260, ratio: 0.137, estimated_carbon: 1210 },
    { energy_category: 'heat', label: '热', total_consumption: 1220, avg_load: 130, ratio: 0.068, estimated_carbon: 610 },
    { energy_category: 'water', label: '水', total_consumption: 980, avg_load: 72, ratio: 0.054, estimated_carbon: 360 },
    { energy_category: 'gas', label: '气', total_consumption: 690, avg_load: 58, ratio: 0.039, estimated_carbon: 250 },
  ],
  subitem_statistics: [],
  location_rankings: {
    building: FALLBACK_RANKING,
    area: FALLBACK_RANKING.slice(2),
  },
  realtime_load_trend: FALLBACK_TREND.electricity.map((point) => ({
    timestamp: `2026-05-14T${point.t}:00`,
    total_load: point.v,
    total_consumption: point.v,
  })),
  alarm_summary: {
    total_count: 3,
    unresolved_count: 3,
    resolved_count: 0,
    by_severity: { critical: 1, warning: 2, info: 0 },
    top_locations: [{ location_id: 3, name: '动力中心', location_type: 'building', alarm_count: 2 }],
    latest: [],
  },
}

export const FALLBACK_PREVIOUS_OVERVIEW: CampusOverview = {
  ...FALLBACK_OVERVIEW,
  analysis_summary: {
    ...FALLBACK_OVERVIEW.analysis_summary,
    total_consumption: 17180,
    realtime_load: 1765,
    estimated_carbon: 10340,
  },
  energy_category_summary: FALLBACK_OVERVIEW.energy_category_summary.map((item) => ({
    ...item,
    total_consumption: Math.round(item.total_consumption * 0.955),
    avg_load: Math.round(item.avg_load * 0.95),
    estimated_carbon: Math.round(item.estimated_carbon * 0.953),
  })),
  location_rankings: {
    building: FALLBACK_RANKING.map((item) => ({
      ...item,
      total_consumption: Math.round(item.total_consumption * 0.94),
      avg_load: Math.round(item.avg_load * 0.95),
    })),
    area: FALLBACK_RANKING.slice(2).map((item) => ({
      ...item,
      total_consumption: Math.round(item.total_consumption * 0.94),
      avg_load: Math.round(item.avg_load * 0.95),
    })),
  },
  realtime_load_trend: FALLBACK_TREND_BY_RANGE.yest.electricity.map((point) => ({
    timestamp: `2026-05-13T${point.t}:00`,
    total_load: point.v,
    total_consumption: point.v,
  })),
}

export const FALLBACK_INGESTION_HEALTH: DeviceIngestionHealthItem[] = [
  { device_id: 101, status: 'online', is_online: true, last_success_at: nowIso, consecutive_failures: 0, total_messages: 1440, total_failures: 0, success_rate: 1 },
  { device_id: 102, status: 'online', is_online: true, last_success_at: nowIso, consecutive_failures: 0, total_messages: 1432, total_failures: 2, success_rate: 0.998 },
  { device_id: 103, status: 'degraded', is_online: true, last_success_at: nowIso, consecutive_failures: 1, total_messages: 1320, total_failures: 18, success_rate: 0.986 },
  { device_id: 104, status: 'online', is_online: true, last_success_at: nowIso, consecutive_failures: 0, total_messages: 1428, total_failures: 1, success_rate: 0.999 },
]

export const FALLBACK_DEVICES: Device[] = [
  {
    id: 900101,
    name: '总进线智能电表',
    sn: 'DEMO-ELEC-001',
    device_type: 'load',
    device_category: 'load',
    energy_type: 'electricity',
    unit: 'kW',
    location: 'A 座配电室',
    is_active: true,
  },
  {
    id: 900102,
    name: 'A 座分项电表',
    sn: 'DEMO-ELEC-002',
    device_type: 'load',
    device_category: 'load',
    energy_type: 'electricity',
    unit: 'kW',
    location: 'A 座研发楼',
    is_active: true,
  },
  {
    id: 900103,
    name: '屋顶光伏逆变器',
    sn: 'DEMO-PV-001',
    device_type: 'pv',
    device_category: 'solar',
    energy_type: 'electricity',
    unit: 'kW',
    location: '综合楼屋面',
    is_active: true,
  },
  {
    id: 900104,
    name: '储能柜 1 号',
    sn: 'DEMO-ESS-001',
    device_type: 'storage',
    device_category: 'storage',
    energy_type: 'electricity',
    unit: 'kWh',
    location: '动力中心',
    is_active: true,
  },
  {
    id: 900105,
    name: '冷站冷量表',
    sn: 'DEMO-COOL-001',
    device_type: 'cooling_meter',
    device_category: 'cooling_meter',
    energy_type: 'cooling',
    unit: 'kW',
    location: '动力中心冷站',
    is_active: true,
  },
  {
    id: 900106,
    name: '换热站热量表',
    sn: 'DEMO-HEAT-001',
    device_type: 'heat_meter',
    device_category: 'heat_meter',
    energy_type: 'heat',
    unit: 'kW',
    location: '换热站',
    is_active: true,
  },
  {
    id: 900107,
    name: '园区给水总表',
    sn: 'DEMO-WATER-001',
    device_type: 'water_meter',
    device_category: 'water_meter',
    energy_type: 'water',
    unit: 'm³/h',
    location: '市政接入口',
    is_active: true,
  },
  {
    id: 900108,
    name: '燃气总表',
    sn: 'DEMO-GAS-001',
    device_type: 'gas_meter',
    device_category: 'gas_meter',
    energy_type: 'gas',
    unit: 'm³/h',
    location: '动力中心',
    is_active: true,
  },
]

export const FALLBACK_ALERTS: Alarm[] = [
  { id: 9001, device_id: 103, message: '燃气总表采集延迟超过 10 分钟', severity: 'warning', category: '采集健康', source: '动力中心', timestamp: nowIso, is_resolved: false },
  { id: 9002, device_id: 102, message: '冷站瞬时负荷高于计划曲线', severity: 'critical', category: '负荷异常', source: '动力中心', timestamp: nowIso, is_resolved: false },
  { id: 9003, device_id: 101, message: 'A 座研发楼尖峰负荷接近阈值', severity: 'warning', category: '用能预警', source: 'A 座研发楼', timestamp: nowIso, is_resolved: false },
]
