import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationHealthCard from '../CompensationHealthCard.vue'
import type { CompensationHealthModel } from '../../types'

function model(overrides: Partial<CompensationHealthModel> = {}): CompensationHealthModel {
  return {
    score: 78,
    rating: '良好',
    ratingTone: 'success',
    breakdown: [
      { key: 'comm', label: '通讯链路', value: 65 },
      { key: 'voltageHarmonic', label: '电压谐波', value: 42 },
      { key: 'currentHarmonic', label: '电流谐波', value: 88 },
      { key: 'switching', label: '投切动作', value: 96 },
      { key: 'temperature', label: '温度', value: 100 },
      { key: 'voltageStability', label: '电压稳定', value: null },
    ],
    ...overrides,
  }
}

describe('CompensationHealthCard', () => {
  it('渲染总分与 6 维', () => {
    const wrapper = mount(CompensationHealthCard, { props: { model: model() } })
    expect(wrapper.text()).toContain('78')
    expect(wrapper.text()).toContain('良好')
    expect(wrapper.findAll('[data-test="health-bar"]')).toHaveLength(6)
  })

  it('缺测维度显示「待采集」', () => {
    const wrapper = mount(CompensationHealthCard, { props: { model: model() } })
    expect(wrapper.text()).toContain('待采集')
  })

  it('score 为 null 时显示空状态', () => {
    const wrapper = mount(CompensationHealthCard, {
      props: { model: model({ score: null, rating: '暂无评级', ratingTone: 'neutral' }) },
    })
    expect(wrapper.text()).toContain('暂无健康度数据')
  })
})
