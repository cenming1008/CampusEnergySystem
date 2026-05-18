import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import CompensationDetailPanel from '../CompensationDetailPanel.vue'

describe('CompensationDetailPanel', () => {
  it('switches capacitor banks between circuit state and three-phase measurements', async () => {
    const wrapper = mount(CompensationDetailPanel, {
      props: {
        isCapacitorBank: true,
        activeTab: 'circuit',
      },
      global: {
        stubs: {
          CompensationThreePhasePanel: {
            template: '<section class="threephase-probe">三相量测</section>',
          },
          CompensationCircuitStatePanel: {
            template: '<section class="circuit-probe">回路状态</section>',
          },
          'el-segmented': {
            props: ['options', 'modelValue'],
            emits: ['change'],
            template: `
              <div class="tab-probe">
                <button
                  v-for="option in options"
                  :key="option.value"
                  type="button"
                  @click="$emit('change', option.value)"
                >
                  {{ option.label }}
                </button>
              </div>
            `,
          },
        },
      },
    })

    const headerText = wrapper.find('.detail-panel__head').text()

    expect(wrapper.find('.detail-panel__intro h3').text()).toBe('实时监测')
    expect(headerText).not.toContain('三相电气量与回路投切状态')
    expect(headerText.indexOf('投入')).toBeGreaterThanOrEqual(0)
    expect(wrapper.find('.tab-probe').exists()).toBe(true)
    expect(wrapper.find('.tab-probe').text()).toContain('回路状态')
    expect(wrapper.find('.tab-probe').text()).toContain('三相量测')
    expect(wrapper.find('.circuit-probe').exists()).toBe(true)
    expect(wrapper.find('.threephase-probe').exists()).toBe(false)

    await wrapper.findAll('.tab-probe button')[1].trigger('click')
    await wrapper.setProps({ activeTab: 'three-phase' })

    expect(wrapper.emitted('update:activeTab')?.[0]).toEqual(['three-phase'])
    expect(wrapper.find('.circuit-probe').exists()).toBe(false)
    expect(wrapper.find('.threephase-probe').exists()).toBe(true)
  })

  it('keeps non-capacitor devices on the three-phase measurement path', () => {
    const wrapper = mount(CompensationDetailPanel, {
      props: {
        isCapacitorBank: false,
        activeTab: 'three-phase',
      },
      global: {
        stubs: {
          CompensationThreePhasePanel: {
            template: '<section class="threephase-probe">三相量测</section>',
          },
          CompensationCircuitStatePanel: {
            template: '<section class="circuit-probe">回路状态</section>',
          },
          'el-segmented': {
            props: ['options'],
            template: '<div><span v-for="option in options" :key="option.value">{{ option.label }}</span></div>',
          },
        },
      },
    })

    const headerText = wrapper.find('.detail-panel__head').text()

    expect(headerText).not.toContain('投入')
    expect(headerText).not.toContain('切除')
    expect(headerText).not.toContain('未配置')
    expect(headerText).not.toContain('等待回读')
    expect(wrapper.find('.threephase-probe').exists()).toBe(true)
    expect(wrapper.find('.circuit-probe').exists()).toBe(false)
  })
})
