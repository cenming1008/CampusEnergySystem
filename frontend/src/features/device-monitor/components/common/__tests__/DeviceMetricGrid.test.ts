import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import DeviceMetricGrid from '../DeviceMetricGrid.vue'

describe('DeviceMetricGrid', () => {
  it('renders all backend metrics as equal-size generic monitor cards', () => {
    const wrapper = mount(DeviceMetricGrid, {
      props: {
        metrics: [
          { key: 'flow_rate', label: '实时功率/流量', value: 38.2, unit: 'kW', precision: 1, state: 'live' },
          { key: 'consumption', label: '累计读数', value: 243.874, unit: 'kWh', precision: 2, state: 'live' },
          { key: 'voltage', label: '电压', value: null, unit: 'V', precision: 1, state: 'missing' },
        ],
      },
    })

    const cards = wrapper.findAll('.device-metric-card')
    expect(cards).toHaveLength(3)
    expect(wrapper.find('.device-metric-grid').exists()).toBe(true)
    expect(wrapper.find('.device-metric-bento__hero').exists()).toBe(false)
    expect(wrapper.find('.device-metric-bento__focus').exists()).toBe(false)
    expect(cards[0].text()).toContain('实时功率/流量')
    expect(cards[0].text()).toContain('38.2')
    expect(cards[1].text()).toContain('累计读数')
    expect(cards[1].text()).toContain('243.87')
    expect(cards[1].text()).toContain('kWh')
    expect(cards[2].text()).toContain('电压')
    expect(cards[2].text()).toContain('--')
  })

  it('keeps voltage, current, pressure and temperature in the same parallel card layout', () => {
    const wrapper = mount(DeviceMetricGrid, {
      props: {
        metrics: [
          { key: 'flow_rate', label: '实时功率/流量', value: 38.2, unit: 'kW', precision: 1, state: 'live' },
          { key: 'consumption', label: '累计读数', value: 243.874, unit: 'kWh', precision: 2, state: 'live' },
          { key: 'voltage', label: '电压', value: null, unit: 'V', precision: 1, state: 'missing' },
          { key: 'temperature', label: '温度', value: 21.52, unit: 'degC', precision: 1, state: 'live' },
        ],
      },
    })

    const cards = wrapper.findAll('.device-metric-card')
    expect(cards).toHaveLength(4)
    expect(cards.every((card) => card.classes().includes('device-metric-card'))).toBe(true)
    expect(wrapper.text()).toContain('电压')
    expect(wrapper.text()).toContain('--')
    expect(wrapper.text()).toContain('温度')
    expect(wrapper.text()).toContain('21.5')
    expect(wrapper.text()).toContain('degC')
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
    expect(wrapper.findAll('.device-metric-card')).toHaveLength(1)
  })
})
