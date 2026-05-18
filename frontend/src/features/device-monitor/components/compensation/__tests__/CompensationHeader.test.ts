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
  it('uses a concise console label and settings icon for the console entry', () => {
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

    const consoleButton = wrapper.find('button[aria-label="控制台"]')

    expect(consoleButton.exists()).toBe(true)
    expect(consoleButton.attributes('title')).toBe('控制台')
    expect(consoleButton.text()).toContain('控制台')
    expect(consoleButton.text()).not.toContain('进入控制台')
    expect(consoleButton.find('.setting-icon-probe').exists()).toBe(true)
  })
})
