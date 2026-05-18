import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import ControlConsoleReadonlyParamsPanel from '../ControlConsoleReadonlyParamsPanel.vue'
import type {
  ControlConsoleReadonlySectionView,
  ControlConsoleReadonlySummaryView,
} from '@/features/device-control/viewMapping'

const SectionStub = defineComponent({
  props: {
    title: { type: String, default: '' },
    metaText: { type: String, default: '' },
  },
  template: `
    <section class="section-stub">
      <h3>{{ title }}</h3>
      <small>{{ metaText }}</small>
      <slot />
    </section>
  `,
})

const sectionView: ControlConsoleReadonlySectionView = {
  title: '只读参数快照',
  sectionLabel: '只读参数',
  tone: 'readonly',
  tags: [{ text: '最新参数', tone: 'success' }],
  metaText: '来源：telemetry · 快照：2026-04-22 18:10:00',
  showCapacityExpansion: true,
}

const readonlySummaryView: ControlConsoleReadonlySummaryView = {
  sourceStatusText: '最新参数',
  sourceStatusTone: 'success',
  sourceMeta: sectionView.metaText,
  summaryItems: [
    { label: '投入功率因数', value: '92%' },
    { label: '切除功率因数', value: '100%' },
    { label: '投入延时', value: '10 秒' },
    { label: '切除延时', value: '8 秒' },
    { label: '过压保护门限', value: '245 V' },
    { label: '温度上限门限', value: '55 degC' },
    { label: '通讯速率', value: '9600 bps' },
  ],
  capacityExpansionItems: [
    { label: 'A相分补', value: '5.0 kvar / 5.0 kvar / 10.0 kvar' },
  ],
  groupedParameters: [
    {
      key: 'power_factor',
      label: '功率因数',
      items: [
        {
          key: 'switch_on_power_factor',
          label: '投入功率因数',
          description: '低于该功率因数时投入电容。',
          currentValue: '92%',
          register: '0xD2',
          readWrite: '读/写',
        },
      ],
    },
  ],
}

function mountPanel() {
  return mount(ControlConsoleReadonlyParamsPanel, {
    props: {
      sectionView,
      readonlySummaryView,
    },
    global: {
      stubs: {
        ControlConsoleParameterSection: SectionStub,
      },
    },
  })
}

describe('ControlConsoleReadonlyParamsPanel', () => {
  it('shows compact summary first and keeps capacity and parameter details collapsed', async () => {
    const wrapper = mountPanel()

    expect(wrapper.findAll('.readonly-summary-card')).toHaveLength(6)
    expect(wrapper.text()).toContain('投入功率因数')
    expect(wrapper.text()).toContain('2026-04-22 18:10:00')
    expect(wrapper.text()).not.toContain('来源：telemetry')
    expect(wrapper.text()).not.toContain('快照：')
    expect(wrapper.text()).not.toContain('只读参数快照')
    expect(wrapper.find('.capacity-expansion-panel').exists()).toBe(false)
    expect(wrapper.find('.param-groups').exists()).toBe(false)

    await wrapper.get('[data-test="toggle-capacity"]').trigger('click')
    expect(wrapper.find('.capacity-expansion-panel').exists()).toBe(true)

    await wrapper.get('[data-test="toggle-parameters"]').trigger('click')
    expect(wrapper.find('.param-groups').exists()).toBe(true)
  })
})
