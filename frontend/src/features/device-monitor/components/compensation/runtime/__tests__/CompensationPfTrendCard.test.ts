import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationPfTrendCard from '../CompensationPfTrendCard.vue'

function mountCard(props: Record<string, unknown> = {}) {
  return mount(CompensationPfTrendCard, {
    props: {
      pf: 0.975,
      p: 168,
      q: 38,
      pfTrend: { values: [0.96, 0.97, 0.975], timestamps: [], target: 0.95 },
      timeRangeKey: '1h',
      ...props,
    },
  })
}

describe('CompensationPfTrendCard', () => {
  it('渲染 PF 大数字与视在功率', () => {
    const wrapper = mountCard()
    expect(wrapper.text()).toContain('0.975')
    expect(wrapper.text()).toContain('功率因数')
    // S = round(sqrt(168^2 + 38^2)) = 172
    expect(wrapper.text()).toContain('172')
  })

  it('趋势点 >= 2 时渲染 sparkline 折线', () => {
    const wrapper = mountCard()
    expect(wrapper.find('[data-test="pf-spark-line"]').exists()).toBe(true)
  })

  it('趋势点不足时隐藏 sparkline', () => {
    const wrapper = mountCard({ pfTrend: { values: [0.97], timestamps: [], target: 0.95 } })
    expect(wrapper.find('[data-test="pf-spark-line"]').exists()).toBe(false)
  })

  it('有效 target 时渲染目标区间色带', () => {
    const wrapper = mountCard({ pfTrend: { values: [0.96, 0.97], timestamps: [], target: 0.95 } })
    expect(wrapper.find('[data-test="pf-target-band"]').exists()).toBe(true)
  })

  it('显示 PF 纵轴刻度、时间刻度和当前时间段有效点数', () => {
    const wrapper = mountCard({
      pfTrend: {
        values: [0.91, 0.94, 0.97],
        timestamps: [
          '2026-05-21T10:00:00+08:00',
          '2026-05-21T10:30:00+08:00',
          '2026-05-21T11:00:00+08:00',
        ],
        target: 0.95,
      },
      timeRangeKey: '1h',
    })

    expect(wrapper.find('[data-test="pf-y-axis"]').text()).toContain('1.00')
    expect(wrapper.find('[data-test="pf-y-axis"]').text()).toContain('0.95')
    expect(wrapper.find('[data-test="pf-y-axis"]').text()).toContain('0.90')
    expect(wrapper.find('[data-test="pf-x-axis"]').text()).toContain('10:00')
    expect(wrapper.find('[data-test="pf-x-axis"]').text()).toContain('10:30')
    expect(wrapper.find('[data-test="pf-x-axis"]').text()).toContain('11:00')
    expect(wrapper.find('[data-test="pf-window-summary"]').text()).toContain('1 小时')
    expect(wrapper.find('[data-test="pf-window-summary"]').text()).toContain('3 点')
  })

  it('target 为 null 时隐藏目标区间色带', () => {
    const wrapper = mountCard({ pfTrend: { values: [0.96, 0.97], timestamps: [], target: null } })
    expect(wrapper.find('[data-test="pf-target-band"]').exists()).toBe(false)
  })

  it('点击时间范围标签触发 range-change', async () => {
    const wrapper = mountCard()
    await wrapper.findAll('[data-test="pf-range-tab"]')[2].trigger('click')
    expect(wrapper.emitted('range-change')?.[0]).toEqual(['24h'])
  })
})
