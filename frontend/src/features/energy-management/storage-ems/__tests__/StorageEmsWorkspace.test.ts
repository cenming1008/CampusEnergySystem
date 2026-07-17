import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import StorageEmsWorkspace from '../StorageEmsWorkspace.vue'

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

const overviewFixture = {
  current: {
    load_kw: 420,
    pv_kw: 186.5,
    grid_kw: 113.5,
    storage_kw: 120,
    soc: 61.5,
  },
  storage_device_ids: [7],
  data_source: 'simulated',
  simulation_run_id: 'run-20260717',
  plan_execution_rate: 87.5,
  dispatch: {
    actual_power_kw: 120,
    target_power_kw: 135,
    deviation_kw: -15,
    strategy: 'day_ahead',
    plan_status: 'fallback',
    solver_status: 'fallback',
    fallback_reason: '日前求解超时，保持安全功率',
    slot_index: 31,
    plan_generated_at: '2026-07-17T07:00:00Z',
  },
  provenance: {
    load_timestamp: '2026-07-17T08:00:00Z',
    pv_timestamp: '2026-07-17T08:00:01Z',
    storage_timestamp: '2026-07-17T08:00:02Z',
    time_skew_seconds: 2,
    is_stale: false,
  },
  timestamp: '2026-07-17T08:00:03Z',
}

const strategyMetrics = {
  grid_import_kwh: 1800,
  grid_export_kwh: 30,
  energy_cost: 1200,
  demand_cost: 180,
  degradation_cost: 60,
  curtailment_cost: 10,
  cost: 1450,
  peak_grid_kw: 450,
  pv_self_use_rate: 82,
  curtailment_kwh: 12,
  throughput_kwh: 640,
  equivalent_cycles: 0.64,
  terminal_soc: 52,
  plan_execution_rate: null,
  feasible_slot_rate: 100,
}

const comparisonFixture = {
  device_id: 7,
  data_source: 'calculated',
  scenario_key: 'sunny_workday',
  seed: 20260716,
  initial_soc: 50,
  input_series_checksum: 'fixture-checksum',
  solver_status: 'optimal',
  strategies: {
    baseline: strategyMetrics,
    rule: { ...strategyMetrics, cost: 1320, feasible_slot_rate: 97.916667 },
    day_ahead: { ...strategyMetrics, cost: 1240, feasible_slot_rate: 95.833333 },
  },
}

describe('StorageEmsWorkspace', () => {
  beforeEach(() => {
    getStorageEnergyOverviewMock.mockReset().mockResolvedValue(overviewFixture)
    getStorageStrategyComparisonMock.mockReset().mockResolvedValue(comparisonFixture)
    generateStorageDispatchPlanMock.mockReset().mockResolvedValue({})
  })

  it('renders calculated flow, dispatch evidence, persistent source, fallback, and all strategy rows', async () => {
    const wrapper = mount(StorageEmsWorkspace)
    await flushPromises()

    expect(wrapper.text()).toContain('负荷 420.0 kW')
    expect(wrapper.text()).toContain('光伏 186.5 kW')
    expect(wrapper.text()).toContain('电网 113.5 kW')
    expect(wrapper.text()).toContain('储能 120.0 kW')
    expect(wrapper.text()).toContain('目标功率')
    expect(wrapper.text()).toContain('135.0 kW')
    expect(wrapper.text()).toContain('实际功率')
    expect(wrapper.text()).toContain('120.0 kW')
    expect(wrapper.text()).toContain('仿真数据')
    expect(wrapper.text()).toContain('日前求解超时，保持安全功率')
    expect(wrapper.text()).toContain('基线策略')
    expect(wrapper.text()).toContain('规则策略')
    expect(wrapper.text()).toContain('日前策略')
    expect(wrapper.text()).toContain('sunny_workday')
    expect(wrapper.text()).toContain('20260716')
    expect(wrapper.text()).toContain('50.0%')
    expect(wrapper.text()).not.toContain('执行率 100%')
  })

  it('renders missing source as an explicit placeholder', async () => {
    getStorageEnergyOverviewMock.mockResolvedValue({
      ...overviewFixture,
      data_source: 'unknown',
    })

    const wrapper = mount(StorageEmsWorkspace)
    expect(wrapper.get('.storage-ems__source').text()).toBe('--')
    await flushPromises()

    expect(wrapper.get('.storage-ems__source').text()).toBe('--')
  })

  it('does not compare when the overview request fails', async () => {
    getStorageEnergyOverviewMock.mockRejectedValueOnce(new Error('总览不可用'))

    const wrapper = mount(StorageEmsWorkspace)
    await flushPromises()

    expect(wrapper.text()).toContain('总览不可用')
    expect(getStorageStrategyComparisonMock).not.toHaveBeenCalled()
  })

  it('disables all scenario controls while comparison is in flight', async () => {
    getStorageStrategyComparisonMock.mockReturnValueOnce(new Promise(() => undefined))

    const wrapper = mount(StorageEmsWorkspace)
    await flushPromises()

    const controls = wrapper.findAll('select, input, button').filter((item) => (
      item.element.closest('[aria-labelledby="scenario-title"]')
    ))
    expect(controls.length).toBeGreaterThan(0)
    expect(controls.every((item) => item.attributes('disabled') !== undefined)).toBe(true)
  })

  it('gates plan generation for viewer and authorized roles', async () => {
    const viewer = mount(StorageEmsWorkspace, { props: { canGeneratePlan: false } })
    await flushPromises()
    expect(viewer.get('[data-testid="generate-storage-plan"]').attributes('disabled')).toBeDefined()
    expect(viewer.text()).toContain('当前账号仅可查看')

    const authorized = mount(StorageEmsWorkspace, { props: { canGeneratePlan: true } })
    await flushPromises()
    expect(authorized.get('[data-testid="generate-storage-plan"]').attributes('disabled')).toBeUndefined()
    expect(authorized.text()).not.toContain('当前账号仅可查看')
  })

  it('renders an HTTP 200 optimizer failure without refreshing the old plan', async () => {
    generateStorageDispatchPlanMock.mockResolvedValueOnce({
      status: 'failed',
      solver_status: 'Infeasible',
      dispatch_date: '2026-07-17',
      plans: [],
      failure_reason: 'SOC 约束不可行',
    })
    const wrapper = mount(StorageEmsWorkspace, { props: { canGeneratePlan: true } })
    await flushPromises()

    await wrapper.get('[data-testid="generate-storage-plan"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Infeasible')
    expect(wrapper.text()).toContain('SOC 约束不可行')
    expect(getStorageEnergyOverviewMock).toHaveBeenCalledTimes(1)
  })
})
