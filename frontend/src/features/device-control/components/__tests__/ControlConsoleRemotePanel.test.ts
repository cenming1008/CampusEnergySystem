import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import ControlConsoleRemotePanel from '../ControlConsoleRemotePanel.vue'

const SectionStub = defineComponent({
  props: {
    title: { type: String, default: '' },
  },
  template: `
    <section class="section-stub">
      <h3>{{ title }}</h3>
      <slot name="headerExtra" />
      <slot />
    </section>
  `,
})

function mountPanel(remoteControlEnabled: boolean) {
  return mount(ControlConsoleRemotePanel, {
    props: {
      actionCards: [],
      toggleSubmitting: false,
      currentControlModeLabel: '手动',
      canRunManualSwitch: false,
      manualSwitchDisabledReason: '设备离线',
      manualPhaseOptions: [{ label: 'A 相', value: 'A' }],
      manualSwitchActionOptions: [{ label: '投入', value: 'on' }],
      manualCommonGroupOptions: [{ label: '1 组', value: 1 }],
      manualPhase: 'A',
      manualSwitchAction: 'on',
      manualCommonGroup: 1,
      remoteControlEnabled,
    },
    global: {
      stubs: {
        MonitorSectionPanel: SectionStub,
        'el-tag': { template: '<span><slot /></span>' },
        'el-tooltip': { template: '<span><slot /></span>' },
        'el-select': { template: '<div><slot /></div>' },
        'el-option': true,
      },
    },
  })
}

describe('ControlConsoleRemotePanel', () => {
  it('does not render the remote capability status tag', () => {
    expect(mountPanel(true).text()).not.toContain('已开通')
    expect(mountPanel(false).text()).not.toContain('未开通')
  })
})
