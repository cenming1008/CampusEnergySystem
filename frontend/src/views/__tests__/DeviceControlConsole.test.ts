import { computed } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const {
  getDeviceMonitorOverviewMock,
  getDeviceMonitorControlLogsMock,
  getCompensationCapBankControlProfileMock,
} = vi.hoisted(() => ({
  getDeviceMonitorOverviewMock: vi.fn(),
  getDeviceMonitorControlLogsMock: vi.fn(),
  getCompensationCapBankControlProfileMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: {
      id: '2',
    },
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

vi.mock('@/shared/composables/usePermissions', () => ({
  usePermissions: () => ({
    canManageDevices: computed(() => true),
    canControlDevices: computed(() => true),
    currentRole: computed(() => 'admin'),
    isAdmin: computed(() => true),
  }),
}))

vi.mock('@/api/deviceMonitor', () => ({
  getDeviceMonitorOverview: getDeviceMonitorOverviewMock,
  getDeviceMonitorControlLogs: getDeviceMonitorControlLogsMock,
}))

vi.mock('@/api/compensation', () => ({
  getCompensationCapacitorBankControlProfile: getCompensationCapBankControlProfileMock,
  sendCompensationCapacitorBankRemoteCommand: vi.fn(),
  writeCompensationCapacitorBankControlProfile: vi.fn(),
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
      confirm: vi.fn(),
    },
  }
})

import DeviceControlConsole from '../DeviceControlConsole.vue'

const RemotePanelProbe = defineComponent({
  props: {
    actionCards: {
      type: Array,
      required: true,
    },
  },
  template: `
    <div class="remote-panel-probe">
      远程控制
      {{ actionCards[2]?.actionLabel }}
    </div>
  `,
})

const LogPanelProbe = defineComponent({
  props: {
    logView: {
      type: Object,
      required: true,
    },
  },
  template: `
    <div class="log-panel-probe">
      操作日志
      {{ logView.entries[0]?.title }}|{{ logView.entries[0]?.statusText }}|{{ logView.latestLogText }}
    </div>
  `,
})

const ReadonlyParamsProbe = defineComponent({
  props: {
    readonlySummaryView: {
      type: Object,
      required: true,
    },
  },
  template: `
    <div class="readonly-params-probe">
      {{ readonlySummaryView.sourceStatusText }}|{{ readonlySummaryView.summaryItems[0]?.label }}
    </div>
  `,
})

const WritableParamsProbe = defineComponent({
  props: {
    writeSectionView: {
      type: Object,
      required: true,
    },
    editableParameterCards: {
      type: Array,
      required: true,
    },
  },
  template: `
    <div class="writable-params-probe">
      {{ writeSectionView.roleSummaryText }}|{{ editableParameterCards[0]?.label }}
    </div>
  `,
})

const WriteDialogProbe = defineComponent({
  props: {
    selectedWriteMeta: {
      type: Object,
      required: false,
    },
  },
  template: `
    <div class="write-dialog-probe">
      {{ selectedWriteMeta?.label || 'no-meta' }}
    </div>
  `,
})

const MonitorSectionPanelProbe = defineComponent({
  props: {
    title: {
      type: String,
      required: false,
      default: '',
    },
    subtitle: {
      type: String,
      required: false,
      default: '',
    },
  },
  template: `
    <section class="monitor-section-panel-probe">
      <h3 v-if="title">{{ title }}</h3>
      <p v-if="subtitle">{{ subtitle }}</p>
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

const ConsoleOverviewGridProbe = defineComponent({
  props: {
    items: {
      type: Array,
      required: true,
    },
  },
  template: `
    <div class="console-overview-grid-probe">
      <span
        v-for="item in items"
        :key="item.label"
      >
        {{ item.label }}|{{ item.value }}
      </span>
    </div>
  `,
})

const CompensationHeaderProbe = defineComponent({
  props: {
    model: {
      type: Object,
      required: true,
    },
    consoleEntryLabel: {
      type: String,
      required: false,
      default: '',
    },
    toggleActionLabel: {
      type: String,
      required: true,
    },
    canControlDevices: {
      type: Boolean,
      required: true,
    },
  },
  template: `
    <header class="compensation-header-probe">
      {{ model.title }}|{{ model.serial }}|{{ model.location }}|{{ model.deviceStatus }}|{{ consoleEntryLabel }}|{{ toggleActionLabel }}|{{ canControlDevices ? 'enabled' : 'disabled' }}
    </header>
  `,
})

function mountView() {
  return shallowMount(DeviceControlConsole, {
    global: {
      stubs: {
        ControlConsoleRemotePanel: RemotePanelProbe,
        ControlConsoleLogPanel: LogPanelProbe,
        ControlConsoleReadonlyParamsPanel: ReadonlyParamsProbe,
        ControlConsoleWritableParamsPanel: WritableParamsProbe,
        ControlConsoleWriteDialog: WriteDialogProbe,
        MonitorSectionPanel: MonitorSectionPanelProbe,
        MonitorPageHeader: MonitorPageHeaderProbe,
        CompensationHeader: CompensationHeaderProbe,
        ConsoleOverviewGrid: ConsoleOverviewGridProbe,
        'el-button': true,
        'el-tag': true,
        'el-select': true,
        'el-option': true,
        'el-dialog': true,
        'el-form': true,
        'el-form-item': true,
        'el-switch': true,
        'el-input': true,
        'el-input-number': true,
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

describe('DeviceControlConsole view', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())

    getDeviceMonitorOverviewMock.mockResolvedValue({
      archive: {
        id: 2,
        name: '设备-CAP-001',
        sn: 'CAP-001',
        location: '111',
        device_type: 'capacitor_bank_controller',
        device_subtype: 'capacitor_bank_controller',
      },
      runtime_status: {
        device_id: 2,
        code: 'running',
        label: '运行中',
        is_active: true,
        is_online: true,
        unresolved_alarm_count: 1,
        last_message_at: '2026-04-22T18:03:47',
      },
    })

    getCompensationCapBankControlProfileMock.mockResolvedValue({
      device_id: 2,
      source_status: 'stale',
      is_stale: true,
      source: 'telemetry',
      snapshot_timestamp: '2026-04-22T18:10:00',
      switch_on_power_factor: 92,
      switch_off_power_factor: 100,
      switch_on_delay_seconds: 10,
      switch_off_delay_seconds: 8,
      overvoltage_threshold: 245,
      temperature_upper_limit: 55,
      baud_rate: 9600,
      phase_a_capacity_steps_kvar: [5, 5, 10],
      phase_b_capacity_steps_kvar: [5, 5, 10],
      phase_c_capacity_steps_kvar: [10, 10],
      common_1_capacity_steps_kvar: [10, 10, 20],
      common_2_capacity_steps_kvar: [20, 20],
      common_3_capacity_steps_kvar: [30],
      split_capacity_expansion: {
        phase_a_groups: [],
        phase_b_groups: [],
        phase_c_groups: [],
      },
      common_capacity_expansion: {
        common_1_groups: [],
        common_2_groups: [],
        common_3_groups: [],
      },
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

    getDeviceMonitorControlLogsMock.mockResolvedValue({
      items: [
        {
          id: 10,
          device_id: 2,
          action: 'switch_control_mode',
          target_status: true,
          result: 'success',
          operator: 'admin',
          reason: '控制模式切换 -> 自动模式',
          command_source: 'mqtt',
          created_at: '2026-04-22T18:01:00',
        },
      ],
    })
  })

  it('renders mapper-driven action and parameter texts', async () => {
    const wrapper = mountView()
    await flushAsync()

    const text = wrapper.text()
    expect(wrapper.find('.remote-panel-probe').text()).toContain('切到手动')
    expect(wrapper.find('.readonly-params-probe').text()).toContain('参数可能过期|投入功率因数')
    expect(wrapper.find('.writable-params-probe').text()).toContain('管理员，可发起受控写入|投入功率因数')
    expect(text).not.toContain('设备概览')
    expect(wrapper.find('.log-panel-probe').text()).toContain('控制模式切换|已处理')
    expect(wrapper.find('.log-panel-probe').text()).toContain('已处理 · 2026-04-22 18:01:00')
    expect(text).not.toContain('已开通')
    expect(text).not.toContain('未开通')
  })

  it('uses the monitor header module and points the middle action back to the monitor page', async () => {
    const wrapper = mountView()
    await flushAsync()

    expect(wrapper.find('.compensation-header-probe').text()).toContain('设备-CAP-001|CAP-001|111|在线采集|监控页|停用设备')
    expect(wrapper.text()).not.toContain('前往监控页')
  })

  it('removes overview while keeping control, parameter and log modules', async () => {
    const wrapper = mountView()
    await flushAsync()

    expect(wrapper.find('.console-monitor-layout').exists()).toBe(true)
    expect(wrapper.find('.console-monitor-layout--equal-height').exists()).toBe(true)
    expect(wrapper.find('.console-monitor-layout__main').exists()).toBe(true)
    expect(wrapper.find('.console-monitor-layout__side').exists()).toBe(true)
    expect(wrapper.find('.console-monitor-layout__side--fixed-scroll').exists()).toBe(false)
    expect(wrapper.find('.console-overview-grid-probe').exists()).toBe(false)
    expect(wrapper.find('.log-panel-probe').exists()).toBe(true)
    expect(wrapper.text()).toContain('远程控制')
    expect(wrapper.text()).toContain('参数管理')
    expect(wrapper.text()).toContain('参数修改')
    expect(wrapper.text()).not.toContain('accepted 仅表示指令入队')
    expect(wrapper.text()).toContain('操作日志')
  })

  it('keeps the header device toggle enabled even when console remote actions are unavailable', async () => {
    getCompensationCapBankControlProfileMock.mockResolvedValueOnce({
      device_id: 2,
      source_status: 'live',
      is_stale: false,
      source: 'telemetry',
      capabilities: {
        supports_read: true,
        supports_write: true,
        supports_remote_control: false,
        write_status_message: '',
        remote_control_status_message: '远程控制能力待接入',
        protocol_version: 'campus-control.v1',
        command_message_type: 'control_command',
        receipt_message_type: 'control_receipt',
        control_topic_template: 'campus/control/{device_code}',
        receipt_topic: 'campus/telemetry',
        receipt_timeout_seconds: 120,
        supported_results: ['accepted', 'running', 'success', 'failed', 'timeout', 'rejected'],
      },
    })

    const wrapper = mountView()
    await flushAsync()

    expect(wrapper.find('.compensation-header-probe').text()).toContain('停用设备|enabled')
  })
})
