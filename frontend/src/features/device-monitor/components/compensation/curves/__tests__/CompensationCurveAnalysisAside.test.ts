import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationCurveAnalysisAside from '../CompensationCurveAnalysisAside.vue'
import type {
  CompensationCapacitorBankControlProfile,
  CompensationCapacitorBankTelemetry,
} from '@/api/compensation'
import type { DeviceAlarmRecord } from '@/api/deviceMonitor'
import type { CompensationEventItem } from '@/features/device-monitor/components/compensation/types'

const telemetry: CompensationCapacitorBankTelemetry = {
  device_id: 12,
  timestamp: '2026-05-21T10:00:00+08:00',
  power_factor_a: 0.96,
  power_factor_b: 0.95,
  power_factor_c: 0.97,
  reactive_power_a: 1,
  reactive_power_b: 2,
  reactive_power_c: 3,
  voltage_thd_a: 4.3,
  voltage_thd_b: 4.4,
  voltage_thd_c: 4.5,
  current_harmonic_a: 0,
  current_harmonic_b: 0,
  current_harmonic_c: 0,
  temperature: 37.2,
  voltage_harmonics_a: [
    { order: 3, value: 2.4 },
    { order: 5, value: 2.8 },
  ],
  voltage_harmonics_b: [
    { order: 3, value: 2.5 },
    { order: 5, value: 2.7 },
  ],
  voltage_harmonics_c: [
    { order: 3, value: 2.4 },
    { order: 5, value: 2.7 },
  ],
}

const history: CompensationCapacitorBankTelemetry[] = [
  { ...telemetry, timestamp: '2026-05-21T09:50:00+08:00', power_factor_a: 0.94, power_factor_b: 0.95, power_factor_c: 0.96 },
  telemetry,
]

const controlProfile: CompensationCapacitorBankControlProfile = {
  device_id: 12,
  switch_on_power_factor: 0.95,
  voltage_harmonic_threshold: 5,
  current_harmonic_threshold: 8,
  temperature_upper_limit: 65,
  source_status: 'fresh',
  is_stale: false,
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
    protocol_version: 'test',
    command_message_type: 'set',
    receipt_message_type: 'receipt',
    control_topic_template: '',
    receipt_topic: '',
    receipt_timeout_seconds: 5,
    supported_results: [],
  },
}

const alarms: DeviceAlarmRecord[] = [
  {
    id: 1,
    device_id: 12,
    message: 'A 相电压谐波超限：27.70%（门限 5.00%）',
    severity: 'warning',
    category: 'harmonic',
    source: 'platform_rule',
    timestamp: '2026-05-21T09:55:00+08:00',
    is_resolved: false,
  },
  {
    id: 2,
    device_id: 12,
    message: '通讯恢复',
    severity: 'info',
    category: 'communication',
    source: 'platform_comm',
    timestamp: '2026-05-21T09:56:00+08:00',
    is_resolved: true,
  },
]

const events: CompensationEventItem[] = [
  {
    time: '2026-05-21T09:58:00+08:00',
    title: '投切动作完成',
    detail: '自动投入 B 相分补 #2',
    tone: 'success',
    tag: '控制',
  },
]

describe('CompensationCurveAnalysisAside', () => {
  it('renders curve conclusion, current summary, related events, thresholds and data quality', () => {
    const wrapper = mount(CompensationCurveAnalysisAside, {
      props: {
        telemetry,
        history,
        controlProfile,
        alarms,
        events,
        timeRange: [new Date('2026-05-21T09:00:00+08:00'), new Date('2026-05-21T10:00:00+08:00')],
      },
    })

    expect(wrapper.text()).toContain('曲线分析助手')
    expect(wrapper.text()).toContain('分析结论')
    expect(wrapper.text()).toContain('当前曲线摘要')
    expect(wrapper.text()).toContain('关联事件')
    expect(wrapper.text()).toContain('分析基准与数据质量')
    expect(wrapper.text()).toContain('5次 / 2.8%')
    expect(wrapper.text()).toContain('PF 目标')
    expect(wrapper.text()).toContain('≥ 0.95')
    expect(wrapper.text()).toContain('电压谐波门限')
    expect(wrapper.text()).toContain('5.0%')
    expect(wrapper.text()).toContain('采样点数')
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('A 相电压谐波超限')
    expect(wrapper.text()).toContain('投切动作完成')
    expect(wrapper.text()).not.toContain('通讯恢复')
  })

  it('normalizes register-style threshold values before rendering analysis baselines', () => {
    const wrapper = mount(CompensationCurveAnalysisAside, {
      props: {
        telemetry,
        history,
        controlProfile: {
          ...controlProfile,
          switch_on_power_factor: 90,
          current_harmonic_threshold: 80,
        },
        alarms: [],
        events: [],
        timeRange: null,
      },
    })

    expect(wrapper.text()).toContain('≥ 0.90')
    expect(wrapper.text()).toContain('8.0%')
    expect(wrapper.text()).not.toContain('≥ 90.00')
    expect(wrapper.text()).not.toContain('80.0%')
  })
})
