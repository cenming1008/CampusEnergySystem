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

export const typeColorMap: Record<string, string> = {
  electricity: '#5eead4',
  water: '#7ab8ff',
  gas: '#f7b267',
  heat: '#fb7185',
  cooling: '#b794f6',
  steam: '#a78bfa',
}

export const typeColor = (key: string) => typeColorMap[key] || '#94a3b8'

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
        color: typeColorMap[type.value] || '#94a3b8',
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
