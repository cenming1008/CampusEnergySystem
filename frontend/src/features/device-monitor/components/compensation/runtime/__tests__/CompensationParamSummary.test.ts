import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationParamSummary from '../CompensationParamSummary.vue'

describe('CompensationParamSummary', () => {
  it('渲染参数键值对', () => {
    const wrapper = mount(CompensationParamSummary, {
      props: {
        items: [
          { label: '目标 PF', value: '0.98（滞后）' },
          { label: '投切延时', value: '30 s' },
        ],
      },
    })
    expect(wrapper.text()).toContain('控制参数')
    expect(wrapper.text()).toContain('目标 PF')
    expect(wrapper.text()).toContain('0.98（滞后）')
  })

  it('点击「修改」emit edit', async () => {
    const wrapper = mount(CompensationParamSummary, {
      props: { items: [] },
    })
    await wrapper.find('[data-test="param-edit"]').trigger('click')
    expect(wrapper.emitted('edit')).toBeTruthy()
  })

  it('无参数时显示空状态', () => {
    const wrapper = mount(CompensationParamSummary, { props: { items: [] } })
    expect(wrapper.text()).toContain('暂无控制参数')
  })
})
