import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PanelCollapseToggle from '../PanelCollapseToggle.vue'

describe('PanelCollapseToggle', () => {
  it('点击时派发 toggle 事件', async () => {
    const wrapper = mount(PanelCollapseToggle, {
      props: { collapsed: false },
      global: { stubs: { 'el-icon': { template: '<i><slot /></i>' } } },
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('toggle')).toHaveLength(1)
  })

  it('折叠态 aria-expanded 为 false，展开态为 true', () => {
    const collapsedWrapper = mount(PanelCollapseToggle, {
      props: { collapsed: true },
      global: { stubs: { 'el-icon': { template: '<i><slot /></i>' } } },
    })
    expect(collapsedWrapper.find('button').attributes('aria-expanded')).toBe('false')

    const expandedWrapper = mount(PanelCollapseToggle, {
      props: { collapsed: false },
      global: { stubs: { 'el-icon': { template: '<i><slot /></i>' } } },
    })
    expect(expandedWrapper.find('button').attributes('aria-expanded')).toBe('true')
  })
})
