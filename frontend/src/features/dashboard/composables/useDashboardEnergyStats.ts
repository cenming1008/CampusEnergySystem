import { computed, reactive } from 'vue'
import { getEnergyStatistics, type EnergyStatistics } from '@/api/energy'

const ENERGY_TYPES = ['electricity', 'water', 'gas', 'heat', 'cooling'] as const

export function useDashboardEnergyStats() {
  const energyStats = reactive<Record<string, EnergyStatistics>>({})
  const monthlyEnergyStats = reactive<Record<string, EnergyStatistics>>({})

  const todayEnergy = computed(() => (
    ENERGY_TYPES.reduce((sum, type) => sum + (energyStats[type]?.total_consumption || 0), 0)
  ))

  const monthlyEnergy = computed(() => (
    ENERGY_TYPES.reduce((sum, type) => sum + (monthlyEnergyStats[type]?.total_consumption || 0), 0)
  ))

  const loadEnergyStats = async () => {
    try {
      const today = new Date()
      const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
      const monthStart = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-01`

      const results = await Promise.all(
        ENERGY_TYPES.map(async (type) => {
          try {
            const [stats, monthStats] = await Promise.all([
              getEnergyStatistics({
                energy_type: type,
                start_time: `${dateStr}T00:00:00`,
                end_time: `${dateStr}T23:59:59`
              }),
              getEnergyStatistics({
                energy_type: type,
                start_time: `${monthStart}T00:00:00`,
                end_time: `${dateStr}T23:59:59`
              })
            ])

            return { type, stats, monthStats }
          } catch {
            const fallback = { total_consumption: 0, data_count: 0 } as EnergyStatistics
            return { type, stats: fallback, monthStats: fallback }
          }
        })
      )

      results.forEach(({ type, stats, monthStats }) => {
        energyStats[type] = stats
        monthlyEnergyStats[type] = monthStats
      })
    } catch {
      // 能源统计加载失败
    }
  }

  return {
    energyStats,
    todayEnergy,
    monthlyEnergy,
    monthlyEnergyStats,
    loadEnergyStats
  }
}
