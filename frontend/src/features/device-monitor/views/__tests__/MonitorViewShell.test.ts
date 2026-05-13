import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import MonitorViewShell from '../MonitorViewShell.vue'

describe('MonitorViewShell', () => {
  it('renders header, main, and side slots in the shared monitor layout', () => {
    const wrapper = mount(MonitorViewShell, {
      slots: {
        header: '<div class="header-slot">设备标题</div>',
        main: '<div class="main-slot">核心指标</div>',
        side: '<div class="side-slot">接入诊断</div>',
      },
    })

    expect(wrapper.find('.monitor-view-shell__header .header-slot').exists()).toBe(true)
    expect(wrapper.find('.monitor-view-shell__main .main-slot').exists()).toBe(true)
    expect(wrapper.find('.monitor-view-shell__side .side-slot').exists()).toBe(true)
  })

  it('keeps the main layout usable when the side slot is absent', () => {
    const wrapper = mount(MonitorViewShell, {
      slots: {
        header: '<div class="header-slot">设备标题</div>',
        main: '<div class="main-slot">核心指标</div>',
      },
    })

    expect(wrapper.find('.monitor-view-shell').classes()).toContain('monitor-view-shell--main-only')
    expect(wrapper.find('.monitor-view-shell__main .main-slot').exists()).toBe(true)
    expect(wrapper.find('.monitor-view-shell__side').exists()).toBe(false)
  })
})
