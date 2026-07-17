import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StorageCommandTimeline from '../StorageCommandTimeline.vue'

describe('StorageCommandTimeline', () => {
  it('shows backend reasons for rejected and timeout terminal receipts', () => {
    const wrapper = mount(StorageCommandTimeline, {
      props: {
        items: [
          {
            commandId: '41',
            actionLabel: '设置功率 -80.0 kW',
            result: 'rejected',
            resultLabel: '已拒绝',
            detail: 'SOC 已达到放电下限',
            createdAt: '2026-07-17 10:00:00',
          },
          {
            commandId: '42',
            actionLabel: '停止充放电',
            result: 'timeout',
            resultLabel: '执行超时',
            detail: '在约定等待时间内未收到设备回执',
            createdAt: '2026-07-17 10:05:00',
          },
        ],
      },
    })

    expect(wrapper.text()).toContain('已拒绝')
    expect(wrapper.text()).toContain('SOC 已达到放电下限')
    expect(wrapper.text()).toContain('执行超时')
    expect(wrapper.text()).toContain('在约定等待时间内未收到设备回执')
  })
})
