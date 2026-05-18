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
  it('uses the remote control label as the default secondary entry label', () => {
    const wrapper = mount(CompensationHeader, {
      props: {
        model,
        toggleActionLabel: '停用设备',
        toggleButtonType: 'danger',
        canControlDevices: true,
        showConsoleEntry: true,
      },
      global: {
        stubs: {
          'el-icon': { template: '<span class="icon-probe"><slot /></span>' },
          ArrowLeft: true,
          Refresh: true,
          SwitchButton: true,
          Setting: { template: '<i class="setting-icon-probe" />' },
        },
      },
    })

    const consoleButton = wrapper.find('button[aria-label="远程控制"]')

    expect(consoleButton.exists()).toBe(true)
    expect(consoleButton.attributes('title')).toBe('远程控制')
    expect(consoleButton.text()).toContain('远程控制')
    expect(consoleButton.text()).not.toContain('控制台')
  })

  it('uses the provided workbench action label and settings icon for the secondary entry', () => {
    const wrapper = mount(CompensationHeader, {
      props: {
        model,
        toggleActionLabel: '停用设备',
        toggleButtonType: 'danger',
        canControlDevices: true,
        showConsoleEntry: true,
        consoleEntryLabel: '参数设置',
      },
      global: {
        stubs: {
          'el-icon': { template: '<span class="icon-probe"><slot /></span>' },
          ArrowLeft: true,
          Refresh: true,
          SwitchButton: true,
          Setting: { template: '<i class="setting-icon-probe" />' },
        },
      },
    })

    const consoleButton = wrapper.find('button[aria-label="参数设置"]')

    expect(consoleButton.exists()).toBe(true)
    expect(consoleButton.attributes('title')).toBe('参数设置')
    expect(consoleButton.text()).toContain('参数设置')
    expect(consoleButton.text()).not.toContain('控制台')
    expect(consoleButton.find('.setting-icon-probe').exists()).toBe(true)
  })
})
