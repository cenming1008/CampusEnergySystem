import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StorageControlPanel from '../StorageControlPanel.vue'

function mountPanel(overrides: Record<string, unknown> = {}) {
  return mount(StorageControlPanel, {
    props: {
      dataSourceLabel: '仿真数据',
      controlMode: 'manual',
      actualPower: -40,
      targetPower: -50,
      availableChargePower: 200,
      availableDischargePower: 180,
      bmsStatus: 'normal',
      pcsStatus: 'running',
      gridStatus: 'connected',
      commandSource: '人工控制',
      currentPlanLabel: '--',
      autoAuthorized: false,
      canControl: true,
      canManageAuto: false,
      pending: false,
      submitting: false,
      ...overrides,
    },
  })
}

describe('StorageControlPanel', () => {
  it.each([
    ['仿真数据', '仿真数据'],
    ['真实设备', '真实设备'],
  ])('shows the %s source badge', (source, expected) => {
    const wrapper = mountPanel({ dataSourceLabel: source })
    expect(wrapper.text()).toContain(expected)
  })

  it('disables all controls and keeps automatic authorization off for a viewer', () => {
    const wrapper = mountPanel({ canControl: false, canManageAuto: false })
    expect(wrapper.get('[data-test="storage-power-input"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-test="storage-set-power"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-test="storage-stop"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-test="storage-auto-gate"]').attributes('disabled')).toBeDefined()
    expect((wrapper.get('[data-test="storage-auto-gate"]').element as HTMLInputElement).checked).toBe(false)
  })

  it('emits a manual setpoint without changing the discharge sign', async () => {
    const wrapper = mountPanel()
    await wrapper.get('[data-test="storage-power-input"]').setValue('-80')
    await wrapper.get('[data-test="storage-set-power"]').trigger('click')

    expect(wrapper.emitted('set-power')).toEqual([[-80]])
  })

  it('disables conflicting controls while a command is pending', () => {
    const wrapper = mountPanel({ pending: true })
    expect(wrapper.get('[data-test="storage-set-power"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-test="storage-mode-auto"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-test="storage-mode-manual"]').attributes('disabled')).toBeDefined()
  })
})
