import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationPqQuadrantCard from '../CompensationPqQuadrantCard.vue'

describe('CompensationPqQuadrantCard', () => {
  it('有 P/Q 时渲染当前运行点', () => {
    const wrapper = mount(CompensationPqQuadrantCard, {
      props: {
        model: {
          point: { p: 168, q: 38 },
          history: [],
          axis: { pMax: 500, qMax: 250 },
          referenceLines: [
            { powerFactor: 0.9, label: 'PF 0.90', role: 'threshold' },
            { powerFactor: 0.95, label: 'PF 0.95', role: 'target' },
          ],
          targetPowerFactor: 0.95,
        },
      },
    })
    expect(wrapper.find('[data-test="pq-current-point"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('P 168')
    expect(wrapper.text()).toContain('PF 0.90')
  })

  it('P 或 Q 缺失时显示空状态', () => {
    const wrapper = mount(CompensationPqQuadrantCard, {
      props: {
        model: {
          point: { p: null, q: 38 },
          history: [],
          axis: { pMax: 400, qMax: 200 },
          referenceLines: [],
          targetPowerFactor: null,
        },
      },
    })
    expect(wrapper.find('[data-test="pq-current-point"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('等待实时遥测')
  })

  it('有轨迹时渲染轨迹路径，无轨迹时不渲染', () => {
    const withHistory = mount(CompensationPqQuadrantCard, {
      props: {
        model: {
          point: { p: 168, q: 38 },
          history: [[100, 60], [120, 50]],
          axis: { pMax: 400, qMax: 200 },
          referenceLines: [],
          targetPowerFactor: null,
        },
      },
    })
    expect(withHistory.find('[data-test="pq-history-path"]').exists()).toBe(true)
    const noHistory = mount(CompensationPqQuadrantCard, {
      props: {
        model: {
          point: { p: 168, q: 38 },
          history: [],
          axis: { pMax: 400, qMax: 200 },
          referenceLines: [],
          targetPowerFactor: null,
        },
      },
    })
    expect(noHistory.find('[data-test="pq-history-path"]').exists()).toBe(false)
  })
})
