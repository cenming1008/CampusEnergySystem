import type { Device } from '@/api/device'
import type { CarbonFactor, CarbonSummary, EnergyOverview, EnergyStatistics, EnergyTypeInfo } from '@/api/energy'

export const FALLBACK_ENERGY_TYPES: EnergyTypeInfo[] = [
  { value: 'electricity', label: '电', unit: 'kWh', flow_unit: 'kW' },
  { value: 'cooling', label: '冷', unit: 'kWh', flow_unit: 'kW' },
  { value: 'heat', label: '热', unit: 'kWh', flow_unit: 'kW' },
  { value: 'water', label: '水', unit: 'm³', flow_unit: 'm³/h' },
  { value: 'gas', label: '气', unit: 'm³', flow_unit: 'm³/h' },
]

export const FALLBACK_ENERGY_DEVICES: Device[] = [
  { id: 910101, name: '总进线智能电表', sn: 'ENERGY-DEMO-E-001', device_type: 'load', device_category: 'load', energy_type: 'electricity', unit: 'kW', location: 'A 座配电室', is_active: true },
  { id: 910102, name: '冷站冷量表', sn: 'ENERGY-DEMO-C-001', device_type: 'cooling_meter', device_category: 'cooling_meter', energy_type: 'cooling', unit: 'kW', location: '动力中心冷站', is_active: true },
  { id: 910103, name: '换热站热量表', sn: 'ENERGY-DEMO-H-001', device_type: 'heat_meter', device_category: 'heat_meter', energy_type: 'heat', unit: 'kW', location: '换热站', is_active: true },
  { id: 910104, name: '园区给水总表', sn: 'ENERGY-DEMO-W-001', device_type: 'water_meter', device_category: 'water_meter', energy_type: 'water', unit: 'm³/h', location: '市政接入口', is_active: true },
  { id: 910105, name: '燃气总表', sn: 'ENERGY-DEMO-G-001', device_type: 'gas_meter', device_category: 'gas_meter', energy_type: 'gas', unit: 'm³/h', location: '动力中心', is_active: true },
]

export const FALLBACK_CARBON_FACTORS: Record<string, CarbonFactor> = {
  electricity: { factor: 0.5703, unit: 'kgCO₂/kWh', scope: 2 },
  cooling: { factor: 0.18, unit: 'kgCO₂/kWh', scope: 2 },
  heat: { factor: 0.22, unit: 'kgCO₂/kWh', scope: 2 },
  water: { factor: 0.91, unit: 'kgCO₂/m³', scope: 3 },
  gas: { factor: 2.15, unit: 'kgCO₂/m³', scope: 1 },
}

export const FALLBACK_ENERGY_STATISTICS: Record<string, EnergyStatistics> = {
  electricity: { total_consumption: 12640, avg_consumption: 1805.7, avg_flow_rate: 1320, peak_flow_rate: 1860, data_count: 24, consumption_unit: 'kWh', flow_unit: 'kW' },
  cooling: { total_consumption: 2460, avg_consumption: 351.4, avg_flow_rate: 260, peak_flow_rate: 410, data_count: 24, consumption_unit: 'kWh', flow_unit: 'kW' },
  heat: { total_consumption: 1220, avg_consumption: 174.3, avg_flow_rate: 130, peak_flow_rate: 230, data_count: 24, consumption_unit: 'kWh', flow_unit: 'kW' },
  water: { total_consumption: 980, avg_consumption: 140, avg_flow_rate: 72, peak_flow_rate: 118, data_count: 24, consumption_unit: 'm³', flow_unit: 'm³/h' },
  gas: { total_consumption: 690, avg_consumption: 98.6, avg_flow_rate: 58, peak_flow_rate: 96, data_count: 24, consumption_unit: 'm³', flow_unit: 'm³/h' },
}

export const FALLBACK_ENERGY_CARBON_SUMMARY: CarbonSummary = {
  total_carbon: 10850,
  boundary: '园区演示边界',
  calculation_method: '演示估算',
  is_accounting_grade: false,
  note: '当前为前端演示占位数据',
  summary_basis: 'demo_fallback',
  by_energy_type: {
    electricity: { carbon_emission: 8420, energy_consumption: 12640, unit: 'kWh' },
    cooling: { carbon_emission: 1210, energy_consumption: 2460, unit: 'kWh' },
    heat: { carbon_emission: 610, energy_consumption: 1220, unit: 'kWh' },
    water: { carbon_emission: 360, energy_consumption: 980, unit: 'm³' },
    gas: { carbon_emission: 250, energy_consumption: 690, unit: 'm³' },
  },
}

const trendItems = Array.from({ length: 7 }, (_, index) => {
  const day = 8 + index
  const total = 1850 + index * 130 + Math.round(Math.sin(index / 2) * 120)
  return {
    timestamp: `2026-05-${String(day).padStart(2, '0')}T00:00:00`,
    total_consumption: total,
    total_load: 980 + index * 80,
    energy_breakdown: {
      electricity: Math.round(total * 0.7),
      cooling: Math.round(total * 0.14),
      heat: Math.round(total * 0.07),
      water: Math.round(total * 0.05),
      gas: Math.round(total * 0.04),
    },
  }
})

export const FALLBACK_ENERGY_OVERVIEW: EnergyOverview = {
  statistics: FALLBACK_ENERGY_STATISTICS,
  carbon_summary: FALLBACK_ENERGY_CARBON_SUMMARY,
  overview_boundary: 'demo_fallback',
  unit_rule: '按能源介质分项展示',
  cross_energy_mix_allowed: false,
  field_boundary_rule: '演示占位，不写入真实数据',
  energy_profiles: {},
  time_window: { start_time: '2026-05-08T00:00:00', end_time: '2026-05-14T23:59:59', granularity: 'day' },
  scope: { location_id: null, location_type: null, location_counts: { campus: 1, building: 4 }, campus_entity_count: 1, energy_categories: ['electricity', 'cooling', 'heat', 'water', 'gas'], sub_items: ['照明插座', '空调冷站', '动力设备'] },
  summary: { total_consumption: 17990, avg_load: 1151, device_count: 5, active_device_count: 5, covered_energy_type_count: 5, covered_sub_item_count: 3, anomaly_count: 2, consumption_stat_basis: 'period_delta_from_cumulative_reading' },
  trend: { granularity: 'day', items: trendItems, peak_load: trendItems[6], peak_consumption: trendItems[6], consumption_stat_basis: 'period_delta_from_cumulative_reading' },
  comparison: {
    period_over_period: { current_total_consumption: 17990, previous_total_consumption: 17180, delta_consumption: 810, change_rate: 0.047, consumption_stat_basis: 'period_delta_from_cumulative_reading' },
    energy_categories: [
      { energy_category: 'electricity', label: '电', total_consumption: 12640, avg_load: 1320, ratio: 0.702 },
      { energy_category: 'cooling', label: '冷', total_consumption: 2460, avg_load: 260, ratio: 0.137 },
      { energy_category: 'heat', label: '热', total_consumption: 1220, avg_load: 130, ratio: 0.068 },
      { energy_category: 'water', label: '水', total_consumption: 980, avg_load: 72, ratio: 0.054 },
      { energy_category: 'gas', label: '气', total_consumption: 690, avg_load: 58, ratio: 0.039 },
    ],
    sub_items: [],
  },
  ranking: {
    areas: [
      { location_id: 1, name: '动力中心', location_type: 'building', full_path: '滨海科技园 / 动力中心', total_consumption: 3360, avg_load: 480, energy_breakdown: { electricity: 2100, cooling: 820, heat: 440 } },
      { location_id: 2, name: '综合服务楼', location_type: 'building', full_path: '滨海科技园 / 综合服务楼', total_consumption: 2620, avg_load: 360, energy_breakdown: { electricity: 1880, gas: 340, water: 400 } },
    ],
    buildings: [],
    devices: [
      { device_id: 910101, name: '总进线智能电表', device_type: 'load', device_category: 'load', energy_type: 'electricity', location: 'A 座配电室', total_consumption: 6200, avg_load: 860 },
      { device_id: 910102, name: '冷站冷量表', device_type: 'cooling_meter', device_category: 'cooling_meter', energy_type: 'cooling', location: '动力中心冷站', total_consumption: 2460, avg_load: 260 },
    ],
  },
  anomaly: { boundary: 'demo_fallback', summary: { total_count: 2, data_gap_count: 0, ingestion_failure_count: 1, active_alarm_count: 1 }, items: [] },
  insights: ['电力负荷在白天办公时段抬升明显', '冷站负荷与室外温度相关性较高'],
}
