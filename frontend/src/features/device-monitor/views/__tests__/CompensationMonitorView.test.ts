import { describe, expect, it, vi } from 'vitest'
import { defineComponent, reactive } from 'vue'
import { shallowMount } from '@vue/test-utils'
import CompensationMonitorView from '../CompensationMonitorView.vue'

const ShellStub = defineComponent({
  template: `
    <div class="shell-stub">
      <slot name="header" />
      <main><slot name="main" /></main>
      <aside><slot name="side" /></aside>
    </div>
  `,
})

const HeaderStub = defineComponent({
  props: {
    consoleEntryLabel: {
      type: String,
      default: '',
    },
  },
  emits: ['open-console'],
  template: `
    <header class="header-stub">
      <button
        class="header-console-action"
        type="button"
        @click="$emit('open-console')"
      >
        {{ consoleEntryLabel }}
      </button>
    </header>
  `,
})

const ControlSummaryStub = defineComponent({
  emits: ['open-console'],
  template: `
    <button
      class="control-summary-stub"
      type="button"
      @click="$emit('open-console')"
    >
      参数入口
    </button>
  `,
})

const SectionStub = defineComponent({
  props: {
    title: {
      type: String,
      default: '',
    },
  },
  template: `
    <section class="section-stub">
      <h3>{{ title }}</h3>
      <slot />
    </section>
  `,
})

const namedStub = (className: string, label: string) => defineComponent({
  template: `<div class="${className}">${label}</div>`,
})

function createPage(tab = 'runtime') {
  return reactive({
    compensationHeaderModel: {},
    toggleActionLabel: '停用设备',
    toggleButtonType: 'danger',
    toggleSubmitting: false,
    canControlDevices: true,
    isPendingArchiveDevice: false,
    compensationSubtype: 'capacitor_bank_controller',
    isSvgDevice: false,
    compensationWorkbenchTabs: [
      { label: '运行监视', value: 'runtime' },
      { label: '曲线分析', value: 'curves' },
      { label: '参数设置', value: 'parameter-settings' },
      { label: '事件记录', value: 'event-records' },
    ],
    compensationWorkbenchTab: tab,
    router: {
      push: vi.fn(),
    },
    deviceId: 1,
    loadPage: vi.fn(),
    handleToggleDevice: vi.fn(),
    compensationCoreMetric: {},
    compensationPfMetric: {},
    compensationMetrics: [],
    compensationExtendedHint: '',
    compensationCapacitorBankTelemetry: null,
    compensationPowerFactorTrend: [],
    compensationStatusText: '在线',
    compensationStatusTone: 'success',
    compensationAlarmCountMetrics: [],
    compensationDetailTab: 'three-phase',
    compensationSvgTelemetry: null,
    compensationCircuitProfile: null,
    moduleStatusModel: {},
    compensationMeasurementMetrics: [],
    compensationCapacitorBankControlProfile: null,
    compensationTrendTab: 'effect',
    timeRange: null,
    compensationTrendTabs: [
      { label: '补偿效果', value: 'effect' },
      { label: '谐波趋势', value: 'harmonic' },
    ],
    compensationTrendModel: {},
    timeShortcuts: [],
    chartLoading: false,
    handleRangeChange: vi.fn(),
    alarms: [],
    alarmActionId: null,
    handleResolveAlarm: vi.fn(),
    compensationEvents: [],
    capacitorBankControlSummaryView: {
      summaryItems: [],
      capacityExpansionItems: [],
      hasSummaryData: false,
    },
    compensationProfileItems: [],
    svgProfileEditVisible: false,
    templateDiagnostics: {
      template_key: 'capacitor_bank_controller',
      overall_status: 'passed',
    },
    compensationSvgProfile: null,
    loadSVGProfile: vi.fn(),
    controlConsoleLoadError: '',
    controlConsoleProfileWarning: '',
    controlConsoleActionCards: [],
    controlConsoleToggleSubmitting: false,
    controlConsoleCurrentControlModeLabel: '自动',
    controlConsoleCanRunManualSwitch: true,
    controlConsoleManualSwitchDisabledReason: '',
    controlConsoleManualPhaseOptions: [],
    controlConsoleManualSwitchActionOptions: [],
    controlConsoleManualCommonGroupOptions: [],
    controlConsoleManualSwitchForm: {
      phase: 'a',
      switch_action: 'switch_on',
      group: 'common_1',
    },
    handleControlConsoleActionCard: vi.fn(),
    handleControlConsoleManualSwitchCommand: vi.fn(),
    controlConsoleReadonlySectionView: {},
    controlConsoleReadonlySummaryView: {},
    controlConsoleWriteSectionView: {},
    controlConsoleCanWriteParameters: true,
    controlConsoleEditableParameterCards: [],
    openControlConsoleWriteDialog: vi.fn(),
    controlConsoleLogView: {},
    controlConsoleWriteDialogVisible: false,
    controlConsoleSelectedWriteMeta: null,
    controlConsoleControlProfile: null,
    controlConsoleWriteForm: {
      target_value: '',
      reason: '',
    },
    controlConsoleWriteSubmitting: false,
    submitControlConsoleParameterWrite: vi.fn(),
  })
}

function mountView(tab = 'runtime') {
  const page = createPage(tab)
  const wrapper = shallowMount(CompensationMonitorView, {
    props: { page: page as never },
    global: {
      stubs: {
        MonitorViewShell: ShellStub,
        CompensationHeader: HeaderStub,
        CompensationRuntimeBoard: namedStub('runtime-board-stub', '运行监视板'),
        CompensationAlarmRail: namedStub('alarm-rail-stub', '告警栏'),
        CompensationParamSummary: namedStub('param-summary-stub', '参数摘要'),
        CompensationRealtimeOverview: namedStub('runtime-overview-stub', '运行概览'),
        CompensationDetailPanel: namedStub('detail-panel-stub', '运行明细'),
        CompensationTrendPanel: namedStub('trend-panel-stub', '趋势曲线'),
        HarmonicSpectrumPanel: namedStub('harmonic-panel-stub', '高次谐波'),
        CompensationAlarmTable: namedStub('alarm-table-stub', '告警列表'),
        CompensationEventTimeline: namedStub('event-timeline-stub', '事件时间线'),
        CompensationAlarmSummaryPanel: namedStub('alarm-summary-stub', '告警摘要'),
        CompensationControlSummaryPanel: ControlSummaryStub,
        CompensationDeviceProfile: namedStub('device-profile-stub', '设备档案'),
        CompensationDiagnosticsCollapsible: namedStub('diagnostics-stub', '诊断信息'),
        CompensationSvgProfileEditDialog: namedStub('svg-dialog-stub', 'SVG 档案弹窗'),
        ControlConsoleRemotePanel: namedStub('remote-panel-stub', '远程面板'),
        ControlConsoleLogPanel: namedStub('log-panel-stub', '控制日志'),
        ControlConsoleParametersPanel: namedStub('params-panel-stub', '参数面板'),
        ControlConsoleWriteDialog: namedStub('write-dialog-stub', '写入弹窗'),
        MonitorInlineAlert: namedStub('inline-alert-stub', '提示'),
        MonitorSectionPanel: SectionStub,
      },
    },
  })

  return { wrapper, page }
}

describe('CompensationMonitorView', () => {
  it('renders remote control as a runtime module instead of a workbench tab', async () => {
    const { wrapper, page } = mountView()

    expect(wrapper.text()).toContain('运行监视')
    expect(wrapper.text()).toContain('曲线分析')
    expect(wrapper.find('.comp-workbench__tabs').text()).not.toContain('远程控制')
    expect(wrapper.text()).toContain('参数设置')
    expect(wrapper.text()).toContain('事件记录')
    expect(wrapper.find('.runtime-board-stub').exists()).toBe(true)
    expect(wrapper.find('.runtime-overview-stub').exists()).toBe(false)
    expect(wrapper.find('.detail-panel-stub').exists()).toBe(false)
    expect(wrapper.find('.remote-panel-stub').exists()).toBe(false)

    await wrapper.find('.header-console-action').trigger('click')

    expect(page.compensationWorkbenchTab).toBe('runtime')
    expect(page.router.push).not.toHaveBeenCalled()
  })

  it('keeps the remote control module out of non-runtime workbench tabs', () => {
    const { wrapper } = mountView('parameter-settings')

    expect(wrapper.find('.remote-panel-stub').exists()).toBe(false)
    expect(wrapper.find('.params-panel-stub').exists()).toBe(true)
  })

  it('shows the merged parameters panel on the parameter-settings tab', () => {
    const { wrapper } = mountView('parameter-settings')

    expect(wrapper.find('.params-panel-stub').exists()).toBe(true)
    expect(wrapper.findAll('.params-panel-stub')).toHaveLength(1)
    expect(wrapper.find('.remote-panel-stub').exists()).toBe(false)
  })

  it('shows alarms and control logs on the event-records tab', () => {
    const { wrapper } = mountView('event-records')

    expect(wrapper.find('.alarm-table-stub').exists()).toBe(true)
    expect(wrapper.find('.log-panel-stub').exists()).toBe(true)
    expect(wrapper.find('.event-timeline-stub').exists()).toBe(true)
    expect(wrapper.find('.diagnostics-stub').exists()).toBe(true)
    expect(wrapper.find('.remote-panel-stub').exists()).toBe(false)
  })

  it('shows realtime harmonics and historical trends together on the curves tab', () => {
    const { wrapper, page } = mountView('curves')

    expect(wrapper.find('.trend-panel-stub').exists()).toBe(true)
    expect(wrapper.find('.harmonic-panel-stub').exists()).toBe(true)
    expect(page.compensationTrendTab).toBe('effect')
  })
})
