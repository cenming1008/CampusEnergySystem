import { defineComponent, nextTick, reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, shallowMount } from '@vue/test-utils'

const {
  getDeviceMonitorOverviewMock,
  getDeviceMonitorRealtimeMock,
  getDeviceMonitorTrendMock,
  getDeviceMonitorStatusHistoryMock,
  getDeviceMonitorAlarmsMock,
  getDeviceMonitorControlLogsMock,
  getCompensationCapBankLatestMock,
  getCompensationCapBankHistoryMock,
  getCompensationCapBankControlProfileMock,
  getCompensationSvgLatestMock,
  getCompensationSvgHistoryMock,
  getCompensationSvgProfileMock,
  getStorageTelemetryLatestMock,
  getStorageTelemetryHistoryMock,
  initChartMock,
  routeParams,
  routeState,
  routerPushMock,
} = vi.hoisted(() => ({
  getDeviceMonitorOverviewMock: vi.fn(),
  getDeviceMonitorRealtimeMock: vi.fn(),
  getDeviceMonitorTrendMock: vi.fn(),
  getDeviceMonitorStatusHistoryMock: vi.fn(),
  getDeviceMonitorAlarmsMock: vi.fn(),
  getDeviceMonitorControlLogsMock: vi.fn(),
  getCompensationCapBankLatestMock: vi.fn(),
  getCompensationCapBankHistoryMock: vi.fn(),
  getCompensationCapBankControlProfileMock: vi.fn(),
  getCompensationSvgLatestMock: vi.fn(),
  getCompensationSvgHistoryMock: vi.fn(),
  getCompensationSvgProfileMock: vi.fn(),
  getStorageTelemetryLatestMock: vi.fn(),
  getStorageTelemetryHistoryMock: vi.fn(),
  initChartMock: vi.fn(),
  routeParams: { id: '2' },
  routeState: {
    query: {} as Record<string, string>,
  },
  routerPushMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: routeParams,
    query: routeState.query,
  }),
  useRouter: () => ({
    back: vi.fn(),
    push: routerPushMock,
  }),
}))

vi.mock('@/shared/composables/usePermissions', () => ({
  usePermissions: () => ({
    canManageDevices: { value: true },
    canControlDevices: { value: true },
    currentRole: { value: 'admin' },
    isAdmin: { value: true },
  }),
}))

vi.mock('@/shared/composables/useECharts', () => ({
  useECharts: () => ({
    chartRef: { value: null },
    initChart: initChartMock,
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
  }),
}))

vi.mock('@/api/deviceMonitor', () => ({
  getDeviceMonitorOverview: getDeviceMonitorOverviewMock,
  getDeviceMonitorRealtime: getDeviceMonitorRealtimeMock,
  getDeviceMonitorTrend: getDeviceMonitorTrendMock,
  getDeviceMonitorStatusHistory: getDeviceMonitorStatusHistoryMock,
  getDeviceMonitorAlarms: getDeviceMonitorAlarmsMock,
  getDeviceMonitorControlLogs: getDeviceMonitorControlLogsMock,
}))

vi.mock('@/api/compensation', () => ({
  getCompensationCapacitorBankTelemetryLatest: getCompensationCapBankLatestMock,
  getCompensationCapacitorBankTelemetryHistory: getCompensationCapBankHistoryMock,
  getCompensationCapacitorBankControlProfile: getCompensationCapBankControlProfileMock,
  getCompensationSvgOperationsProfile: getCompensationSvgProfileMock,
  getCompensationSvgTelemetryHistory: getCompensationSvgHistoryMock,
  getCompensationSvgTelemetryLatest: getCompensationSvgLatestMock,
}))

vi.mock('@/api/storage', () => ({
  getStorageTelemetryLatest: getStorageTelemetryLatestMock,
  getStorageTelemetryHistory: getStorageTelemetryHistoryMock,
}))

vi.mock('@/api/alarm', () => ({
  resolveAlarm: vi.fn(),
}))

vi.mock('@/api/device', () => ({
  toggleDeviceStatus: vi.fn(),
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual<typeof import('element-plus')>('element-plus')
  return {
    ...actual,
    ElMessage: {
      error: vi.fn(),
      success: vi.fn(),
      warning: vi.fn(),
    },
    ElMessageBox: {
      prompt: vi.fn(),
    },
  }
})

import DeviceMonitor from '../DeviceMonitor.vue'

function mountView() {
  return shallowMount(DeviceMonitor, {
    global: {
      stubs: {
        CompensationHeader: true,
        CompensationMonitorView: false,
        CompensationRealtimeOverview: true,
        CompensationTrendPanel: true,
        CompensationEventTimeline: true,
        CompensationStatusSummary: true,
        CompensationDeviceProfile: true,
        CompensationControlSummaryPanel: true,
        DeviceMetricGrid: DeviceMetricGridProbe,
        DeviceTrendPanel: DeviceTrendPanelProbe,
        DeviceDiagnosticsSummary: DeviceDiagnosticsSummaryProbe,
        DeviceTemplateDiagnosticsPanel: DeviceTemplateDiagnosticsPanelProbe,
        CompensationDiagnosticsCollapsible: DeviceTemplateDiagnosticsPanelProbe,
        StorageHeader: true,
        StorageRealtimeOverview: true,
        StorageTrendPanel: true,
        StorageStatusPanel: true,
        MonitorSectionPanel: MonitorSectionPanelProbe,
        MonitorPageHeader: MonitorPageHeaderProbe,
        MonitorViewShell: false,
        CompensationAlarmTable: true,
        CompensationDetailPanel: true,
        CompensationThreePhasePanel: true,
        CompensationCircuitStatePanel: true,
        GenericMonitorView: false,
        StorageMonitorView: false,
        'el-button': true,
        'el-card': true,
        'el-date-picker': true,
        'el-empty': true,
        'el-radio-group': true,
        'el-radio-button': true,
        'el-segmented': true,
        'el-tag': true,
        'el-scrollbar': true,
        'el-alert': true,
        'el-table': true,
        'el-table-column': true,
      },
      directives: {
        loading: () => undefined,
      },
    },
  })
}

const RealtimeOverviewProbe = defineComponent({
  props: {
    moduleStatus: {
      type: Object,
      required: false,
    },
  },
  template: '<div class="realtime-overview-probe">{{ moduleStatus?.runningModuleCount }}/{{ moduleStatus?.totalModuleCount }}</div>',
})

const MonitorSectionPanelProbe = defineComponent({
  template: `
    <section class="monitor-section-panel-probe">
      <slot name="headerExtra" />
      <slot />
    </section>
  `,
})

const MonitorPageHeaderProbe = defineComponent({
  template: `
    <header class="monitor-page-header-probe">
      <slot name="leading" />
      <slot name="titleMeta" />
      <slot name="actions" />
      <slot />
    </header>
  `,
})

const DeviceMetricGridProbe = defineComponent({
  props: {
    metrics: {
      type: Array,
      required: true,
    },
  },
  template: `
    <div class="device-metric-grid-probe">
      <span
        v-for="item in metrics"
        :key="item.key"
      >
        {{ item.label }}{{ item.value ?? '--' }}{{ item.unit || '' }}
      </span>
    </div>
  `,
})

const DeviceTrendPanelProbe = defineComponent({
  props: {
    fields: {
      type: Array,
      required: true,
    },
  },
  computed: {
    supportedFields() {
      const supported = ['flow_rate', 'voltage', 'current', 'reactive_power', 'power_factor', 'consumption']
      return (this.fields as Array<{ key: string; label: string }>).filter((item) => supported.includes(item.key))
    },
  },
  template: `
    <div class="device-trend-panel-probe">
      <span
        v-for="item in supportedFields"
        :key="item.key"
      >
        {{ item.label }}
      </span>
    </div>
  `,
})

const DeviceDiagnosticsSummaryProbe = defineComponent({
  props: {
    runtimeStatus: {
      type: Object,
      required: false,
    },
    diagnosticsSummary: {
      type: Object,
      required: false,
    },
  },
  template: `
    <div class="device-diagnostics-summary-probe">
      通讯状态
      {{ (diagnosticsSummary?.is_online ?? runtimeStatus?.is_online) ? '在线采集' : '离线' }}
      {{ runtimeStatus?.unresolved_alarm_count ?? 0 }} 条
      {{ diagnosticsSummary?.last_success_at || runtimeStatus?.last_success_at || '' }}
    </div>
  `,
})

const DeviceTemplateDiagnosticsPanelProbe = defineComponent({
  props: {
    diagnostics: {
      type: Object,
      required: false,
    },
  },
  template: `
    <div class="device-template-diagnostics-panel-probe">
      接入诊断
      {{ diagnostics?.template_key || '--' }}
      {{ diagnostics?.overall_status || '--' }}
    </div>
  `,
})

const CompensationTrendPanelSwitchToSpectrumProbe = defineComponent({
  props: {
    tabs: {
      type: Array,
      required: true,
    },
  },
  template: `
    <div class="compensation-trend-panel-spectrum-probe">
      <span
        v-for="item in tabs"
        :key="item.value"
        class="trend-tab-label"
      >
        {{ item.label }}
      </span>
    </div>
  `,
})

function mountViewWithRealtimeProbe() {
  return shallowMount(DeviceMonitor, {
    global: {
      stubs: {
        CompensationHeader: true,
        CompensationMonitorView: false,
        CompensationRealtimeOverview: true,
        CompensationTrendPanel: true,
        CompensationEventTimeline: true,
        CompensationStatusSummary: true,
        CompensationDeviceProfile: true,
        CompensationControlSummaryPanel: true,
        DeviceMetricGrid: DeviceMetricGridProbe,
        DeviceTrendPanel: DeviceTrendPanelProbe,
        DeviceDiagnosticsSummary: DeviceDiagnosticsSummaryProbe,
        DeviceTemplateDiagnosticsPanel: DeviceTemplateDiagnosticsPanelProbe,
        CompensationDiagnosticsCollapsible: DeviceTemplateDiagnosticsPanelProbe,
        StorageHeader: true,
        StorageRealtimeOverview: true,
        StorageTrendPanel: true,
        StorageStatusPanel: true,
        MonitorSectionPanel: MonitorSectionPanelProbe,
        MonitorPageHeader: MonitorPageHeaderProbe,
        MonitorViewShell: false,
        CompensationAlarmTable: true,
        CompensationDetailPanel: RealtimeOverviewProbe,
        CompensationThreePhasePanel: true,
        CompensationCircuitStatePanel: true,
        GenericMonitorView: false,
        StorageMonitorView: false,
        'el-button': true,
        'el-card': true,
        'el-date-picker': true,
        'el-empty': true,
        'el-radio-group': true,
        'el-radio-button': true,
        'el-segmented': true,
        'el-tag': true,
        'el-scrollbar': true,
        'el-alert': true,
        'el-table': true,
        'el-table-column': true,
      },
      directives: {
        loading: () => undefined,
      },
    },
  })
}

function mountViewWithSpectrumTabProbe() {
  return shallowMount(DeviceMonitor, {
    global: {
      stubs: {
        CompensationHeader: true,
        CompensationMonitorView: false,
        CompensationRealtimeOverview: true,
        CompensationTrendPanel: CompensationTrendPanelSwitchToSpectrumProbe,
        CompensationEventTimeline: true,
        CompensationStatusSummary: true,
        CompensationDeviceProfile: true,
        CompensationControlSummaryPanel: true,
        DeviceMetricGrid: DeviceMetricGridProbe,
        DeviceTrendPanel: DeviceTrendPanelProbe,
        DeviceDiagnosticsSummary: DeviceDiagnosticsSummaryProbe,
        DeviceTemplateDiagnosticsPanel: DeviceTemplateDiagnosticsPanelProbe,
        CompensationDiagnosticsCollapsible: DeviceTemplateDiagnosticsPanelProbe,
        StorageHeader: true,
        StorageRealtimeOverview: true,
        StorageTrendPanel: true,
        StorageStatusPanel: true,
        MonitorSectionPanel: MonitorSectionPanelProbe,
        MonitorPageHeader: MonitorPageHeaderProbe,
        MonitorViewShell: false,
        CompensationAlarmTable: true,
        CompensationDetailPanel: true,
        CompensationThreePhasePanel: true,
        CompensationCircuitStatePanel: true,
        GenericMonitorView: false,
        StorageMonitorView: false,
        'el-button': true,
        'el-card': true,
        'el-date-picker': true,
        'el-empty': true,
        'el-radio-group': true,
        'el-radio-button': true,
        'el-segmented': true,
        'el-tag': true,
        'el-scrollbar': true,
        'el-alert': true,
        'el-table': true,
        'el-table-column': true,
      },
      directives: {
        loading: () => undefined,
      },
    },
  })
}

async function flushAsync() {
  await flushPromises()
  await flushPromises()
}

describe('DeviceMonitor view', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    routeParams.id = '2'
    routeState.query = reactive({})

    getDeviceMonitorOverviewMock.mockResolvedValue({
      archive: {
        id: 2,
        name: '设备-CAP-001',
        sn: 'CAP-001',
        device_type: 'capacitor_bank_controller',
        device_subtype: 'capacitor_bank_controller',
        device_category: 'compensation',
        energy_type: 'electricity',
        unit: 'kW',
      },
      runtime_status: {
        device_id: 2,
        code: 'running',
        label: '运行中',
        is_active: true,
        is_online: true,
        unresolved_alarm_count: 0,
      },
      realtime: {
        device_id: 2,
        timestamp: '2026-04-21T17:09:39',
        flow_rate: 59,
        voltage: 220.5,
        current: 84.57,
        power_factor: 0.9034,
        reactive_power: -28,
        temperature: 41.2,
      },
      ingestion_health: {},
      recent_alarms: [],
      recent_control_logs: [],
      compensation_monitor: {
        subtype: 'capacitor_bank_controller',
        control_mode: {
          value: '手动',
          source: 'telemetry',
          state: 'live',
        },
        circuit_summary: {
          running_count: 6,
          total_count: 24,
          has_realtime_state: true,
          source: 'telemetry',
          state: 'live',
        },
        profile_status: {
          source_status: 'fresh',
          is_stale: false,
        },
        key_metrics: {
          capacity_utilization: {
            value: 25,
            source: 'telemetry',
            state: 'live',
          },
          cabinet_temperature: {
            value: 41.2,
            source: 'telemetry',
            state: 'live',
          },
          compensation_level: {
            value: 6,
            source: 'telemetry',
            state: 'live',
          },
        },
        capabilities_summary: {
          supports_read: true,
          supports_write: true,
          supports_remote_control: true,
        },
      },
      template_diagnostics: {
        template_key: 'capacitor_bank_controller',
        display_name: '电容补偿控制器',
        category: 'compensation',
        subtype: 'capacitor_bank_controller',
        metric_coverage: {
          total: 6,
          live: 6,
          missing: 0,
          missing_keys: [],
        },
        trend_coverage: {
          declared_keys: ['reactive_power', 'power_factor', 'voltage', 'current'],
          drawable_keys: ['reactive_power', 'power_factor', 'voltage', 'current'],
          unsupported_keys: [],
        },
        panel_coverage: {
          specific_panels: ['three_phase', 'circuit_state', 'harmonic_spectrum', 'control_profile', 'control_summary'],
        },
        ingestion_health: {
          ingestion_status: 'online',
          is_online: true,
        },
        overall_status: 'passed',
      },
    })
    getDeviceMonitorTrendMock.mockResolvedValue({
      device_id: 2,
      start_time: '2026-04-21T16:10:52',
      end_time: '2026-04-21T17:10:52',
      points: [],
      summary: { latest: 0, peak: 0, valley: 0, average: 0 },
    })
    getDeviceMonitorStatusHistoryMock.mockResolvedValue({ items: [] })
    getDeviceMonitorAlarmsMock.mockResolvedValue({ items: [] })
    getDeviceMonitorControlLogsMock.mockResolvedValue({ items: [] })
    getDeviceMonitorRealtimeMock.mockResolvedValue({
      device_id: 2,
      timestamp: '2026-04-21T17:09:39',
    })
    getCompensationCapBankLatestMock.mockResolvedValue({
      device_id: 2,
      timestamp: '2026-04-21T17:09:39',
      temperature: 41.2,
      frequency: 50,
    })
    getCompensationCapBankHistoryMock.mockResolvedValue([
      { device_id: 2, timestamp: '2026-04-21T16:32:03', temperature: 40.5, frequency: 49.98 },
      { device_id: 2, timestamp: '2026-04-21T17:10:52', temperature: 40.8, frequency: 49.98 },
    ])
    getCompensationCapBankControlProfileMock.mockResolvedValue({
      device_id: 2,
      source_status: 'fresh',
      is_stale: false,
      source: 'telemetry',
      snapshot_timestamp: '2026-04-21T17:10:10',
      split_capacity_expansion: { phase_a_groups: [], phase_b_groups: [], phase_c_groups: [] },
      common_capacity_expansion: { common_1_groups: [], common_2_groups: [], common_3_groups: [] },
      capabilities: {
        supports_read: true,
        supports_write: true,
        supports_remote_control: true,
        write_status_message: '',
        remote_control_status_message: '',
        protocol_version: 'campus-control.v1',
        command_message_type: 'control_command',
        receipt_message_type: 'control_receipt',
        control_topic_template: 'campus/control/{device_code}',
        receipt_topic: 'campus/telemetry',
        receipt_timeout_seconds: 120,
        supported_results: ['accepted', 'running', 'success', 'failed', 'timeout', 'rejected'],
      },
    })
    getCompensationSvgLatestMock.mockResolvedValue({
      device_id: 2,
      timestamp: '2026-04-21T17:09:39',
      auto_mode: true,
      capacity_utilization: 50,
      cabinet_temp: 36.5,
    })
    getCompensationSvgHistoryMock.mockResolvedValue([])
    getCompensationSvgProfileMock.mockResolvedValue({
      device_id: 2,
      module_count: 8,
    })
    getStorageTelemetryLatestMock.mockResolvedValue(null)
    getStorageTelemetryHistoryMock.mockResolvedValue([])
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('mounts the monitor page without crashing on initial refresh load', async () => {
    const wrapper = mountView()
    await flushAsync()

    expect(wrapper.exists()).toBe(true)
    expect(getDeviceMonitorOverviewMock).toHaveBeenCalledTimes(1)
    expect(getCompensationCapBankHistoryMock).toHaveBeenCalledTimes(1)
  })

  it('opens capacitor-bank workbench on remote-control tab from query', async () => {
    routeParams.id = '8'
    routeState.query.tab = 'remote-control'
    getDeviceMonitorOverviewMock.mockResolvedValueOnce({
      archive: {
        id: 8,
        name: '无功补偿控制器',
        sn: 'CAP-001',
        device_type: 'compensation',
        device_subtype: 'capacitor_bank_controller',
        archive_status: 'active',
      },
      runtime_status: {
        device_id: 8,
        code: 'running',
        label: '运行中',
        is_active: true,
        is_online: true,
        unresolved_alarm_count: 0,
      },
      realtime: {
        device_id: 8,
        timestamp: '2026-04-21T17:09:39',
        reactive_power: -28,
        power_factor: 0.9034,
      },
      ingestion_health: {},
      recent_alarms: [],
      recent_control_logs: [],
      compensation_monitor: {
        subtype: 'capacitor_bank_controller',
        control_mode: {
          value: '手动',
          source: 'telemetry',
          state: 'live',
        },
        circuit_summary: {
          running_count: 6,
          total_count: 24,
          has_realtime_state: true,
          source: 'telemetry',
          state: 'live',
        },
        profile_status: {
          source_status: 'fresh',
          is_stale: false,
        },
        key_metrics: {},
        capabilities_summary: {
          supports_read: true,
          supports_write: true,
          supports_remote_control: true,
        },
      },
    })

    const wrapper = mountView()
    await flushAsync()

    const page = wrapper.findComponent({ name: 'CompensationMonitorView' }).props('page') as {
      compensationWorkbenchTab: string
    }
    expect(page.compensationWorkbenchTab).toBe('remote-control')
  })

  it('syncs capacitor-bank workbench tab when route query changes', async () => {
    const wrapper = mountView()
    await flushAsync()

    const page = wrapper.findComponent({ name: 'CompensationMonitorView' }).props('page') as {
      compensationWorkbenchTab: string
    }
    expect(page.compensationWorkbenchTab).toBe('runtime')

    routeState.query.tab = 'parameter-settings'
    await flushAsync()

    expect(page.compensationWorkbenchTab).toBe('parameter-settings')
  })

  it('keeps compensation devices on the dedicated path instead of generic metric fallback', async () => {
    const wrapper = mountView()
    await flushAsync()

    expect(wrapper.find('.device-metric-grid-probe').exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'CompensationMonitorView' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'GenericMonitorView' }).exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'CompensationHeader' }).exists()).toBe(true)
    expect(wrapper.find('.device-template-diagnostics-panel-probe').exists()).toBe(true)
  })

  it('renders the harmonic spectrum panel as a standalone section for capacitor bank controllers', async () => {
    getCompensationCapBankLatestMock.mockResolvedValueOnce({
      device_id: 2,
      timestamp: '2026-04-21T17:09:39',
      voltage_harmonics_a: [
        { order: 2, value: 1.2 },
        { order: 5, value: 6.4 },
      ],
    })

    const wrapper = mountViewWithSpectrumTabProbe()
    await flushAsync()

    const page = wrapper.findComponent({ name: 'CompensationMonitorView' }).props('page') as {
      compensationWorkbenchTab: string
    }
    page.compensationWorkbenchTab = 'curves'
    await nextTick()

    const trendProbeText = wrapper.find('.compensation-trend-panel-spectrum-probe').text()
    expect(trendProbeText).toContain('谐波趋势')
    expect(trendProbeText).not.toContain('高次谐波')
    expect(wrapper.findComponent({ name: 'HarmonicSpectrumPanel' }).exists()).toBe(true)
  })

  it.each(['offline', 'missing', 'partial'] as const)(
    'keeps capacitor bank diagnostics on the dedicated path when template status is %s',
    async (overallStatus) => {
      getDeviceMonitorOverviewMock.mockResolvedValueOnce({
        archive: {
          id: 2,
          name: '无功补偿器',
          sn: 'SN001',
          device_type: 'capacitor_bank_controller',
          device_subtype: 'capacitor_bank_controller',
          device_category: 'compensation',
          energy_type: 'electricity',
          unit: 'kVar',
        },
        runtime_status: {
          device_id: 2,
          code: overallStatus === 'offline' ? 'offline' : 'unknown',
          label: overallStatus === 'offline' ? '离线' : '状态未知',
          is_active: true,
          is_online: overallStatus !== 'offline',
          ingestion_status: overallStatus === 'offline' ? 'offline' : 'online',
          unresolved_alarm_count: 0,
        },
        realtime: {
          device_id: 2,
          timestamp: null,
        },
        ingestion_health: {},
        recent_alarms: [],
        recent_control_logs: [],
        compensation_monitor: {
          subtype: 'capacitor_bank_controller',
          control_mode: {
            value: '自动',
            source: 'configured_fallback',
            state: 'mock',
          },
          circuit_summary: {
            running_count: 0,
            total_count: 24,
            has_realtime_state: false,
            source: 'missing',
            state: 'missing',
          },
          profile_status: {
            source_status: 'empty',
            is_stale: true,
          },
          key_metrics: {},
          capabilities_summary: {
            supports_read: true,
            supports_write: true,
            supports_remote_control: true,
          },
        },
        template_diagnostics: {
          template_key: 'capacitor_bank_controller',
          display_name: '电容补偿控制器',
          category: 'compensation',
          subtype: 'capacitor_bank_controller',
          metric_coverage: {
            total: 6,
            live: overallStatus === 'partial' ? 1 : 0,
            missing: overallStatus === 'partial' ? 5 : 6,
            missing_keys: ['reactive_power', 'power_factor', 'voltage', 'current', 'running_circuit_count', 'capacity_utilization'],
          },
          trend_coverage: {
            declared_keys: ['reactive_power', 'power_factor', 'voltage', 'current'],
            drawable_keys: ['reactive_power', 'power_factor', 'voltage', 'current'],
            unsupported_keys: [],
          },
          panel_coverage: {
            specific_panels: ['three_phase', 'circuit_state', 'harmonic_spectrum', 'control_profile', 'control_summary'],
          },
          ingestion_health: {
            ingestion_status: overallStatus === 'offline' ? 'offline' : 'online',
            is_online: overallStatus !== 'offline',
          },
          overall_status: overallStatus,
        },
      })
      getCompensationCapBankLatestMock.mockResolvedValueOnce(null)
      getCompensationCapBankHistoryMock.mockResolvedValueOnce([])

      const wrapper = mountView()
      await flushAsync()

      expect(wrapper.findComponent({ name: 'CompensationMonitorView' }).exists()).toBe(true)
      expect(wrapper.findComponent({ name: 'GenericMonitorView' }).exists()).toBe(false)
      expect(wrapper.find('.device-template-diagnostics-panel-probe').text()).toContain('capacitor_bank_controller')
      expect(wrapper.find('.device-template-diagnostics-panel-probe').text()).toContain(overallStatus)
    },
  )

  it('prefers backend compensation semantics for svg module counts', async () => {
    getDeviceMonitorOverviewMock.mockResolvedValueOnce({
      archive: {
        id: 2,
        name: '设备-SVG-001',
        sn: 'SVG-001',
        device_type: 'svg',
        device_subtype: 'svg',
        device_category: 'compensation',
        energy_type: 'electricity',
        unit: 'kVar',
      },
      runtime_status: {
        device_id: 2,
        code: 'running',
        label: '运行中',
        is_active: true,
        is_online: true,
        unresolved_alarm_count: 0,
      },
      realtime: {
        device_id: 2,
        timestamp: '2026-04-21T17:09:39',
        reactive_power: 48,
        power_factor: 0.99,
        temperature: 36.5,
      },
      ingestion_health: {},
      recent_alarms: [],
      recent_control_logs: [],
      compensation_monitor: {
        subtype: 'svg',
        control_mode: {
          value: '自动',
          source: 'telemetry',
          state: 'live',
        },
        circuit_summary: {
          running_count: 6,
          total_count: 12,
          has_realtime_state: true,
          source: 'telemetry',
          state: 'live',
        },
        profile_status: null,
        key_metrics: {
          capacity_utilization: {
            value: 50,
            source: 'telemetry',
            state: 'live',
          },
          cabinet_temperature: {
            value: 36.5,
            source: 'telemetry',
            state: 'live',
          },
          compensation_level: {
            value: 6,
            source: 'telemetry',
            state: 'live',
          },
        },
        capabilities_summary: {
          supports_read: true,
          supports_write: false,
          supports_remote_control: false,
        },
      },
    })

    const wrapper = mountViewWithRealtimeProbe()
    await flushAsync()

    expect(wrapper.find('.realtime-overview-probe').text()).toBe('6/12')
  })

  it('marks stale realtime values when ingestion is offline', async () => {
    getDeviceMonitorOverviewMock.mockResolvedValueOnce({
      archive: {
        id: 2,
        name: '2号水表',
        sn: 'WT-002',
        device_type: 'water_meter',
        device_category: 'water_meter',
        energy_type: 'water',
        unit: 'm³/h',
      },
      runtime_status: {
        device_id: 2,
        code: 'offline',
        label: '离线',
        is_active: true,
        is_online: false,
        ingestion_status: 'offline',
        unresolved_alarm_count: 0,
        last_message_at: '2026-04-21T17:00:00',
        last_success_at: '2026-04-21T17:00:00',
        latest_timestamp: '2026-04-21T17:00:00',
      },
      realtime: {
        device_id: 2,
        timestamp: '2026-04-21T17:00:00',
        flow_rate: 2.1,
        consumption: 40,
      },
      ingestion_health: {},
      recent_alarms: [],
      recent_control_logs: [],
      compensation_monitor: null,
    })

    const wrapper = mountView()
    await flushAsync()

    expect(wrapper.text()).toContain('通讯状态')
    expect(wrapper.text()).toContain('离线')
    expect(wrapper.text()).toContain('实时功率/流量')
    expect(wrapper.text()).toContain('数据已过期')
    expect(wrapper.text()).toContain('最近成功入库')
    expect(wrapper.text()).toContain('2026-04-21 17:00:00')
  })

  it('renders generic monitor metrics and trend options from backend template fields', async () => {
    getDeviceMonitorOverviewMock.mockResolvedValueOnce({
      archive: {
        id: 2,
        name: '2号水表',
        sn: 'WT-002',
        device_type: 'water_meter',
        device_category: 'water_meter',
        energy_type: 'water',
        unit: 'm³/h',
      },
      runtime_status: {
        device_id: 2,
        code: 'running',
        label: '运行中',
        is_active: true,
        is_online: true,
        ingestion_status: 'online',
        unresolved_alarm_count: 0,
      },
      realtime: {
        device_id: 2,
        timestamp: '2026-04-21T17:00:00',
        flow_rate: 2.1,
        consumption: 40,
        pressure: 0.33,
        temperature: 21.5,
      },
      ingestion_health: {},
      recent_alarms: [],
      recent_control_logs: [],
      compensation_monitor: null,
      monitor_template: {
        template_key: 'generic_device',
        category: 'water_meter',
        subtype: null,
        display_name: '通用设备',
        specific_panels: [],
      },
      metric_cards: [
        { key: 'pressure', label: '压力', value: 0.33, unit: 'MPa', precision: 2, source: 'realtime', state: 'live' },
        { key: 'temperature', label: '温度', value: 21.5, unit: '°C', precision: 1, source: 'realtime', state: 'live' },
        { key: 'voltage', label: '电压', value: null, unit: 'V', precision: 1, source: 'missing', state: 'missing' },
      ],
      trend_fields: [
        { key: 'consumption', label: '累计读数', unit: 'm³', precision: 1 },
        { key: 'voltage', label: '电压', unit: 'V', precision: 1 },
        { key: 'pressure', label: '不支持趋势', unit: 'MPa', precision: 2 },
      ],
      diagnostics_summary: {
        ingestion_status: 'online',
        is_online: true,
        last_message_at: '2026-04-21T17:00:00',
        last_success_at: '2026-04-21T17:00:00',
      },
      template_diagnostics: {
        template_key: 'water_meter',
        display_name: '水表',
        category: 'water_meter',
        subtype: null,
        metric_coverage: {
          total: 3,
          live: 2,
          missing: 1,
          missing_keys: ['voltage'],
        },
        trend_coverage: {
          declared_keys: ['consumption', 'voltage', 'pressure'],
          drawable_keys: ['consumption', 'voltage'],
          unsupported_keys: ['pressure'],
        },
        panel_coverage: {
          specific_panels: [],
        },
        ingestion_health: {
          ingestion_status: 'online',
          is_online: true,
          last_message_at: '2026-04-21T17:00:00',
          last_success_at: '2026-04-21T17:00:00',
        },
        overall_status: 'partial',
      },
    })

    const wrapper = mountView()
    await flushAsync()

    expect(wrapper.findComponent({ name: 'GenericMonitorView' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'CompensationMonitorView' }).exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'StorageMonitorView' }).exists()).toBe(false)
    expect(wrapper.text()).toContain('压力')
    expect(wrapper.text()).toContain('0.33')
    expect(wrapper.text()).toContain('MPa')
    expect(wrapper.text()).toContain('温度')
    expect(wrapper.text()).toContain('21.5')
    expect(wrapper.text()).toContain('电压')
    expect(wrapper.text()).toContain('--')

    const trendOptions = (wrapper.vm as unknown as { page: { chartMetricOptions: Array<{ label: string }> } }).page.chartMetricOptions
    expect(trendOptions.map((item) => item.label)).toContain('累计读数')
    expect(trendOptions.map((item) => item.label)).toContain('电压')
    expect(wrapper.text()).not.toContain('不支持趋势')
    expect(wrapper.find('.device-template-diagnostics-panel-probe').text()).toContain('water_meter')
  })

  it('keeps storage devices on the dedicated path instead of generic metric fallback', async () => {
    getDeviceMonitorOverviewMock.mockResolvedValueOnce({
      archive: {
        id: 2,
        name: '储能柜',
        sn: 'ESS-001',
        device_type: 'storage',
        device_category: 'storage',
        energy_type: 'electricity',
        unit: 'kW',
      },
      runtime_status: {
        device_id: 2,
        code: 'running',
        label: '运行中',
        is_active: true,
        is_online: true,
        unresolved_alarm_count: 0,
      },
      realtime: {
        device_id: 2,
        timestamp: '2026-04-21T17:00:00',
        flow_rate: 12,
        voltage: 380,
        current: 21,
      },
      ingestion_health: {},
      recent_alarms: [],
      recent_control_logs: [],
      compensation_monitor: null,
      storage_monitor: {
        key_metrics: {
          soc: { value: 76, source: 'telemetry', state: 'live' },
        },
      },
      monitor_template: {
        template_key: 'storage',
        category: 'storage',
        subtype: null,
        display_name: '储能设备',
        specific_panels: ['storage_realtime', 'storage_trend', 'storage_status'],
      },
      metric_cards: [
        { key: 'soc', label: 'SOC', value: 76, unit: '%', precision: 1, source: 'telemetry', state: 'live' },
      ],
      trend_fields: [
        { key: 'flow_rate', label: '功率', unit: 'kW', precision: 2 },
      ],
      template_diagnostics: {
        template_key: 'storage',
        display_name: '储能设备',
        category: 'storage',
        subtype: null,
        metric_coverage: {
          total: 1,
          live: 1,
          missing: 0,
          missing_keys: [],
        },
        trend_coverage: {
          declared_keys: ['flow_rate'],
          drawable_keys: ['flow_rate'],
          unsupported_keys: [],
        },
        panel_coverage: {
          specific_panels: ['storage_realtime', 'storage_trend', 'storage_status'],
        },
        ingestion_health: {
          ingestion_status: 'online',
          is_online: true,
        },
        overall_status: 'passed',
      },
    })
    getStorageTelemetryLatestMock.mockResolvedValueOnce({
      device_id: 2,
      timestamp: '2026-04-21T17:00:00',
      soc: 76,
      active_power: 12,
    })

    const wrapper = mountView()
    await flushAsync()

    expect(wrapper.find('.device-metric-grid-probe').exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'StorageMonitorView' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'GenericMonitorView' }).exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'StorageHeader' }).exists()).toBe(true)
    expect(wrapper.find('.device-template-diagnostics-panel-probe').exists()).toBe(true)
    expect(getStorageTelemetryLatestMock).toHaveBeenCalledTimes(1)
  })

  it('refreshes compensation summary semantics during realtime polling', async () => {
    vi.useFakeTimers()

    const wrapper = mountViewWithRealtimeProbe()
    await flushAsync()

    expect(wrapper.find('.realtime-overview-probe').text()).toBe('6/24')

    getDeviceMonitorOverviewMock.mockResolvedValueOnce({
      archive: {
        id: 2,
        name: '设备-CAP-001',
        sn: 'CAP-001',
        device_type: 'capacitor_bank_controller',
        device_subtype: 'capacitor_bank_controller',
        device_category: 'compensation',
        energy_type: 'electricity',
        unit: 'kW',
      },
      runtime_status: {
        device_id: 2,
        code: 'running',
        label: '运行中',
        is_active: true,
        is_online: true,
        unresolved_alarm_count: 0,
      },
      realtime: {
        device_id: 2,
        timestamp: '2026-04-21T17:14:39',
        flow_rate: 60,
        voltage: 220.8,
        current: 85.1,
        power_factor: 0.92,
        reactive_power: 32,
        temperature: 41.6,
      },
      ingestion_health: {},
      recent_alarms: [],
      recent_control_logs: [],
      compensation_monitor: {
        subtype: 'capacitor_bank_controller',
        control_mode: {
          value: '自动',
          source: 'telemetry',
          state: 'live',
        },
        circuit_summary: {
          running_count: 20,
          total_count: 20,
          has_realtime_state: true,
          source: 'telemetry',
          state: 'live',
        },
        profile_status: {
          source_status: 'fresh',
          is_stale: false,
        },
        key_metrics: {
          capacity_utilization: {
            value: 100,
            source: 'telemetry',
            state: 'live',
          },
          cabinet_temperature: {
            value: 41.6,
            source: 'telemetry',
            state: 'live',
          },
          compensation_level: {
            value: 20,
            source: 'telemetry',
            state: 'live',
          },
        },
        capabilities_summary: {
          supports_read: true,
          supports_write: true,
          supports_remote_control: true,
        },
      },
    })

    getDeviceMonitorRealtimeMock.mockResolvedValueOnce({
      device_id: 2,
      timestamp: '2026-04-21T17:14:39',
      flow_rate: 60,
      voltage: 220.8,
      current: 85.1,
      power_factor: 0.92,
      reactive_power: 32,
      temperature: 41.6,
    })

    await vi.advanceTimersByTimeAsync(5000)
    await flushAsync()

    expect(getDeviceMonitorOverviewMock).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.realtime-overview-probe').text()).toBe('20/20')
  })

  it('keeps the default recent trend window live during realtime polling', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-04-21T17:10:52'))

    mountView()
    await flushAsync()

    expect(getDeviceMonitorTrendMock).toHaveBeenCalledWith(2, expect.objectContaining({
      start_time: '2026-04-21T16:10:52',
      end_time: '2026-04-21T17:10:52',
    }))

    await vi.advanceTimersByTimeAsync(5000)
    await flushAsync()

    expect(getDeviceMonitorTrendMock).toHaveBeenLastCalledWith(2, expect.objectContaining({
      start_time: '2026-04-21T16:10:57',
      end_time: '2026-04-21T17:10:57',
    }))
  })
})
