import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import DeviceMetricGrid from '../DeviceMetricGrid.vue'

describe('DeviceMetricGrid', () => {
  it('renders backend metric cards with precision and missing state', () => {
    const wrapper = mount(DeviceMetricGrid, {
      props: {
        metrics: [
          { key: 'pressure', label: '压力', value: 0.333, unit: 'MPa', precision: 2, state: 'live' },
          { key: 'voltage', label: '电压', value: null, unit: 'V', precision: 1, state: 'missing' },
        ],
      },
    })

    expect(wrapper.text()).toContain('压力')
    expect(wrapper.text()).toContain('0.33')
    expect(wrapper.text()).toContain('MPa')
    expect(wrapper.text()).toContain('电压')
    expect(wrapper.text()).toContain('--')
  })

  it('renders empty state when no metric cards are available', () => {
    const wrapper = mount(DeviceMetricGrid, {
      props: {
        metrics: [],
      },
    })

    expect(wrapper.text()).toContain('暂无指标数据')
  })

  it('keeps long labels and empty units readable', () => {
    const wrapper = mount(DeviceMetricGrid, {
      props: {
        metrics: [
          {
            key: 'long_label',
            label: '很长很长的设备侧监控指标名称',
            value: 1,
            unit: null,
            precision: 0,
            state: 'live',
          },
        ],
      },
    })

    expect(wrapper.text()).toContain('很长很长的设备侧监控指标名称')
    expect(wrapper.text()).toContain('1')
  })
})
