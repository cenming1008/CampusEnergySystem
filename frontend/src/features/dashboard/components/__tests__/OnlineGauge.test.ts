import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import OnlineGauge from '../OnlineGauge.vue'

describe('OnlineGauge', () => {
  it('uses enabled/disabled copy when counts come from device management state', () => {
    const wrapper = mount(OnlineGauge, {
      props: {
        onlineCount: 2,
        offlineCount: 1,
        totalCount: 3,
        onlineRate: 67,
      },
    })

    expect(wrapper.text()).toContain('设备启用总览')
    expect(wrapper.text()).toContain('启用设备')
    expect(wrapper.text()).toContain('停用设备')
    expect(wrapper.text()).not.toContain('设备在线总览')
    expect(wrapper.text()).not.toContain('在线设备')
    expect(wrapper.text()).not.toContain('离线设备')
  })
})
