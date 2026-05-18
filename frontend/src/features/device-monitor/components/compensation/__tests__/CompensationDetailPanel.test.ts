import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import CompensationDetailPanel from '../CompensationDetailPanel.vue'

describe('CompensationDetailPanel', () => {
  it('renames realtime detail, removes the subtitle, and places circuit legend before the tabs', () => {
    const wrapper = mount(CompensationDetailPanel, {
      props: {
        isCapacitorBank: true,
        activeTab: 'circuit',
      },
      global: {
        stubs: {
          CompensationThreePhasePanel: true,
          CompensationCircuitStatePanel: true,
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

    expect(wrapper.find('.detail-panel__intro h3').text()).toBe('实时监测')
    expect(headerText).not.toContain('三相电气量与回路投切状态')
    expect(headerText.indexOf('投入')).toBeGreaterThanOrEqual(0)
    expect(headerText.indexOf('投入')).toBeLessThan(headerText.indexOf('回路状态'))
    expect(headerText.indexOf('等待回读')).toBeLessThan(headerText.indexOf('回路状态'))
  })

  it('hides the circuit legend while three-phase measurement is selected', () => {
    const wrapper = mount(CompensationDetailPanel, {
      props: {
        isCapacitorBank: true,
        activeTab: 'three-phase',
      },
      global: {
        stubs: {
          CompensationThreePhasePanel: true,
          CompensationCircuitStatePanel: true,
          'el-segmented': {
            props: ['options'],
            template: '<div><span v-for="option in options" :key="option.value">{{ option.label }}</span></div>',
          },
        },
      },
    })

    const headerText = wrapper.find('.detail-panel__head').text()

    expect(headerText).toContain('三相量测')
    expect(headerText).not.toContain('投入')
    expect(headerText).not.toContain('切除')
    expect(headerText).not.toContain('未配置')
    expect(headerText).not.toContain('等待回读')
  })
})
