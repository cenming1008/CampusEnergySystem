import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import CompensationControlSummaryPanel from '../CompensationControlSummaryPanel.vue'

describe('CompensationControlSummaryPanel', () => {
  it('shows an explicit parameter edit entry for capacitor controller thresholds', async () => {
    const wrapper = mount(CompensationControlSummaryPanel, {
      props: {
        summaryItems: [{ label: '过压保护门限', value: '250 V' }],
        capacityExpansionItems: [],
        hasSummaryData: true,
      },
      global: {
        stubs: {
          PanelCollapseToggle: {
            template: '<button type="button" class="collapse-probe" @click="$emit(\'toggle\')">折叠</button>',
            emits: ['toggle'],
          },
        },
      },
    })

    const editButton = wrapper.get('button[aria-label="修改参数"]')
    expect(editButton.text()).toContain('修改参数')

    await editButton.trigger('click')
    expect(wrapper.emitted('open-console')).toHaveLength(1)
  })

  it('shows capacity totals first and keeps per-circuit capacity details collapsed', async () => {
    const wrapper = mount(CompensationControlSummaryPanel, {
      props: {
        summaryItems: [
          { label: '投入功率因数', value: '0.90' },
          { label: '通讯速率', value: '9600 bps' },
        ],
        capacityExpansionItems: [
          { label: 'A相分补', value: '12.0 kvar / 12.0 kvar / 24.0 kvar' },
          { label: '公补 1-8', value: '30.0 kvar / 60.0 kvar' },
        ],
        hasSummaryData: true,
      },
      global: {
        stubs: {
          PanelCollapseToggle: {
            template: '<button type="button" class="collapse-probe" @click="$emit(\'toggle\')">折叠</button>',
            emits: ['toggle'],
          },
        },
      },
    })

    expect(wrapper.text()).toContain('分补合计')
    expect(wrapper.text()).toContain('48.0 kvar')
    expect(wrapper.text()).toContain('公补合计')
    expect(wrapper.text()).toContain('90.0 kvar')
    expect(wrapper.text()).toContain('展开容量明细')
    expect(wrapper.text()).not.toContain('通讯速率')

    await wrapper.get('.capacity-summary__toggle').trigger('click')
    expect(wrapper.text()).toContain('A相回路 1')
    expect(wrapper.text()).toContain('12.0 kvar')
    expect(wrapper.text()).toContain('A相回路 3')
    expect(wrapper.text()).toContain('24.0 kvar')
    expect(wrapper.text()).toContain('公补回路 1')
    expect(wrapper.text()).toContain('30.0 kvar')
    expect(wrapper.text()).toContain('公补回路 2')
    expect(wrapper.text()).toContain('60.0 kvar')
  })
})
