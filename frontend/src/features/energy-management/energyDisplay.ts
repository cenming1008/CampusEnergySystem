import type {
  AnalysisEnergyCategoryComparisonItem,
  AnalysisInsightItem,
  AnalysisTrendItem,
  CarbonSummary,
  EnergyOverview,
  EnergyStatistics,
  EnergyTypeInfo,
} from '@/api/energy'
import type { Device } from '@/api/device'

// Park EMS Design Tokens v1.0 — 介质色板。
// 这些十六进制值与 main.css 中 --token-medium-* 严格一一对应。
// 同步规则：改动这里时必须同步 main.css 的 token 段。
// 之所以保留 hex（而非 var(--token-*)）：
//   1. ECharts 配色项不解析 CSS 变量，必须传 hex/rgb 字符串。
//   2. 部分调用方做 `color + '55'` 形式的 alpha 拼接（见 EnergyManagement.vue 的 chip rail）。
// 调用方需要 token 变量时直接写 'var(--token-medium-elec)' 即可。
export const typeColorMap: Record<string, string> = {
  electricity: '#3B82F6',
  water:       '#14B8A6',
  gas:         '#F59E0B',
  heat:        '#EF4444',
  cooling:     '#06B6D4',
  steam:       '#EF4444',  // 蒸汽暂归入热色系
}

export const typeColor = (key: string) => typeColorMap[key] || '#6B7280'

export const typeCssVarMap: Record<string, string> = {
  electricity: 'var(--token-medium-elec)',
  water:       'var(--token-medium-water)',
  gas:         'var(--token-medium-gas)',
  heat:        'var(--token-medium-heat)',
  cooling:     'var(--token-medium-cool)',
  steam:       'var(--token-medium-heat)',
}
export const typeCssVar = (key: string) => typeCssVarMap[key] || 'var(--token-status-disabled)'

export function hasSteamRuntimePresence(
  statistics: Record<string, EnergyStatistics>,
  deviceList: Device[],
  carbonSummary: CarbonSummary | null,
) {
  const steamStats = statistics.steam
  const hasSteamDevice = deviceList.some((device) => device.energy_type === 'steam')
  const hasSteamStats = Boolean(
    steamStats && (
      steamStats.data_count > 0 ||
      steamStats.total_consumption > 0 ||
      steamStats.avg_flow_rate > 0 ||
      steamStats.peak_flow_rate > 0
    )
  )
  const steamCarbon = carbonSummary?.by_energy_type?.steam
  const hasSteamCarbon = Boolean(
    steamCarbon && (steamCarbon.energy_consumption > 0 || steamCarbon.carbon_emission > 0)
  )
  return hasSteamDevice || hasSteamStats || hasSteamCarbon
}

export function buildEnergyMixItems(
  visibleEnergyTypes: EnergyTypeInfo[],
  statistics: Record<string, EnergyStatistics>,
) {
  const items = visibleEnergyTypes
    .map((type) => {
      const stats = statistics[type.value]
      const value = stats?.total_consumption || 0
      return {
        key: type.value,
        label: type.label,
        unit: type.unit,
        value,
        color: typeColorMap[type.value] || '#6B7280',
      }
    })
    .filter((item) => item.value > 0)

  const total = items.reduce((sum, item) => sum + item.value, 0)
  return items.map((item) => ({
    ...item,
    percent: total > 0 ? (item.value / total) * 100 : 0,
  }))
}

export function normalizeTrendItems(overview: EnergyOverview | null): AnalysisTrendItem[] {
  const trend = overview?.trend
  if (trend?.items?.length) return trend.items
  return (trend?.points ?? []).map((point) => ({
    timestamp: point.timestamp,
    total_consumption: point.value,
    total_load: point.load ?? 0,
    energy_breakdown: {},
  }))
}

export function normalizeEnergyCategoryComparison(
  overview: EnergyOverview | null,
  energyTypes: EnergyTypeInfo[],
): AnalysisEnergyCategoryComparisonItem[] {
  const comparison = overview?.comparison
  if (comparison?.energy_categories?.length) return comparison.energy_categories
  return (comparison?.mix ?? []).map((item) => ({
    energy_category: item.energy_type,
    label: energyTypes.find((type) => type.value === item.energy_type)?.label || item.energy_type,
    total_consumption: 0,
    avg_load: 0,
    ratio: item.share,
  }))
}

export function normalizeInsightItems(overview: EnergyOverview | null): AnalysisInsightItem[] {
  return (overview?.insights ?? []).map((item) => ({
    title: item,
    detail: item,
    severity: 'info',
    dimension: 'summary',
  }))
}
