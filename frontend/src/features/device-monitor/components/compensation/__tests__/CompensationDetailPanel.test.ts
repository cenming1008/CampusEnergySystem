import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import CompensationDetailPanel from '../CompensationDetailPanel.vue'

describe('CompensationDetailPanel', () => {
  it('places three-phase measurements under circuit state for capacitor banks', () => {
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
            props: ['options'],
            template: `
              <div class="tab-probe">
                <span v-for="option in options" :key="option.value">{{ option.label }}</span>
              </div>
            `,
          },
        },
      },
    })

    const headerText = wrapper.find('.detail-panel__head').text()
    const bodyText = wrapper.find('.detail-panel__body').text()

    expect(wrapper.find('.detail-panel__intro h3').text()).toBe('实时监测')
    expect(headerText).not.toContain('三相电气量与回路投切状态')
    expect(headerText.indexOf('投入')).toBeGreaterThanOrEqual(0)
    expect(headerText).not.toContain('三相量测')
    expect(wrapper.find('.tab-probe').exists()).toBe(false)
    expect(bodyText.indexOf('回路状态')).toBeLessThan(bodyText.indexOf('三相量测'))
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
