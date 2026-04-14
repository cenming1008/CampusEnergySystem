import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useDashboardEnergyStats } from '../useDashboardEnergyStats'

const { getEnergyOverviewMock } = vi.hoisted(() => ({
  getEnergyOverviewMock: vi.fn(),
}))

vi.mock('@/api/energy', () => ({
  getEnergyOverview: getEnergyOverviewMock,
}))

describe('useDashboardEnergyStats', () => {
  beforeEach(() => {
    getEnergyOverviewMock.mockReset()
  })

  it('loads energy statistics for dashboard cards', async () => {
    getEnergyOverviewMock
      .mockResolvedValueOnce({
        statistics: {
          electricity: { total_consumption: 321.5, avg_consumption: 10, avg_flow_rate: 3, peak_flow_rate: 8, data_count: 24 },
          water: { total_consumption: 12, avg_consumption: 2, avg_flow_rate: 1, peak_flow_rate: 4, data_count: 12 },
        },
      })
      .mockResolvedValueOnce({
        statistics: {
          electricity: { total_consumption: 999, avg_consumption: 30, avg_flow_rate: 5, peak_flow_rate: 15, data_count: 300 },
          water: { total_consumption: 88, avg_consumption: 4, avg_flow_rate: 1.5, peak_flow_rate: 5, data_count: 80 },
        },
      })

    const state = useDashboardEnergyStats()
    await state.loadEnergyStats()

    expect(getEnergyOverviewMock).toHaveBeenCalledTimes(2)
    expect(state.energyStats.electricity.total_consumption).toBe(321.5)
    expect(state.energyStats.water.total_consumption).toBe(12)
    expect(state.todayEnergy.value).toBe(333.5)
    expect(state.monthlyEnergyStats.electricity.total_consumption).toBe(999)
  })

  it('fills zero fallback when one energy type request fails', async () => {
    getEnergyOverviewMock.mockRejectedValue(new Error('overview unavailable'))

    const state = useDashboardEnergyStats()
    await state.loadEnergyStats()

    expect(Object.keys(state.energyStats)).toHaveLength(0)
    expect(state.todayEnergy.value).toBe(0)
    expect(state.monthlyEnergy.value).toBe(0)
  })
})
