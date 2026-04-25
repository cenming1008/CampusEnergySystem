import { beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import EnergyManagement from '../EnergyManagement.vue'
import router from '@/router'

const {
  getEnergyTypesMock,
  getEnergyOverviewMock,
  getCarbonFactorsMock,
  getEnergyDataMock,
  getCarbonEmissionsMock,
  getDevicesMock,
  saveEnergyDataMock,
  errorMock,
  successMock,
} = vi.hoisted(() => ({
  getEnergyTypesMock: vi.fn(),
  getEnergyOverviewMock: vi.fn(),
  getCarbonFactorsMock: vi.fn(),
  getEnergyDataMock: vi.fn(),
  getCarbonEmissionsMock: vi.fn(),
  getDevicesMock: vi.fn(),
  saveEnergyDataMock: vi.fn(),
  errorMock: vi.fn(),
  successMock: vi.fn(),
}))

vi.mock('@/shared/lib/echarts', () => ({
  echarts: {
    init: vi.fn(() => ({
      setOption: vi.fn(),
      resize: vi.fn(),
      dispose: vi.fn(),
    })),
    graphic: {
      LinearGradient: vi.fn(),
    },
  },
}))

vi.mock('@/api/energy', () => ({
  getEnergyTypes: getEnergyTypesMock,
  getEnergyOverview: getEnergyOverviewMock,
  getCarbonFactors: getCarbonFactorsMock,
  getEnergyData: getEnergyDataMock,
  getCarbonEmissions: getCarbonEmissionsMock,
  calculateCarbon: vi.fn(),
  saveEnergyData: saveEnergyDataMock,
}))

vi.mock('@/api/device', () => ({
  getDevices: getDevicesMock,
}))

vi.mock('@/stores/useAuthStore', () => ({
  useAuthStore: () => ({
    locationScope: null,
  }),
}))

vi.mock('@/shared/composables/usePermissions', () => ({
  usePermissions: () => ({
    hasScopedAccess: false,
  }),
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual<typeof import('element-plus')>('element-plus')
  return {
    ...actual,
    ElMessage: {
      error: errorMock,
      success: successMock,
      warning: vi.fn(),
    },
  }
})

function mountView() {
  return shallowMount(EnergyManagement, {
    global: {
      stubs: {
        'el-alert': true,
        'el-button': true,
        'el-collapse': true,
        'el-collapse-item': true,
        'el-date-picker': true,
        'el-dialog': true,
        'el-empty': true,
        'el-form': true,
        'el-form-item': true,
        'el-icon': true,
        'el-input-number': true,
        'el-option': true,
        'el-select': true,
        'el-tab-pane': { template: '<section><slot /></section>' },
        'el-table': true,
        'el-table-column': true,
        'el-tabs': { template: '<div><slot /></div>' },
        'el-tag': true,
        EnergyOverviewTab: true,
        EnergyTrendComparisonTab: true,
        EnergyRankingAnomalyTab: true,
        EnergyDataEntryTab: true,
        EnergyEntryDialog: true,
        EnergyHeaderControls: true,
      },
      directives: {
        loading: () => undefined,
      },
    },
  })
}

async function flushAsync() {
  await Promise.resolve()
  await Promise.resolve()
  await Promise.resolve()
}

function mockOverview() {
  return {
    statistics: {
      electricity: {
        total_consumption: 12,
        avg_consumption: 6,
        avg_flow_rate: 2,
        peak_flow_rate: 4,
        data_count: 2,
      },
    },
    carbon_summary: {
      total_carbon: 8,
      by_energy_type: {},
    },
    time_window: { granularity: 'day', start_time: '2026-04-01T00:00:00', end_time: '2026-04-08T00:00:00' },
    trend: { items: [], peak_load: null, peak_consumption: null, consumption_stat_basis: 'period_delta_from_cumulative_reading' },
    comparison: { period_over_period: null, energy_categories: [], sub_items: [] },
    ranking: { areas: [], buildings: [], devices: [] },
    anomaly: { boundary: 'operational_signal_first_batch', summary: { total_count: 0, data_gap_count: 0, ingestion_failure_count: 0, active_alarm_count: 0 }, items: [] },
    insights: [],
  }
}

describe('EnergyManagement view', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    getEnergyTypesMock.mockReset()
    getEnergyOverviewMock.mockReset()
    getCarbonFactorsMock.mockReset()
    getEnergyDataMock.mockReset()
    getCarbonEmissionsMock.mockReset()
    getDevicesMock.mockReset()
    saveEnergyDataMock.mockReset()
    errorMock.mockReset()
    successMock.mockReset()

    getEnergyTypesMock.mockResolvedValue({
      energy_types: [
        { value: 'electricity', label: '电力', unit: 'kWh', flow_unit: 'kW' },
      ],
    })
    getDevicesMock.mockResolvedValue([])
    getCarbonFactorsMock.mockResolvedValue({ carbon_factors: {} })
    getEnergyOverviewMock.mockResolvedValue(mockOverview())
    saveEnergyDataMock.mockResolvedValue({})
  })

  it('renders dedicated tab components from the energy-management feature', async () => {
    const wrapper = mountView()
    await vi.runAllTimersAsync()
    await flushAsync()

    expect(wrapper.findComponent({ name: 'EnergyOverviewTab' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'EnergyTrendComparisonTab' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'EnergyRankingAnomalyTab' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'EnergyDataEntryTab' }).exists()).toBe(true)
  })

  it('loads merged energy overview with analysis query parameters', async () => {
    mountView()
    await vi.runAllTimersAsync()
    await flushAsync()

    expect(getEnergyOverviewMock).toHaveBeenCalledWith(
      expect.objectContaining({
        include_analysis: true,
        top_n: 5,
        granularity: 'day',
      })
    )
  })

  it('does not register the old forecast route', () => {
    vi.useRealTimers()
    expect(router.resolve('/forecast').name).toBe('NotFound')
  })

  it('reloads overview when ranking top N changes', async () => {
    const wrapper = mountView()
    await vi.runAllTimersAsync()
    await flushAsync()

    getEnergyOverviewMock.mockClear()
    ;(wrapper.vm as unknown as { rankingTopN: number }).rankingTopN = 10
    await flushAsync()

    expect(getEnergyOverviewMock).toHaveBeenCalledWith(
      expect.objectContaining({
        top_n: 10,
      })
    )
  })

  it('saves manual entry and refreshes overview', async () => {
    const wrapper = mountView()
    await vi.runAllTimersAsync()
    await flushAsync()

    getEnergyOverviewMock.mockClear()
    const vm = wrapper.vm as unknown as {
      entryForm: {
        device_id?: number
        energy_type: string
        consumption: number
        flow_rate: number
        timestamp: string
      }
      handleSaveEntry: () => Promise<void>
    }
    vm.entryForm = {
      device_id: 3,
      energy_type: 'electricity',
      consumption: 30,
      flow_rate: 5,
      timestamp: '2026-04-24T08:00:00',
    }

    await vm.handleSaveEntry()
    await flushAsync()

    expect(saveEnergyDataMock).toHaveBeenCalledWith({
      device_id: 3,
      energy_type: 'electricity',
      consumption: 30,
      flow_rate: 5,
      timestamp: '2026-04-24T08:00:00',
    })
    expect(getEnergyOverviewMock).toHaveBeenCalled()
  })
})
