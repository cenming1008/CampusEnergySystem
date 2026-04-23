import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'

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

import CompensationTrendPanel from '../CompensationTrendPanel.vue'

describe('CompensationTrendPanel', () => {
  beforeEach(() => {
    setOptionsMock.mockReset()
    initChartMock.mockReset()
  })

  it('uses a real time axis when the model requests a fixed time range', async () => {
    mount(CompensationTrendPanel, {
      props: {
        tabs: [{ label: '补偿效果', value: 'effect' }],
        activeTab: 'effect',
        model: {
          labels: [],
          legend: ['无功功率 Q'],
          axes: [{ name: 'kVar' }],
          series: [{ name: '无功功率 Q', data: [['2026-04-17T00:00:00', 10]], color: '#38bdf8' }],
          summary: [],
          empty: false,
          emptyText: '',
          isMock: false,
          xAxisType: 'time',
          xAxisMin: '2026-04-17T00:00:00',
          xAxisMax: '2026-04-24T00:00:00',
        },
      },
      global: {
        stubs: {
          'el-segmented': true,
          'el-date-picker': true,
          'el-tag': true,
        },
        directives: {
          loading: () => undefined,
        },
      },
    })

    await Promise.resolve()
    await Promise.resolve()

    const option = setOptionsMock.mock.calls.at(-1)?.[0]
    expect(option?.xAxis?.type).toBe('time')
    expect(option?.xAxis?.min).toBe('2026-04-17T00:00:00')
    expect(option?.xAxis?.max).toBe('2026-04-24T00:00:00')
  })
})
