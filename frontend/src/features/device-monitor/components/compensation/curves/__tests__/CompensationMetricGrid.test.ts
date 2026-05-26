import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

const { setOptionsMock, initChartMock } = vi.hoisted(() => ({
  setOptionsMock: vi.fn(),
  initChartMock: vi.fn(),
}))

vi.mock('@/shared/composables/useECharts', () => ({
  useECharts: () => ({
    chartRef: ref(document.createElement('div')),
    initChart: initChartMock,
    setOptions: setOptionsMock,
  }),
}))

import CompensationMetricGrid from '../CompensationMetricGrid.vue'

const history: CompensationCapacitorBankTelemetry[] = [
  {
    device_id: 1,
    timestamp: '2026-05-21T09:00:00+08:00',
    voltage_a: 220,
    voltage_b: 221,
    voltage_c: 219,
    current_a: 30,
    current_b: 31,
    current_c: 29,
    power_factor_a: 0.96,
    power_factor_b: 0.95,
    power_factor_c: 0.97,
    reactive_power_a: 4,
    reactive_power_b: 5,
    reactive_power_c: 6,
    active_power_a: 20,
    active_power_b: 21,
    active_power_c: 22,
    voltage_thd_a: 2,
    voltage_thd_b: 2.1,
    voltage_thd_c: 2.2,
    current_harmonic_a: 3,
    current_harmonic_b: 3.1,
    current_harmonic_c: 3.2,
    temperature: 36,
  },
  {
    device_id: 1,
    timestamp: '2026-05-21T09:05:00+08:00',
    voltage_a: 222,
    voltage_b: 220,
    voltage_c: 221,
    current_a: 32,
    current_b: 30,
    current_c: 31,
    power_factor_a: 0.97,
    power_factor_b: 0.96,
    power_factor_c: 0.98,
    reactive_power_a: 3,
    reactive_power_b: 4,
    reactive_power_c: 5,
    active_power_a: 21,
    active_power_b: 22,
    active_power_c: 23,
    voltage_thd_a: 2.3,
    voltage_thd_b: 2.2,
    voltage_thd_c: 2.1,
    current_harmonic_a: 3.4,
    current_harmonic_b: 3.3,
    current_harmonic_c: 3.2,
    temperature: 37,
  },
]

describe('CompensationMetricGrid', () => {
  beforeEach(() => {
    setOptionsMock.mockReset()
    initChartMock.mockReset()
  })

  it('switches the large chart to a single metric instead of overlaying selected metrics', async () => {
    const wrapper = mount(CompensationMetricGrid, {
      props: {
        telemetry: history.at(-1) ?? null,
        history,
      },
    })

    await wrapper.findAll('.metric-grid__toggle-btn').find((button) => button.text() === '大图')?.trigger('click')
    await Promise.resolve()
    await Promise.resolve()

    const reactivePowerChip = wrapper.findAll('.metric-grid__chip').find((button) => button.text().includes('无功功率 Q'))
    expect(reactivePowerChip?.exists()).toBe(true)

    await reactivePowerChip?.trigger('click')
    await Promise.resolve()
    await Promise.resolve()

    const activeChips = wrapper.findAll('.metric-grid__chip.is-active').map((button) => button.text())
    expect(activeChips).toEqual(['无功功率 Q kVar'])

    const option = setOptionsMock.mock.calls.at(-1)?.[0]
    expect(option?.yAxis).toHaveLength(1)
    expect(option?.yAxis?.[0]?.name).toBe('kVar')
    expect(option?.series?.map((series: { name: string }) => series.name)).toEqual(['Q'])
  })

  it('labels harmonic current metrics with ampere units instead of THDi percent wording', () => {
    const wrapper = mount(CompensationMetricGrid, {
      props: {
        telemetry: history.at(-1) ?? null,
        history,
      },
    })

    const text = wrapper.text()
    expect(text).toContain('谐波电流')
    expect(text).toContain('A')
    expect(text).not.toContain('THDi')
  })
})
