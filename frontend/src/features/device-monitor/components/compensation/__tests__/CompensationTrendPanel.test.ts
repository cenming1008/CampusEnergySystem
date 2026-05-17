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
    const wrapper = mount(CompensationTrendPanel, {
      props: {
        tabs: [{ label: '补偿效果', value: 'effect' }],
        activeTab: 'effect',
        model: {
          labels: [],
          legend: ['无功功率 Q', '功率因数 PF'],
          axes: [{ name: 'kVar' }, { name: 'PF', position: 'right' }],
          series: [
            { name: '无功功率 Q', data: [['2026-04-17T00:00:00', 10]], color: '#38bdf8' },
            { name: '功率因数 PF', data: [['2026-04-17T00:00:00', 0.96]], color: '#4ade80', yAxisIndex: 1 },
          ],
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
    expect(option?.legend?.show).toBe(false)
    expect(wrapper.find('.trend-panel__legend').text()).toContain('无功功率 Q')
    expect(wrapper.find('.trend-panel__legend').text()).toContain('功率因数 PF')
  })

  it('keeps the chart area blank instead of overlaying empty-state copy', async () => {
    const wrapper = mount(CompensationTrendPanel, {
      props: {
        tabs: [{ label: '补偿效果', value: 'effect' }],
        activeTab: 'effect',
        model: {
          labels: [],
          legend: ['无功功率 Q', '功率因数 PF'],
          axes: [{ name: 'kVar' }, { name: 'PF', position: 'right' }],
          series: [],
          summary: [
            { label: '当前 Q', value: '-' },
            { label: '当前 PF', value: '-' },
          ],
          empty: true,
          emptyText: '',
          isMock: false,
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
    expect(option?.title?.text ?? '').toBe('')
    expect(option?.series).toEqual([])
    expect(wrapper.text()).not.toContain('当前时间范围内暂无可绘制数据')
    expect(wrapper.text()).toContain('当前 Q -')
  })
})
