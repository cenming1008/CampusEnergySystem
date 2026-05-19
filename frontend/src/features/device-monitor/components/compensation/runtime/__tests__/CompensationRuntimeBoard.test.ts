import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationRuntimeBoard from '../CompensationRuntimeBoard.vue'

function makePage(overrides: Record<string, unknown> = {}) {
  return {
    realtime: { power_factor: 0.975, flow_rate: 168, reactive_power: 38 },
    compensationPowerFactorTrend: { values: [0.96, 0.97], timestamps: [], target: 0.95 },
    compensationPqPoint: { p: 168, q: 38 },
    compensationPqHistory: [],
    compensationHealthModel: { score: 78, rating: '良好', ratingTone: 'success', breakdown: [] },
    compensationCapacitorBankTelemetry: null,
    compensationCircuitProfile: {},
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
    props: { page },
    global: {
      stubs: {
        CompensationPfTrendCard: true,
        CompensationPqQuadrantCard: true,
        CompensationHealthCard: true,
        CompensationBankTopology: true,
        CompensationPhaseMatrix: true,
        CompensationCircuitDrawer: true,
        ControlConsoleRemotePanel: true,
        MonitorInlineAlert: true,
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

  it('控制台加载错误时显示告警而非远程控制面板', () => {
    const wrapper = mountBoard(makePage({ controlConsoleLoadError: '控制台不可用' }))
    expect(wrapper.findComponent({ name: 'ControlConsoleRemotePanel' }).exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'MonitorInlineAlert' }).exists()).toBe(true)
  })
})
