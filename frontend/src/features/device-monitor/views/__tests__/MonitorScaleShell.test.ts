import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import MonitorScaleShell from '../MonitorScaleShell.vue'

class ResizeObserverStub {
  observe = vi.fn()
  disconnect = vi.fn()
}

describe('MonitorScaleShell', () => {
  beforeEach(() => {
    vi.stubGlobal('ResizeObserver', ResizeObserverStub)
  })

  it('scales the monitor canvas from the available width while preserving height', async () => {
    const wrapper = mount(MonitorScaleShell, {
      props: {
        baseWidth: 1680,
        minScale: 0.6,
        maxScale: 1.22,
      },
      slots: {
        default: '<section class="probe-panel">监控内容</section>',
      },
    })

    const shell = wrapper.find('.monitor-scale-shell').element as HTMLElement
    const canvas = wrapper.find('.monitor-scale-shell__canvas').element as HTMLElement

    Object.defineProperty(shell, 'clientWidth', { configurable: true, value: 1008 })
    Object.defineProperty(canvas, 'scrollHeight', { configurable: true, value: 1200 })

    window.dispatchEvent(new Event('resize'))
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.monitor-scale-shell__canvas').attributes('style')).toContain('width: 1680px')
    expect(wrapper.find('.monitor-scale-shell__canvas').attributes('style')).toContain('scale(0.6)')
    expect(wrapper.find('.monitor-scale-shell').attributes('style')).toContain('min-height: 720px')
  })

  it('caps large desktop scaling so the page does not over-expand', async () => {
    const wrapper = mount(MonitorScaleShell, {
      props: {
        baseWidth: 1680,
        minScale: 0.6,
        maxScale: 1.22,
      },
      slots: {
        default: '<section class="probe-panel">监控内容</section>',
      },
    })

    const shell = wrapper.find('.monitor-scale-shell').element as HTMLElement
    const canvas = wrapper.find('.monitor-scale-shell__canvas').element as HTMLElement

    Object.defineProperty(shell, 'clientWidth', { configurable: true, value: 2400 })
    Object.defineProperty(canvas, 'scrollHeight', { configurable: true, value: 1000 })

    window.dispatchEvent(new Event('resize'))
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.monitor-scale-shell__canvas').attributes('style')).toContain('scale(1.22)')
    expect(wrapper.find('.monitor-scale-shell').attributes('style')).toContain('min-height: 1220px')
  })
})
