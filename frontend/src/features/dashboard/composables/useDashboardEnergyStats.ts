import { computed, reactive } from 'vue'
import { getEnergyStatistics, type EnergyStatistics } from '@/api/energy'

const ENERGY_TYPES = ['electricity', 'water', 'gas', 'heat', 'cooling'] as const

export function useDashboardEnergyStats() {
  const energyStats = reactive<Record<string, EnergyStatistics>>({})

  const todayEnergy = computed(() => energyStats.electricity?.total_consumption || 0)

  const loadEnergyStats = async () => {
    try {
      const today = new Date()
      const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

      const results = await Promise.all(
        ENERGY_TYPES.map(async (type) => {
          try {
            const stats = await getEnergyStatistics({
              energy_type: type,
              start_time: `${dateStr}T00:00:00`,
              end_time: `${dateStr}T23:59:59`
            })

            return { type, stats }
          } catch {
            return { type, stats: { total_consumption: 0, data_count: 0 } as EnergyStatistics }
          }
        })
      )

      results.forEach(({ type, stats }) => {
        energyStats[type] = stats
      })
    } catch (error) {
      console.error('加载能源统计失败:', error)
    }
  }

  return {
    energyStats,
    todayEnergy,
    loadEnergyStats
  }
}
