import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import DeviceDiagnosticsSummary from '../DeviceDiagnosticsSummary.vue'

describe('DeviceDiagnosticsSummary', () => {
  it('prefers diagnostics summary over runtime status for ingestion fields', () => {
    const wrapper = mount(DeviceDiagnosticsSummary, {
      props: {
        runtimeStatus: {
          device_id: 1,
          code: 'running',
          label: '运行中',
          is_active: true,
          is_online: false,
          ingestion_status: 'offline',
          unresolved_alarm_count: 2,
        },
        diagnosticsSummary: {
          ingestion_status: 'online',
          is_online: true,
          last_message_at: '2026-04-21T17:00:00',
          last_success_at: '2026-04-21T17:00:00',
        },
      },
    })

    expect(wrapper.text()).toContain('在线采集')
    expect(wrapper.text()).toContain('2 条')
    expect(wrapper.text()).toContain('2026-04-21 17:00:00')
  })

  it('renders safe defaults when runtime and diagnostics are missing', () => {
    const wrapper = mount(DeviceDiagnosticsSummary)

    expect(wrapper.text()).toContain('未知')
    expect(wrapper.text()).toContain('暂无数据')
    expect(wrapper.text()).toContain('0 条')
  })
})
