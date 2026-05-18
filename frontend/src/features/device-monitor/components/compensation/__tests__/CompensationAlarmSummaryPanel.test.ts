import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import type { DeviceAlarmRecord } from '@/api/deviceMonitor'
import CompensationAlarmSummaryPanel from '../CompensationAlarmSummaryPanel.vue'

function makeAlarm(id: number, isResolved = false): DeviceAlarmRecord {
  return {
    id,
    device_id: 1,
    message: `告警 ${id}`,
    severity: id === 1 ? 'critical' : 'warning',
    timestamp: `2026-05-18T12:${String(id).padStart(2, '0')}:00+08:00`,
    is_resolved: isResolved,
  }
}

function mountPanel(rows: DeviceAlarmRecord[]) {
  return mount(CompensationAlarmSummaryPanel, {
    props: { rows, actionId: null },
    global: {
      stubs: {
        'el-button': {
          props: ['loading'],
          template: '<button><slot /></button>',
        },
      },
    },
  })
}

describe('CompensationAlarmSummaryPanel', () => {
  it('renders a compact scrollable latest 50 alarm list with unresolved count', () => {
    const wrapper = mountPanel([
      ...Array.from({ length: 52 }, (_, index) => makeAlarm(index + 1)),
      makeAlarm(53, true),
    ])

    expect(wrapper.text()).toContain('告警记录')
    expect(wrapper.text()).toContain('52 未处理')
    expect(wrapper.findAll('.alarm-summary-item')).toHaveLength(50)
    const titles = wrapper.findAll('.alarm-summary-item__title span').map(item => item.text())
    expect(titles).toContain('告警 1')
    expect(titles).toContain('告警 50')
    expect(titles).not.toContain('告警 51')
  })

  it('emits resolve for unresolved alarms and marks resolved alarms as handled', async () => {
    const wrapper = mountPanel([makeAlarm(1), makeAlarm(2, true)])

    await wrapper.find('button').trigger('click')

    expect(wrapper.emitted('resolve')?.[0]).toEqual([expect.objectContaining({ id: 1 })])
    expect(wrapper.text()).toContain('已处理')
  })
})
