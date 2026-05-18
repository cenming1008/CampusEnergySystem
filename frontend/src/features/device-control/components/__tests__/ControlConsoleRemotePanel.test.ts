import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import ControlConsoleRemotePanel from '../ControlConsoleRemotePanel.vue'
import type { ControlConsoleActionCard } from '@/features/device-control/viewMapping'

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

const actionCards: ControlConsoleActionCard[] = [
  {
    key: 'toggle_device',
    title: '启停 / 使能',
    actionLabel: '停用设备',
    enabled: true,
    iconKey: 'switch',
  },
  {
    key: 'reset_alarm',
    title: '报警复位',
    actionLabel: '复位报警',
    enabled: true,
    iconKey: 'refresh',
  },
  {
    key: 'switch_control_mode',
    title: '控制模式切换',
    actionLabel: '切到自动',
    enabled: true,
    iconKey: 'setting',
  },
]

function mountPanel(remoteControlEnabled: boolean) {
  return mount(ControlConsoleRemotePanel, {
    props: {
      actionCards,
      toggleSubmitting: false,
      currentControlModeLabel: '手动',
      canRunManualSwitch: true,
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

  it('renders only mode switching and manual switching in a compact control row', async () => {
    const wrapper = mountPanel(true)

    expect(wrapper.find('.remote-control-compact').exists()).toBe(true)
    expect(wrapper.text()).toContain('控制模式切换')
    expect(wrapper.text()).toContain('切到自动')
    expect(wrapper.text()).toContain('手动投切控制')
    expect(wrapper.text()).not.toContain('启停 / 使能')
    expect(wrapper.text()).not.toContain('报警复位')
    expect(wrapper.findAll('.remote-card')).toHaveLength(0)

    await wrapper.get('[data-test="mode-switch-action"]').trigger('click')
    expect(wrapper.emitted('actionCard')?.[0]).toEqual(['switch_control_mode'])
  })
})
