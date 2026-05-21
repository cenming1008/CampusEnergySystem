import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationAlarmRail from '../CompensationAlarmRail.vue'
import type { DeviceAlarmRecord } from '@/api/deviceMonitor'

function makeAlarm(id: number, isResolved = false): DeviceAlarmRecord {
  return {
    id,
    device_id: 1,
    message: `告警 ${id}`,
    severity: id === 1 ? 'critical' : 'warning',
    timestamp: `2026-05-19T12:${String(id).padStart(2, '0')}:00+08:00`,
    is_resolved: isResolved,
  }
}

describe('CompensationAlarmRail', () => {
  it('只渲染未处理告警并显示数量', () => {
    const wrapper = mount(CompensationAlarmRail, {
      props: { rows: [makeAlarm(1), makeAlarm(2), makeAlarm(3, true)], actionId: null },
    })
    expect(wrapper.text()).toContain('未处理告警')
    expect(wrapper.text()).toContain('2 待处理')
    expect(wrapper.findAll('[data-test="alarm-rail-item"]')).toHaveLength(2)
  })

  it('超过 5 条未处理告警时列表保持全部渲染但使用 5 条可视高度滚动', () => {
    const rows = Array.from({ length: 8 }, (_, index) => makeAlarm(index + 1))
    const wrapper = mount(CompensationAlarmRail, {
      props: { rows, actionId: null },
    })
    const body = wrapper.find('[data-test="alarm-rail-scroll"]')

    expect(wrapper.findAll('[data-test="alarm-rail-item"]')).toHaveLength(8)
    expect(body.classes()).toContain('rail-body--scrollable')
    expect(body.attributes('style')).toContain('--rail-visible-rows: 5')
  })

  it('点击处理按钮 emit resolve', async () => {
    const wrapper = mount(CompensationAlarmRail, {
      props: { rows: [makeAlarm(1)], actionId: null },
    })
    await wrapper.find('[data-test="alarm-resolve"]').trigger('click')
    expect(wrapper.emitted('resolve')?.[0]?.[0]).toEqual(expect.objectContaining({ id: 1 }))
  })

  it('无未处理告警时显示空状态', () => {
    const wrapper = mount(CompensationAlarmRail, {
      props: { rows: [makeAlarm(1, true)], actionId: null },
    })
    expect(wrapper.text()).toContain('暂无未处理告警')
  })

  it('点击"查看全部"footer emit view-all 且 rows 为空时不显示', async () => {
    const wrapper = mount(CompensationAlarmRail, {
      props: { rows: [makeAlarm(1), makeAlarm(2)], actionId: null },
    })
    const footer = wrapper.find('[data-test="alarm-view-all"]')
    expect(footer.exists()).toBe(true)
    expect(footer.text()).toContain('查看全部 2 条记录')
    await footer.trigger('click')
    expect(wrapper.emitted('view-all')).toHaveLength(1)

    const emptyWrapper = mount(CompensationAlarmRail, {
      props: { rows: [], actionId: null },
    })
    expect(emptyWrapper.find('[data-test="alarm-view-all"]').exists()).toBe(false)
  })
})
