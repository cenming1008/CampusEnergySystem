import { describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { useStorageEms } from '../useStorageEms'
import type {
  StorageDispatchGenerationResult,
  StorageEnergyOverview,
  StorageStrategyComparisonResult,
} from '@/api/storageEnergy'

const {
  getStorageEnergyOverviewMock,
  getStorageStrategyComparisonMock,
  generateStorageDispatchPlanMock,
} = vi.hoisted(() => ({
  getStorageEnergyOverviewMock: vi.fn(),
  getStorageStrategyComparisonMock: vi.fn(),
  generateStorageDispatchPlanMock: vi.fn(),
}))

vi.mock('@/api/storageEnergy', () => ({
  getStorageEnergyOverview: getStorageEnergyOverviewMock,
  getStorageStrategyComparison: getStorageStrategyComparisonMock,
  generateStorageDispatchPlan: generateStorageDispatchPlanMock,
}))

const overview = {
  storage_device_ids: [7],
} as StorageEnergyOverview

function comparison(scenarioKey: 'sunny_workday' | 'pv_surplus', seed: number) {
  return {
    scenario_key: scenarioKey,
    seed,
    initial_soc: 50,
  } as StorageStrategyComparisonResult
}

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((done) => { resolve = done })
  return { promise, resolve }
}

describe('useStorageEms', () => {
  it('retains HTTP 200 optimizer failure and does not refresh the old plan', async () => {
    const failed = {
      status: 'failed',
      solver_status: 'Infeasible',
      dispatch_date: '2026-07-17',
      plans: [],
      failure_reason: 'SOC 约束不可行',
    } satisfies StorageDispatchGenerationResult
    generateStorageDispatchPlanMock.mockResolvedValueOnce(failed)
    getStorageEnergyOverviewMock.mockClear()
    const state = useStorageEms()

    await state.generatePlan(7)

    expect(state.generationResult.value).toEqual(failed)
    expect(state.generationError.value).toContain('SOC 约束不可行')
    expect(state.error.value).toContain('SOC 约束不可行')
    expect(getStorageEnergyOverviewMock).not.toHaveBeenCalled()
    expect(state.generationLoading.value).toBe(false)
  })

  it('preserves overview failure when a comparison later succeeds', async () => {
    getStorageEnergyOverviewMock.mockRejectedValueOnce(new Error('总览不可用'))
    getStorageStrategyComparisonMock.mockResolvedValueOnce(comparison('sunny_workday', 20260716))
    const state = useStorageEms()

    expect(await state.refresh()).toBe(false)
    await state.compareStrategies()

    expect(state.overviewError.value).toBe('总览不可用')
    expect(state.comparisonError.value).toBeNull()
    expect(state.error.value).toBe('总览不可用')
  })

  it('ignores a delayed superseded comparison response', async () => {
    const first = deferred<StorageStrategyComparisonResult>()
    const second = deferred<StorageStrategyComparisonResult>()
    getStorageStrategyComparisonMock
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise)
    const state = useStorageEms()
    state.overview.value = overview

    const firstRequest = state.compareStrategies()
    expect(state.comparison.value).toBeNull()
    expect(state.comparisonLoading.value).toBe(true)

    state.scenario.value = 'pv_surplus'
    state.seed.value = 20260718
    const secondRequest = state.compareStrategies()
    second.resolve(comparison('pv_surplus', 20260718))
    await secondRequest
    await nextTick()
    expect(state.comparison.value?.scenario_key).toBe('pv_surplus')

    first.resolve(comparison('sunny_workday', 20260716))
    await firstRequest
    expect(state.comparison.value?.scenario_key).toBe('pv_surplus')
    expect(state.comparison.value?.seed).toBe(20260718)
    expect(state.comparisonLoading.value).toBe(false)
  })
})
