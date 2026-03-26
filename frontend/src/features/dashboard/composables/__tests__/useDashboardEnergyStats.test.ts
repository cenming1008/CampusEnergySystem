import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useDashboardEnergyStats } from '../useDashboardEnergyStats'

const { getEnergyStatisticsMock } = vi.hoisted(() => ({
  getEnergyStatisticsMock: vi.fn(),
}))

vi.mock('@/api/energy', () => ({
  getEnergyStatistics: getEnergyStatisticsMock,
}))

describe('useDashboardEnergyStats', () => {
  beforeEach(() => {
    getEnergyStatisticsMock.mockReset()
  })

  it('loads energy statistics for dashboard cards', async () => {
    getEnergyStatisticsMock.mockImplementation(async ({ energy_type }: { energy_type: string }) => ({
      total_consumption: energy_type === 'electricity' ? 321.5 : 12,
      avg_consumption: 10,
      avg_flow_rate: 3,
      peak_flow_rate: 8,
      data_count: 24,
    }))

    const state = useDashboardEnergyStats()
    await state.loadEnergyStats()

    expect(getEnergyStatisticsMock).toHaveBeenCalledTimes(5)
    expect(state.energyStats.electricity.total_consumption).toBe(321.5)
    expect(state.energyStats.water.total_consumption).toBe(12)
    expect(state.todayEnergy.value).toBe(321.5)
  })

  it('fills zero fallback when one energy type request fails', async () => {
    getEnergyStatisticsMock.mockImplementation(async ({ energy_type }: { energy_type: string }) => {
      if (energy_type === 'gas') {
        throw new Error('gas unavailable')
      }
      return {
        total_consumption: 20,
        avg_consumption: 5,
        avg_flow_rate: 2,
        peak_flow_rate: 7,
        data_count: 10,
      }
    })

    const state = useDashboardEnergyStats()
    await state.loadEnergyStats()

    expect(state.energyStats.gas.total_consumption).toBe(0)
    expect(state.energyStats.gas.data_count).toBe(0)
    expect(state.energyStats.electricity.total_consumption).toBe(20)
  })
})
