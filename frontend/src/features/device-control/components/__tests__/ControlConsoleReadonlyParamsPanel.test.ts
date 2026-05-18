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
    { label: '公补 1-3', value: '30.0 kvar / 60.0 kvar / 90.0 kvar' },
  ],
  groupedParameters: [
    {
      key: 'strategy',
      label: '投切策略',
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
    {
      key: 'circuits',
      label: '回路配置',
      items: [
        {
          key: 'common_output_circuit_count',
          label: '共补输出回路',
          description: '共补输出路数配置。',
          currentValue: '12',
          register: '0xD6',
          readWrite: '读/写',
        },
      ],
    },
    {
      key: 'protection',
      label: '保护门限',
      items: [
        {
          key: 'overvoltage_threshold',
          label: '过压保护门限',
          description: '过压保护触发门限。',
          currentValue: '245 V',
          register: '0xDD',
          readWrite: '读/写',
        },
      ],
    },
    {
      key: 'device',
      label: '通讯参数',
      items: [
        {
          key: 'baud_rate',
          label: '通讯速率',
          description: '控制器通讯波特率。',
          currentValue: '9600 bps',
          register: '0xE2',
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
  it('shows compact summary with capacity and parameter details by default', () => {
    const wrapper = mountPanel()

    expect(wrapper.findAll('.readonly-summary-card')).toHaveLength(6)
    expect(wrapper.text()).toContain('投入功率因数')
    expect(wrapper.text()).toContain('2026-04-22 18:10:00')
    expect(wrapper.text()).not.toContain('来源：telemetry')
    expect(wrapper.text()).not.toContain('快照：')
    expect(wrapper.text()).not.toContain('只读参数快照')
    expect(wrapper.find('.capacity-expansion-panel').exists()).toBe(true)
    expect(wrapper.find('.param-groups').exists()).toBe(true)
    expect(wrapper.find('[data-test="toggle-capacity"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="toggle-parameters"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('容量展开详情展开')
    expect(wrapper.text()).not.toContain('全部参数明细展开')
  })

  it('shows parameter groups side by side with only parameter names and values', () => {
    const wrapper = mountPanel()

    expect(wrapper.findAll('[data-test="param-group-tab"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="param-group-card"]')).toHaveLength(4)
    expect(wrapper.text()).toContain('投切策略')
    expect(wrapper.text()).toContain('回路配置')
    expect(wrapper.text()).toContain('保护门限')
    expect(wrapper.text()).toContain('通讯参数')
    expect(wrapper.text()).toContain('投入功率因数')
    expect(wrapper.text()).toContain('共补输出回路')
    expect(wrapper.text()).toContain('过压保护门限')
    expect(wrapper.text()).toContain('通讯速率')

    expect(wrapper.text()).not.toContain('寄存器')
    expect(wrapper.text()).not.toContain('0xD2')
    expect(wrapper.text()).not.toContain('读/写')
    expect(wrapper.text()).not.toContain('低于该功率因数时投入电容。')
    expect(wrapper.text()).not.toContain('共补输出路数配置。')
  })

  it('shows capacity expansion as circuit-to-capacity pairs', () => {
    const wrapper = mountPanel()

    const slots = wrapper.findAll('[data-test="capacity-slot"]')
    expect(slots).toHaveLength(6)
    expect(slots[0].text()).toContain('A1')
    expect(slots[0].text()).toContain('5.0 kvar')
    expect(slots[2].text()).toContain('A3')
    expect(slots[2].text()).toContain('10.0 kvar')
    expect(slots[3].text()).toContain('1路')
    expect(slots[3].text()).toContain('30.0 kvar')
    expect(slots[5].text()).toContain('3路')
    expect(slots[5].text()).toContain('90.0 kvar')
    expect(wrapper.text()).not.toContain('30.0 kvar / 60.0 kvar / 90.0 kvar')
  })
})
