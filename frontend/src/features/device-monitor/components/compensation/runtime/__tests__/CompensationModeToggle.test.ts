import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationModeToggle from '../CompensationModeToggle.vue'

describe('CompensationModeToggle', () => {
  it('active segment gets is-active class, inactive does not', () => {
    const wrapper = mount(CompensationModeToggle, { props: { mode: 'manual' } })
    expect(wrapper.find('[data-test="mode-manual"]').classes()).toContain('is-active')
    expect(wrapper.find('[data-test="mode-auto"]').classes()).not.toContain('is-active')
  })

  it('clicking the non-active segment emits switch', async () => {
    const wrapper = mount(CompensationModeToggle, { props: { mode: 'auto' } })
    await wrapper.find('[data-test="mode-manual"]').trigger('click')
    expect(wrapper.emitted('switch')).toHaveLength(1)
  })

  it('clicking the already-active segment does NOT emit switch', async () => {
    const wrapper = mount(CompensationModeToggle, { props: { mode: 'auto' } })
    await wrapper.find('[data-test="mode-auto"]').trigger('click')
    expect(wrapper.emitted('switch')).toBeFalsy()
  })

  it('when disabled, clicking the non-active segment does NOT emit switch', async () => {
    const wrapper = mount(CompensationModeToggle, {
      props: { mode: 'auto', disabled: true, disabledReason: '当前不可切换' },
    })
    await wrapper.find('[data-test="mode-manual"]').trigger('click')
    expect(wrapper.emitted('switch')).toBeFalsy()
  })
})
