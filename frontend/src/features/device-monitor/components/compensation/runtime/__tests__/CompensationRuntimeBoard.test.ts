import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationRuntimeBoard from '../CompensationRuntimeBoard.vue'
import type { DeviceMonitorPageModel } from '@/features/device-monitor/composables/useDeviceMonitorPage'

function makePage(overrides: Record<string, unknown> = {}) {
  return {
    realtime: { power_factor: 0.975, flow_rate: 168, reactive_power: 38 },
    compensationPowerFactorTrend: { values: [0.96, 0.97], timestamps: [], target: 0.95 },
    compensationPqPoint: { p: 168, q: 38 },
    compensationPqHistory: [],
    compensationHealthModel: { score: 78, rating: '良好', ratingTone: 'success', breakdown: [] },
    compensationCapacitorBankTelemetry: null,
    compensationCircuitProfile: {},
    compensationMeasurementMetrics: [],
    compensationEvents: [],
    alarms: [],
    alarmActionId: null,
    capacitorBankControlSummaryView: { summaryItems: [], capacityExpansionItems: [], hasSummaryData: false },
    controlConsoleActionCards: [],
    controlConsoleToggleSubmitting: false,
    controlConsoleCurrentControlModeLabel: '自动',
    controlConsoleCanRunManualSwitch: true,
    controlConsoleManualSwitchDisabledReason: '',
    controlConsoleManualPhaseOptions: [],
    controlConsoleManualSwitchActionOptions: [],
    controlConsoleManualCommonGroupOptions: [],
    controlConsoleManualSwitchForm: { phase: 'A', switch_action: 'none', group: 1 },
    controlConsoleLoadError: '',
    canControlDevices: true,
    isPendingArchiveDevice: false,
    timeRange: null,
    handleResolveAlarm: () => {},
    handleControlConsoleManualSwitchCommand: () => {},
    handleControlConsoleActionCard: () => {},
    handleRangeChange: () => {},
    ...overrides,
  }
}

function mountBoard(page: Record<string, unknown>) {
  return mount(CompensationRuntimeBoard, {
    props: { page: page as unknown as DeviceMonitorPageModel },
    global: {
      stubs: {
        CompensationPfTrendCard: true,
        CompensationPqQuadrantCard: true,
        CompensationHealthCard: true,
        CompensationBankTopology: { template: '<div><slot name="header-actions" /></div>', name: 'CompensationBankTopology' },
        CompensationPhaseMatrix: true,
        CompensationCircuitDrawer: true,
        CompensationModeToggle: true,
      },
    },
  })
}

describe('CompensationRuntimeBoard', () => {
  it('渲染 hero / topology / bottom 三段', () => {
    const wrapper = mountBoard(makePage())
    expect(wrapper.find('.rt-hero').exists()).toBe(true)
    expect(wrapper.find('.rt-topology').exists()).toBe(true)
    expect(wrapper.find('.rt-bottom').exists()).toBe(true)
  })

  it('未选中回路时不渲染抽屉', () => {
    const wrapper = mountBoard(makePage())
    expect(wrapper.findComponent({ name: 'CompensationCircuitDrawer' }).exists()).toBe(false)
  })

  it('拓扑 emit pick 后渲染抽屉', async () => {
    const wrapper = mountBoard(makePage())
    await wrapper.findComponent({ name: 'CompensationBankTopology' }).vm.$emit('pick', {
      groupLabel: 'A 相分补',
      phase: 'A',
      commonGroup: null,
      index: 1,
      state: 'on',
      phaseAlarm: false,
    })
    expect(wrapper.findComponent({ name: 'CompensationCircuitDrawer' }).exists()).toBe(true)
  })

  it('底部行渲染统一相矩阵（全宽）', () => {
    const wrapper = mountBoard(makePage())
    expect(wrapper.findComponent({ name: 'CompensationPhaseMatrix' }).exists()).toBe(true)
  })

  it('控制模式切换开关渲染在拓扑卡头部', () => {
    const wrapper = mountBoard(makePage())
    expect(wrapper.findComponent({ name: 'CompensationModeToggle' }).exists()).toBe(true)
  })

  it('快捷时间只更新 timeRange，由页面 watcher 统一触发加载', async () => {
    const handleRangeChange = vi.fn()
    const page = makePage({ handleRangeChange })
    const wrapper = mountBoard(page)

    await wrapper.findComponent({ name: 'CompensationPfTrendCard' }).vm.$emit('range-change', '10m')

    expect(Array.isArray(page.timeRange)).toBe(true)
    expect(handleRangeChange).not.toHaveBeenCalled()
  })
})
