import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import DeviceTrendPanel from '../DeviceTrendPanel.vue'

describe('DeviceTrendPanel', () => {
  it('renders supported trend fields and hides unsupported fields', () => {
    const wrapper = mount(DeviceTrendPanel, {
      props: {
        modelValue: 'consumption',
        timeRange: null,
        fields: [
          { key: 'consumption', label: '累计读数', unit: 'm³', precision: 1 },
          { key: 'voltage', label: '电压', unit: 'V', precision: 1 },
          { key: 'pressure', label: '不支持趋势', unit: 'MPa', precision: 2 },
        ],
        summary: {
          latest: null,
          peak: null,
          average: null,
          valley: null,
        },
        unit: 'm³',
        loading: false,
      },
      global: {
        stubs: {
          MonitorSectionPanel: {
            template: '<section><slot name="headerExtra" /><slot /></section>',
          },
          'el-radio-group': {
            template: '<div><slot /></div>',
          },
          'el-radio-button': {
            props: ['value'],
            template: '<button><slot /></button>',
          },
          'el-date-picker': true,
        },
        directives: {
          loading: () => undefined,
        },
      },
    })

    expect(wrapper.text()).toContain('累计读数')
    expect(wrapper.text()).toContain('电压')
    expect(wrapper.text()).not.toContain('不支持趋势')
  })

  it('shows empty state when no supported trend fields are available', () => {
    const wrapper = mount(DeviceTrendPanel, {
      props: {
        modelValue: 'flow_rate',
        timeRange: null,
        fields: [
          { key: 'pressure', label: '压力', unit: 'MPa', precision: 2 },
        ],
        summary: {
          latest: null,
          peak: null,
          average: null,
          valley: null,
        },
        unit: '',
        loading: false,
      },
      global: {
        stubs: {
          MonitorSectionPanel: {
            template: '<section><slot name="headerExtra" /><slot /></section>',
          },
          'el-date-picker': true,
        },
        directives: {
          loading: () => undefined,
        },
      },
    })

    expect(wrapper.text()).toContain('暂无可用趋势字段')
  })
})
