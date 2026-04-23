import { defineComponent } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'

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
  initChartMock,
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
  initChartMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: {
      id: '2',
    },
  }),
  useRouter: () => ({
    back: vi.fn(),
    push: vi.fn(),
  }),
}))

vi.mock('@/shared/composables/usePermissions', () => ({
  usePermissions: () => ({
    canControlDevices: true,
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
        CompensationRealtimeOverview: true,
        CompensationTrendPanel: true,
        CompensationEventTimeline: true,
        CompensationStatusSummary: true,
        CompensationDeviceProfile: true,
        CompensationControlSummaryPanel: true,
        MonitorSectionPanel: MonitorSectionPanelProbe,
        MonitorPageHeader: MonitorPageHeaderProbe,
        CompensationAlarmTable: true,
        CompensationThreePhasePanel: true,
        CompensationCircuitStatePanel: true,
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
      required: true,
    },
  },
  template: '<div class="realtime-overview-probe">{{ moduleStatus.runningModuleCount }}/{{ moduleStatus.totalModuleCount }}</div>',
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

function mountViewWithRealtimeProbe() {
  return shallowMount(DeviceMonitor, {
    global: {
      stubs: {
        CompensationHeader: true,
        CompensationRealtimeOverview: RealtimeOverviewProbe,
        CompensationTrendPanel: true,
        CompensationEventTimeline: true,
        CompensationStatusSummary: true,
        CompensationDeviceProfile: true,
        CompensationControlSummaryPanel: true,
        MonitorSectionPanel: MonitorSectionPanelProbe,
        MonitorPageHeader: MonitorPageHeaderProbe,
        CompensationAlarmTable: true,
        CompensationThreePhasePanel: true,
        CompensationCircuitStatePanel: true,
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
  await Promise.resolve()
  await Promise.resolve()
  await Promise.resolve()
}

describe('DeviceMonitor view', () => {
  beforeEach(() => {
    vi.clearAllMocks()

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
})
