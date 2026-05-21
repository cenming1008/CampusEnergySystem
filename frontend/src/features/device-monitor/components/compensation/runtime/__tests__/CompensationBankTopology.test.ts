import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationBankTopology from '../CompensationBankTopology.vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

function telemetry(overrides: Partial<CompensationCapacitorBankTelemetry> = {}): CompensationCapacitorBankTelemetry {
  return {
    device_id: 1,
    timestamp: '2026-05-19T10:00:00+08:00',
    // A 相：第 1 路投入（bit0），其余切除
    circuit_state_phase_a: 0b00000001,
    circuit_state_phase_b: 0b00000110,
    circuit_state_phase_c: 0b00000010,
    circuit_state_common_1: 0,
    circuit_state_common_2: 0,
    circuit_state_common_3: 0,
    overvoltage_alarm_a: false,
    overvoltage_alarm_b: false,
    overvoltage_alarm_c: false,
    ...overrides,
  } as CompensationCapacitorBankTelemetry
}

const profile = {
  splitCircuitCount: 24,
  commonCircuitCount: 24,
  phaseACircuitTotalCount: 8,
  phaseBCircuitTotalCount: 8,
  phaseCCircuitTotalCount: 8,
  common1CircuitTotalCount: 8,
  common2CircuitTotalCount: 8,
  common3CircuitTotalCount: 8,
}

describe('CompensationBankTopology', () => {
  it('渲染 6 条母线', () => {
    const wrapper = mount(CompensationBankTopology, {
      props: { telemetry: telemetry(), circuitProfile: profile },
    })
    expect(wrapper.findAll('[data-test="topo-bus"]')).toHaveLength(6)
  })

  it('mask 解码为投入/切除回路', () => {
    const wrapper = mount(CompensationBankTopology, {
      props: { telemetry: telemetry(), circuitProfile: profile },
    })
    // A 相 8 路中 1 路投入
    const aBus = wrapper.findAll('[data-test="topo-bus"]')[0]
    expect(aBus.findAll('.topo-cap.is-on')).toHaveLength(1)
    expect(aBus.findAll('.topo-cap.is-off')).toHaveLength(7)
  })

  it('点击回路 emit pick', async () => {
    const wrapper = mount(CompensationBankTopology, {
      props: { telemetry: telemetry(), circuitProfile: profile },
    })
    await wrapper.findAll('.topo-cap')[0].trigger('click')
    const pick = wrapper.emitted('pick')?.[0]?.[0] as Record<string, unknown>
    expect(pick.phase).toBe('A')
    expect(pick.index).toBe(1)
    expect(pick.state).toBe('on')
  })

  it('相级告警时该相标签带告警角标', () => {
    const wrapper = mount(CompensationBankTopology, {
      props: {
        telemetry: telemetry({ overvoltage_alarm_b: true }),
        circuitProfile: profile,
      },
    })
    const bBus = wrapper.findAll('[data-test="topo-bus"]')[1]
    expect(bBus.find('.topo-phase-alarm').exists()).toBe(true)
  })

  it('按分相补偿和共补回路做轻分区', () => {
    const wrapper = mount(CompensationBankTopology, {
      props: { telemetry: telemetry(), circuitProfile: profile },
    })
    const sections = wrapper.findAll('.topo-section-label')

    expect(sections).toHaveLength(2)
    expect(sections[0].text()).toContain('分相补偿')
    expect(sections[1].text()).toContain('共补回路')
  })

  it('每行显示已投运与可用回路小计', () => {
    const wrapper = mount(CompensationBankTopology, {
      props: { telemetry: telemetry(), circuitProfile: profile },
    })
    const buses = wrapper.findAll('[data-test="topo-bus"]')

    expect(buses[0].find('.topo-row-summary').text()).toContain('1/8')
    expect(buses[1].find('.topo-row-summary').text()).toContain('2/8')
    expect(buses[3].find('.topo-row-summary').text()).toContain('0/8')
  })
})
