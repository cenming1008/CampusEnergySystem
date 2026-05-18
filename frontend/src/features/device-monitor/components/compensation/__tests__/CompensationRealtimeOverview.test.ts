import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import CompensationRealtimeOverview from '../CompensationRealtimeOverview.vue'

const metric = {
  key: 'reactivePower',
  label: '当前无功功率',
  value: '暂无数据',
  unit: 'kVar',
  hint: '实时值缺失',
  state: 'missing' as const,
}

describe('CompensationRealtimeOverview', () => {
  it('renders a calm waiting-for-telemetry state when all realtime metrics are unavailable', () => {
    const wrapper = mount(CompensationRealtimeOverview, {
      props: {
        coreMetric: metric,
        pfMetric: {
          key: 'powerFactor',
          label: '功率因数',
          value: '暂无数据',
          unit: 'PF',
          hint: '实时值缺失',
          state: 'missing',
        },
        metrics: [
          { key: 'voltage', label: '母线电压', value: '通讯中断', unit: 'V', hint: '', state: 'missing' },
          { key: 'current', label: '线电流', value: '通讯中断', unit: 'A', hint: '', state: 'missing' },
          { key: 'activePower', label: '有功功率', value: '暂无数据', unit: 'kW', hint: '', state: 'missing' },
          { key: 'capacityUsage', label: '容量利用率', value: '0.0', unit: '%', hint: '', state: 'mock' },
          { key: 'controlMode', label: '控制模式', value: '自动', hint: '', state: 'mock' },
          { key: 'cabinetTemperature', label: '柜内温度', value: '暂无数据', unit: '°C', hint: '', state: 'missing' },
        ],
        moduleStatus: {
          title: '回路',
          unitLabel: '回路',
          runningModuleCount: 0,
          totalModuleCount: 24,
          moduleStates: [],
          hint: '',
        },
        extendedHint: '',
      },
      global: {
        stubs: {
          'el-progress': {
            template: '<div class="progress-probe"><slot /></div>',
          },
          'el-tooltip': {
            template: '<span><slot /></span>',
          },
          'el-tag': {
            template: '<span class="tag-probe"><slot /></span>',
          },
        },
      },
    })

    expect(wrapper.text()).toContain('等待设备上报实时遥测')
    expect(wrapper.text()).toContain('收到首包数据后将自动显示补偿效果')
    expect(wrapper.find('.bento-hero__value').text()).toContain('等待采集')
    expect(wrapper.text()).not.toContain('✕ 缺测')
  })

  it('renders PF trend axes as a one-day power factor view', () => {
    const wrapper = mount(CompensationRealtimeOverview, {
      props: {
        coreMetric: {
          key: 'reactivePower',
          label: '当前无功功率',
          value: '-12.0',
          unit: 'kVar',
          hint: '',
          state: 'live',
        },
        pfMetric: {
          key: 'powerFactor',
          label: '功率因数',
          value: '0.96',
          unit: 'PF',
          hint: '',
          state: 'live',
        },
        metrics: [
          { key: 'voltage', label: '母线电压', value: '220.0', unit: 'V', hint: '', state: 'live' },
        ],
        pfTrend: {
          values: [0.91, 0.96, 0.94],
          timestamps: ['2026-05-18T09:00:00+08:00', '2026-05-18T09:10:00+08:00', '2026-05-18T09:20:00+08:00'],
          target: 0.95,
        },
        extendedHint: '',
      },
      global: {
        stubs: {
          'el-tooltip': {
            template: '<span><slot /></span>',
          },
          'el-tag': {
            template: '<span class="tag-probe"><slot /></span>',
          },
        },
      },
    })

    expect(wrapper.findAll('.bento-hero__spark-axis')).toHaveLength(2)
    expect(wrapper.findAll('.bento-hero__spark-x-labels span').map((node) => node.text())).toEqual([
      '00:00',
      '06:00',
      '12:00',
      '18:00',
      '24:00',
    ])
    expect(wrapper.findAll('.bento-hero__spark-tick')).toHaveLength(25)
    expect(wrapper.find('.bento-hero__spark-y-title').exists()).toBe(false)
    expect(wrapper.text()).toContain('近一天功率因数趋势')
  })
})
