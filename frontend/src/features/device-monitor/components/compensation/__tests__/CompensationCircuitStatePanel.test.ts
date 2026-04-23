import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationCircuitStatePanel from '../CompensationCircuitStatePanel.vue'

describe('CompensationCircuitStatePanel', () => {
  it('marks protocol slots beyond configured circuits as unconfigured', () => {
    const wrapper = mount(CompensationCircuitStatePanel, {
      props: {
        capacitorBankTelemetry: {
          device_id: 16,
          timestamp: '2026-04-15T15:45:00',
          circuit_state_phase_a: 0xff,
          circuit_state_phase_b: 0xff,
          circuit_state_phase_c: 0xff,
          circuit_state_common_1: 0xff,
          circuit_state_common_2: 0xff,
          circuit_state_common_3: 0xff,
        },
        configuredSplitCircuitCount: 8,
        configuredCommonCircuitCount: 12,
      },
    })

    expect(wrapper.findAll('.step-badge--unconfigured')).toHaveLength(28)
  })

  it('shows unknown slots before MQTT-reported circuit counts arrive, then recomputes configured slots', async () => {
    const wrapper = mount(CompensationCircuitStatePanel, {
      props: {
        capacitorBankTelemetry: {
          device_id: 16,
          timestamp: '2026-04-15T15:45:00',
          circuit_state_phase_a: 0x03,
          circuit_state_phase_b: 0x00,
          circuit_state_phase_c: 0x00,
          circuit_state_common_1: 0x01,
          circuit_state_common_2: 0x00,
          circuit_state_common_3: 0x00,
        },
      },
    })

    expect(wrapper.findAll('.step-badge--na')).toHaveLength(48)
    expect(wrapper.findAll('.group-card__count').map((node) => node.text())).toEqual([
      '等待 MQTT 回读',
      '等待 MQTT 回读',
      '等待 MQTT 回读',
      '等待 MQTT 回读',
      '等待 MQTT 回读',
      '等待 MQTT 回读',
    ])
    expect(wrapper.findAll('.step-badge--na')[0].attributes('title')).toBe('等待 MQTT 回读回路配置')

    await wrapper.setProps({
      configuredSplitCircuitCount: 8,
      configuredCommonCircuitCount: 12,
    })

    expect(wrapper.findAll('.step-badge--unconfigured')).toHaveLength(28)
    expect(wrapper.findAll('.step-badge--on')).toHaveLength(3)
  })

  it('prefers explicit per-group circuit totals from the gateway over local redistribution', () => {
    const wrapper = mount(CompensationCircuitStatePanel, {
      props: {
        capacitorBankTelemetry: {
          device_id: 16,
          timestamp: '2026-04-15T15:45:00',
          circuit_state_phase_a: 0x07,
          circuit_state_phase_b: 0x07,
          circuit_state_phase_c: 0x03,
          circuit_state_common_1: 0x3f,
          circuit_state_common_2: 0x0f,
          circuit_state_common_3: 0x03,
        },
        configuredSplitCircuitCount: 8,
        configuredCommonCircuitCount: 12,
        phaseACircuitTotalCount: 3,
        phaseBCircuitTotalCount: 3,
        phaseCCircuitTotalCount: 2,
        common1CircuitTotalCount: 6,
        common2CircuitTotalCount: 4,
        common3CircuitTotalCount: 2,
      },
    })

    const counts = wrapper.findAll('.group-card__count').map((node) => node.text())
    expect(counts).toEqual([
      '3/3 投入',
      '3/3 投入',
      '2/2 投入',
      '6/6 投入',
      '4/4 投入',
      '2/2 投入',
    ])
    expect(wrapper.findAll('.step-badge--unconfigured')).toHaveLength(28)
  })

  it('treats explicit zero circuit counts as configured zero, not unknown', () => {
    const wrapper = mount(CompensationCircuitStatePanel, {
      props: {
        capacitorBankTelemetry: {
          device_id: 16,
          timestamp: '2026-04-15T15:45:00',
          circuit_state_phase_a: 0xff,
          circuit_state_phase_b: 0xff,
          circuit_state_phase_c: 0xff,
          circuit_state_common_1: 0xff,
          circuit_state_common_2: 0xff,
          circuit_state_common_3: 0xff,
        },
        phaseACircuitTotalCount: 0,
        phaseBCircuitTotalCount: 0,
        phaseCCircuitTotalCount: 0,
        common1CircuitTotalCount: 0,
        common2CircuitTotalCount: 0,
        common3CircuitTotalCount: 0,
      },
    })

    expect(wrapper.findAll('.group-card__count').map((node) => node.text())).toEqual([
      '0/0 投入',
      '0/0 投入',
      '0/0 投入',
      '0/0 投入',
      '0/0 投入',
      '0/0 投入',
    ])
    expect(wrapper.findAll('.step-badge--unconfigured')).toHaveLength(48)
    expect(wrapper.findAll('.step-badge--na')).toHaveLength(0)
  })
})
