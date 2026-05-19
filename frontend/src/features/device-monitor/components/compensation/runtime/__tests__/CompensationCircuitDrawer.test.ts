import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationCircuitDrawer from '../CompensationCircuitDrawer.vue'
import type { CompensationCircuitPick } from '../../types'

const circuit: CompensationCircuitPick = {
  groupLabel: 'A 相分补',
  phase: 'A',
  commonGroup: null,
  index: 1,
  state: 'on',
  phaseAlarm: false,
}

describe('CompensationCircuitDrawer', () => {
  it('渲染回路标题与当前状态', () => {
    const wrapper = mount(CompensationCircuitDrawer, {
      props: { circuit, canControl: true, events: [] },
    })
    expect(wrapper.text()).toContain('A 相分补')
    expect(wrapper.text()).toContain('第 1 路')
    expect(wrapper.text()).toContain('投入运行')
  })

  it('无相关事件时显示空状态', () => {
    const wrapper = mount(CompensationCircuitDrawer, {
      props: { circuit, canControl: true, events: [] },
    })
    expect(wrapper.text()).toContain('暂无该回路的投切记录')
  })

  it('canControl 为 false 时操作按钮禁用', () => {
    const wrapper = mount(CompensationCircuitDrawer, {
      props: { circuit, canControl: false, events: [] },
    })
    const buttons = wrapper.findAll('[data-test="circuit-action"]')
    expect(buttons.every((b) => b.attributes('disabled') !== undefined)).toBe(true)
  })

  it('点击「立即切除」emit switch 含相位与动作', async () => {
    const wrapper = mount(CompensationCircuitDrawer, {
      props: { circuit, canControl: true, events: [] },
    })
    await wrapper.find('[data-test="circuit-action-off"]').trigger('click')
    expect(wrapper.emitted('switch')?.[0]?.[0]).toEqual({
      phase: 'A',
      commonGroup: null,
      action: 'off',
    })
  })

  it('点击遮罩 emit close', async () => {
    const wrapper = mount(CompensationCircuitDrawer, {
      props: { circuit, canControl: true, events: [] },
    })
    await wrapper.find('[data-test="drawer-mask"]').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
