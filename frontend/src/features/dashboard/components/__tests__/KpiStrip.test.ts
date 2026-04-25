import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import KpiStrip from '../KpiStrip.vue'

describe('KpiStrip', () => {
  it('labels device totals as enabled devices rather than online devices', () => {
    const wrapper = mount(KpiStrip, {
      props: {
        currentLoad: 12,
        onlineCount: 2,
        totalCount: 3,
        alarmCount: 0,
        todayEnergy: 42,
        monthlyEnergy: 420,
        shift: '白班',
      },
    })

    expect(wrapper.text()).toContain('启用设备')
    expect(wrapper.text()).toContain('启用率 67%')
    expect(wrapper.text()).not.toContain('在线设备')
    expect(wrapper.text()).not.toContain('在线率')
  })
})
