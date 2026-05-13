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
    expect(wrapper.findAll('.strip-cell__value strong').map((node) => node.text())).toContain('--')
    expect(wrapper.text()).not.toContain('✕ 缺测')
  })
})
