import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import DeviceTemplateDiagnosticsPanel from '../DeviceTemplateDiagnosticsPanel.vue'
import type { MonitorTemplateDiagnostics } from '@/api/deviceMonitor'

function diagnostics(overrides: Partial<MonitorTemplateDiagnostics> = {}): MonitorTemplateDiagnostics {
  return {
    template_key: 'water_meter',
    display_name: '水表',
    category: 'water_meter',
    subtype: null,
    metric_coverage: {
      total: 4,
      live: 4,
      missing: 0,
      missing_keys: [],
    },
    trend_coverage: {
      declared_keys: ['flow_rate', 'consumption', 'pressure', 'temperature'],
      drawable_keys: ['flow_rate', 'consumption'],
      unsupported_keys: ['pressure', 'temperature'],
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
    overall_status: 'passed',
    ...overrides,
  }
}

describe('DeviceTemplateDiagnosticsPanel', () => {
  it('renders passed status and template coverage', () => {
    const wrapper = mount(DeviceTemplateDiagnosticsPanel, {
      props: {
        diagnostics: diagnostics(),
      },
    })

    expect(wrapper.text()).toContain('接入诊断')
    expect(wrapper.text()).toContain('水表')
    expect(wrapper.text()).toContain('接入完整')
    expect(wrapper.text()).toContain('4/4')
    expect(wrapper.text()).toContain('flow_rate')
    expect(wrapper.text()).toContain('pressure')
  })

  it('renders partial, missing, and offline status labels', () => {
    const partial = mount(DeviceTemplateDiagnosticsPanel, {
      props: {
        diagnostics: diagnostics({
          overall_status: 'partial',
          metric_coverage: {
            total: 4,
            live: 3,
            missing: 1,
            missing_keys: ['temperature'],
          },
        }),
      },
    })
    expect(partial.text()).toContain('部分接入')
    expect(partial.text()).toContain('temperature')

    const missing = mount(DeviceTemplateDiagnosticsPanel, {
      props: {
        diagnostics: diagnostics({
          overall_status: 'missing',
          metric_coverage: {
            total: 4,
            live: 0,
            missing: 4,
            missing_keys: ['flow_rate', 'consumption', 'pressure', 'temperature'],
          },
        }),
      },
    })
    expect(missing.text()).toContain('指标缺失')

    const offline = mount(DeviceTemplateDiagnosticsPanel, {
      props: {
        diagnostics: diagnostics({
          overall_status: 'offline',
          ingestion_health: {
            ingestion_status: 'offline',
            is_online: false,
            last_message_at: null,
            last_success_at: null,
          },
        }),
      },
    })
    expect(offline.text()).toContain('采集离线')
    expect(offline.text()).toContain('当前按最后一次可用模板结果展示接入检查')
  })

  it('renders capacitor bank missing fields as an operator-readable checklist', () => {
    const wrapper = mount(DeviceTemplateDiagnosticsPanel, {
      props: {
        diagnostics: diagnostics({
          template_key: 'capacitor_bank_controller',
          display_name: '电容补偿控制器',
          overall_status: 'offline',
          metric_coverage: {
            total: 6,
            live: 0,
            missing: 6,
            missing_keys: [
              'reactive_power',
              'power_factor',
              'voltage',
              'current',
              'running_circuit_count',
              'capacity_utilization',
            ],
          },
          panel_coverage: {
            specific_panels: ['three_phase', 'circuit_state', 'control_profile', 'control_summary'],
          },
          ingestion_health: {
            ingestion_status: 'offline',
            is_online: false,
            last_message_at: null,
            last_success_at: null,
          },
        }),
      },
    })

    expect(wrapper.text()).toContain('采集状态')
    expect(wrapper.text()).toContain('等待字段')
    expect(wrapper.text()).toContain('无功功率（reactive_power）')
    expect(wrapper.text()).toContain('功率因数（power_factor）')
    expect(wrapper.text()).toContain('母线电压（voltage）')
    expect(wrapper.text()).toContain('线电流（current）')
    expect(wrapper.text()).toContain('投入回路（running_circuit_count）')
    expect(wrapper.text()).toContain('容量利用率（capacity_utilization）')
    expect(wrapper.text()).toContain('三相快照（three_phase）')
  })

  it('keeps long template keys readable and falls back when missing keys are inconsistent', () => {
    const wrapper = mount(DeviceTemplateDiagnosticsPanel, {
      props: {
        diagnostics: diagnostics({
          template_key: 'capacitor_bank_controller',
          display_name: '电容补偿控制器',
          metric_coverage: {
            total: 6,
            live: 3,
            missing: 3,
            missing_keys: [],
          },
          trend_coverage: {
            declared_keys: ['reactive_power', 'power_factor', 'voltage', 'current'],
            drawable_keys: ['reactive_power', 'power_factor', 'voltage', 'current'],
            unsupported_keys: [],
          },
          panel_coverage: {
            specific_panels: ['three_phase', 'circuit_state', 'control_profile', 'control_summary'],
          },
          overall_status: 'offline',
        }),
      },
    })

    expect(wrapper.find('.template-diagnostics__item--template').exists()).toBe(true)
    expect(wrapper.text()).toContain('capacitor_bank_controller')
    expect(wrapper.text()).toContain('3/6')
    expect(wrapper.text()).toContain('缺失字段待后端确认')
    expect(wrapper.text()).toContain('three_phase')
    expect(wrapper.text()).toContain('control_summary')
  })
})
