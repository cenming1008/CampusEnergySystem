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

  it('recomputes configured slots when circuit counts arrive later', async () => {
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

    expect(wrapper.findAll('.step-badge--unconfigured')).toHaveLength(48)

    await wrapper.setProps({
      configuredSplitCircuitCount: 8,
      configuredCommonCircuitCount: 12,
    })

    expect(wrapper.findAll('.step-badge--unconfigured')).toHaveLength(28)
    expect(wrapper.findAll('.step-badge--on')).toHaveLength(3)
  })
})
