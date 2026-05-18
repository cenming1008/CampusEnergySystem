import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import CompensationThreePhasePanel from '../CompensationThreePhasePanel.vue'

describe('CompensationThreePhasePanel', () => {
  it('does not render the bus measurement metric strip', () => {
    const wrapper = mount(CompensationThreePhasePanel, {
      props: {
        isCapacitorBank: true,
        measurementMetrics: [
          { key: 'voltage', label: '母线电压', value: '225.4', unit: 'V', hint: '', state: 'live' },
          { key: 'current', label: '线电流', value: '0.0', unit: 'A', hint: '', state: 'live' },
          { key: 'activePower', label: '有功功率', value: '0.0', unit: 'kW', hint: '', state: 'live' },
          { key: 'gridFrequency', label: '电网频率', value: '50.01', unit: 'Hz', hint: '', state: 'live' },
          { key: 'controlMode', label: '控制模式', value: '手动', hint: '', state: 'live' },
          { key: 'cabinetTemperature', label: '柜内温度', value: '37.2', unit: '°C', hint: '', state: 'live' },
        ],
        capacitorBankTelemetry: {
          device_id: 1,
          timestamp: '2026-05-18T21:10:00+08:00',
          voltage_a: 225.4,
          current_a: 0,
        },
      },
    })

    expect(wrapper.text()).not.toContain('母线测量值')
    expect(wrapper.text()).not.toContain('母线电压')
    expect(wrapper.text()).not.toContain('电网频率')
    expect(wrapper.text()).not.toContain('柜内温度')
    expect(wrapper.text()).toContain('三相电气快照')
    expect(wrapper.text()).toContain('A 相')
  })
})
