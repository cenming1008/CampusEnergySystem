import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationPhaseMatrix from '../CompensationPhaseMatrix.vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

function telemetry(overrides: Partial<CompensationCapacitorBankTelemetry> = {}): CompensationCapacitorBankTelemetry {
  return {
    device_id: 1,
    timestamp: '2026-05-19T10:00:00+08:00',
    current_a: 12, current_b: 12, current_c: 12,
    voltage_thd_a: 1.2, voltage_thd_b: 1.4, voltage_thd_c: 1.1,
    current_harmonic_a: 2, current_harmonic_b: 2, current_harmonic_c: 2,
    ...overrides,
  } as CompensationCapacitorBankTelemetry
}

describe('CompensationPhaseMatrix', () => {
  it('渲染指标行与 A/B/C/系统 列', () => {
    const wrapper = mount(CompensationPhaseMatrix, { props: { telemetry: telemetry() } })
    expect(wrapper.text()).toContain('V-THD 谐波')
    expect(wrapper.text()).toContain('A 相')
    expect(wrapper.text()).toContain('系统')
  })

  it('V-THD 超限单元格标记为超限态', () => {
    const wrapper = mount(CompensationPhaseMatrix, {
      props: { telemetry: telemetry({ voltage_thd_a: 27 }) },
    })
    expect(wrapper.find('.matrix-cell.is-crit').exists()).toBe(true)
  })

  it('遥测缺失时单元格显示占位符', () => {
    const wrapper = mount(CompensationPhaseMatrix, { props: { telemetry: null } })
    expect(wrapper.text()).toContain('--')
  })
})
