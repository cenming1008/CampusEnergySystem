import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import CompensationHeader from '../CompensationHeader.vue'

const model = {
  title: '补偿控制器',
  serial: 'CAP-001',
  location: '配电房',
  deviceStatus: '离线',
  deviceStatusTone: 'danger' as const,
  tags: [{ label: '手动', tone: 'warning' as const }],
}

describe('CompensationHeader', () => {
  it('does not render the removed remote-control entry', () => {
    const wrapper = mount(CompensationHeader, {
      props: {
        model,
        toggleActionLabel: '停用设备',
        toggleButtonType: 'danger',
        canControlDevices: true,
      },
      global: {
        stubs: {
          'el-icon': { template: '<span class="icon-probe"><slot /></span>' },
          ArrowLeft: true,
          Refresh: true,
          SwitchButton: true,
        },
      },
    })

    expect(wrapper.find('button[aria-label="远程控制"]').exists()).toBe(false)
    expect(wrapper.find('button[aria-label="参数设置"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('远程控制')
  })

  it('renders workbench tabs in the header without a search input', async () => {
    const wrapper = mount(CompensationHeader, {
      props: {
        model,
        toggleActionLabel: '停用设备',
        toggleButtonType: 'danger',
        canControlDevices: true,
        activeTab: 'curves',
        tabs: [
          { label: '运行监视', value: 'runtime' },
          { label: '曲线分析', value: 'curves' },
          { label: '参数设置', value: 'parameter-settings' },
          { label: '事件记录', value: 'event-records' },
        ],
      },
      global: {
        stubs: {
          'el-icon': { template: '<span class="icon-probe"><slot /></span>' },
          ArrowLeft: true,
          Refresh: true,
          SwitchButton: true,
        },
      },
    })

    expect(wrapper.find('.comp-header__tabs').exists()).toBe(true)
    expect(wrapper.find('.comp-header__tab.is-active').text()).toContain('曲线分析')
    expect(wrapper.find('.comp-header__device-pill').text()).toContain('监视')
    expect(wrapper.find('.comp-header__device-pill').text()).toContain('补偿控制器')
    expect(wrapper.find('.comp-header__device-pill').text()).toContain('配电房')
    expect(wrapper.find('.comp-header__device-pill').text()).not.toContain('曲线分析')
    expect(wrapper.find('.comp-header__device-pill').text()).not.toContain('CAP-001')
    expect(wrapper.find('input').exists()).toBe(false)

    await wrapper.findAll('.comp-header__tab').find((button) => button.text().includes('运行监视'))?.trigger('click')

    expect(wrapper.emitted('tab-change')?.[0]).toEqual(['runtime'])
  })

  it('presents the identity pill as three labeled fields', () => {
    const wrapper = mount(CompensationHeader, {
      props: {
        model,
        toggleActionLabel: '停用设备',
        toggleButtonType: 'danger',
        canControlDevices: true,
      },
      global: {
        stubs: {
          'el-icon': { template: '<span class="icon-probe"><slot /></span>' },
          ArrowLeft: true,
          Refresh: true,
          SwitchButton: true,
        },
      },
    })

    const fields = wrapper.findAll('.comp-header__identity-field')

    expect(fields).toHaveLength(3)
    expect(
      fields.map((field) => {
        const label = field.find('.comp-header__identity-label')
        return label.exists() ? label.text() : ''
      }),
    ).toEqual([
      '',
      '设备名称',
      '位置',
    ])
    expect(fields.map((field) => field.find('.comp-header__identity-value').text())).toEqual([
      '监视',
      '补偿控制器',
      '配电房',
    ])
  })
})
