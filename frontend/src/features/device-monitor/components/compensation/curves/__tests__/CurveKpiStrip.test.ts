import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CurveKpiStrip from '../CurveKpiStrip.vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

const telemetry: CompensationCapacitorBankTelemetry = {
  device_id: 12,
  timestamp: '2026-05-21T10:00:00+08:00',
  power_factor_a: 0.96,
  power_factor_b: 0.95,
  power_factor_c: 0.97,
  reactive_power_a: 2,
  reactive_power_b: 3,
  reactive_power_c: 4,
  voltage_thd_a: 3.4,
  current_harmonic_a: 7.2,
  temperature: 36.5,
}

describe('CurveKpiStrip', () => {
  it('labels current harmonic KPI as an ampere magnitude instead of a percent distortion', () => {
    const wrapper = mount(CurveKpiStrip, {
      props: {
        telemetry,
        history: [telemetry, { ...telemetry, timestamp: '2026-05-21T10:05:00+08:00', current_harmonic_a: 7.5 }],
      },
    })

    const text = wrapper.text()
    expect(text).toContain('A相谐波电流')
    expect(text).toContain('A')
    expect(text).not.toContain('THDi A 相')
    expect(text).not.toContain('8.00%')
  })
})
