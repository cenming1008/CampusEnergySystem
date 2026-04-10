import { computed, reactive } from 'vue'
import { getEnergyOverview, type EnergyStatistics } from '@/api/energy'

export function useDashboardEnergyStats() {
  const energyStats = reactive<Record<string, EnergyStatistics>>({})
  const monthlyEnergyStats = reactive<Record<string, EnergyStatistics>>({})

  const todayEnergy = computed(() =>
    Object.values(energyStats).reduce((sum, s) => sum + (s?.total_consumption || 0), 0)
  )

  const monthlyEnergy = computed(() =>
    Object.values(monthlyEnergyStats).reduce((sum, s) => sum + (s?.total_consumption || 0), 0)
  )

  const loadEnergyStats = async () => {
    try {
      const today = new Date()
      const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
      const monthStart = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-01`

      const [todayOverview, monthOverview] = await Promise.all([
        getEnergyOverview({ start_time: `${dateStr}T00:00:00`, end_time: `${dateStr}T23:59:59` }),
        getEnergyOverview({ start_time: `${monthStart}T00:00:00`, end_time: `${dateStr}T23:59:59` })
      ])

      Object.assign(energyStats, todayOverview.statistics)
      Object.assign(monthlyEnergyStats, monthOverview.statistics)
    } catch {
      // 能源统计加载失败，保持初始空值
    }
  }

  return { energyStats, todayEnergy, monthlyEnergy, monthlyEnergyStats, loadEnergyStats }
}
