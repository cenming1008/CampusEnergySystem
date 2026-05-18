import { computed, effectScope, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const {
  warningMock,
  successMock,
  errorMock,
  confirmMock,
  writeProfileMock,
  sendRemoteCommandMock,
} = vi.hoisted(() => ({
  warningMock: vi.fn(),
  successMock: vi.fn(),
  errorMock: vi.fn(),
  confirmMock: vi.fn(),
  writeProfileMock: vi.fn(),
  sendRemoteCommandMock: vi.fn(),
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual<typeof import('element-plus')>('element-plus')
  return {
    ...actual,
    ElMessage: {
      warning: warningMock,
      success: successMock,
      error: errorMock,
    },
    ElMessageBox: {
      confirm: confirmMock,
    },
  }
})

vi.mock('@/api/device', () => ({
  toggleDeviceStatus: vi.fn(),
}))

vi.mock('@/api/compensation', () => ({
  sendCompensationCapacitorBankRemoteCommand: sendRemoteCommandMock,
  writeCompensationCapacitorBankControlProfile: writeProfileMock,
}))

import { useControlConsoleActions } from '../useControlConsoleActions'

const baseCapabilities = {
  supports_read: true,
  supports_write: true,
  supports_remote_control: true,
  write_status_message: '',
  remote_control_status_message: '',
  protocol_version: 'campus-control.v1',
  command_message_type: 'control_command',
  receipt_message_type: 'control_receipt',
  control_topic_template: 'campus/control/{device_code}',
  receipt_topic: 'campus/telemetry',
  receipt_timeout_seconds: 120,
  supported_results: ['accepted', 'running', 'success', 'failed', 'timeout', 'rejected'],
  writable_parameters: [
    'switch_on_power_factor',
    'switch_off_power_factor',
    'switch_on_delay_seconds',
    'switch_off_delay_seconds',
    'overvoltage_threshold',
    'voltage_harmonic_threshold',
    'current_harmonic_threshold',
    'temperature_upper_limit',
  ],
  remote_commands: [
    {
      action: 'reset_alarm',
      label: '报警复位',
      supported: false,
      disabled_reason: '真实网关暂未提供报警复位寄存器/功能码',
    },
    {
      action: 'switch_control_mode',
      label: '控制模式切换',
      supported: true,
    },
  ],
}

describe('useControlConsoleActions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    confirmMock.mockResolvedValue(undefined)
  })

  it('blocks write dialog when write permission is unavailable', () => {
    const scope = effectScope()
    const state = scope.run(() => useControlConsoleActions({
      deviceId: computed(() => 2),
      canManageDevices: computed(() => true),
      canControlDevices: computed(() => true),
      currentRole: computed(() => 'operator'),
      isAdmin: computed(() => false),
      archive: computed(() => ({ name: '设备-CAP-001' })),
      runtimeStatus: computed(() => ({ is_active: true, is_online: true })),
      controlProfile: ref({
        device_id: 2,
        source_status: 'fresh',
        capabilities: baseCapabilities,
        switch_on_power_factor: 92,
      } as any),
      controlCapabilities: computed(() => baseCapabilities),
      controlLogs: ref([]),
      loadPage: vi.fn().mockResolvedValue(undefined),
    }))

    state!.openWriteDialog('switch_on_power_factor')

    expect(warningMock).toHaveBeenCalledWith('仅管理员可执行参数写入。')
    expect(state!.writeDialogVisible.value).toBe(false)
    scope.stop()
  })

  it('skips duplicate parameter writes when target equals current snapshot', async () => {
    const loadPageMock = vi.fn().mockResolvedValue(undefined)
    const scope = effectScope()
    const state = scope.run(() => useControlConsoleActions({
      deviceId: computed(() => 2),
      canManageDevices: computed(() => true),
      canControlDevices: computed(() => true),
      currentRole: computed(() => 'admin'),
      isAdmin: computed(() => true),
      archive: computed(() => ({ name: '设备-CAP-001' })),
      runtimeStatus: computed(() => ({ is_active: true, is_online: true })),
      controlProfile: ref({
        device_id: 2,
        source_status: 'fresh',
        capabilities: baseCapabilities,
        switch_on_power_factor: 92,
      } as any),
      controlCapabilities: computed(() => baseCapabilities),
      controlLogs: ref([]),
      loadPage: loadPageMock,
    }))

    state!.openWriteDialog('switch_on_power_factor')
    state!.writeForm.value.target_value = 0.92
    await state!.submitParameterWrite()

    expect(warningMock).toHaveBeenCalledWith('目标值与当前快照一致，无需重复下发')
    expect(writeProfileMock).not.toHaveBeenCalled()
    expect(loadPageMock).not.toHaveBeenCalled()
    scope.stop()
  })

  it('blocks write dialog for parameters outside backend writable allowlist', () => {
    const scope = effectScope()
    const state = scope.run(() => useControlConsoleActions({
      deviceId: computed(() => 2),
      canManageDevices: computed(() => true),
      canControlDevices: computed(() => true),
      currentRole: computed(() => 'admin'),
      isAdmin: computed(() => true),
      archive: computed(() => ({ name: '设备-CAP-001' })),
      runtimeStatus: computed(() => ({ is_active: true, is_online: true })),
      controlProfile: ref({
        device_id: 2,
        source_status: 'fresh',
        capabilities: baseCapabilities,
        baud_rate: 9600,
      } as any),
      controlCapabilities: computed(() => baseCapabilities),
      controlLogs: ref([]),
      loadPage: vi.fn().mockResolvedValue(undefined),
    }))

    state!.openWriteDialog('baud_rate')

    expect(warningMock).toHaveBeenCalledWith('真实网关暂未确认该参数写入编码，当前暂不开放写入。')
    expect(state!.writeDialogVisible.value).toBe(false)
    scope.stop()
  })

  it('blocks unsupported remote command from backend capabilities', async () => {
    const loadPageMock = vi.fn().mockResolvedValue(undefined)
    const scope = effectScope()
    const state = scope.run(() => useControlConsoleActions({
      deviceId: computed(() => 2),
      canManageDevices: computed(() => true),
      canControlDevices: computed(() => true),
      currentRole: computed(() => 'admin'),
      isAdmin: computed(() => true),
      archive: computed(() => ({ name: '设备-CAP-001' })),
      runtimeStatus: computed(() => ({ is_active: true, is_online: true })),
      controlProfile: ref({
        device_id: 2,
        source_status: 'fresh',
        capabilities: baseCapabilities,
      } as any),
      controlCapabilities: computed(() => baseCapabilities),
      controlLogs: ref([]),
      loadPage: loadPageMock,
    }))

    state!.handleActionCard('reset_alarm')
    await Promise.resolve()

    expect(warningMock).toHaveBeenCalledWith('真实网关暂未提供报警复位寄存器/功能码')
    expect(sendRemoteCommandMock).not.toHaveBeenCalled()
    expect(loadPageMock).not.toHaveBeenCalled()
    scope.stop()
  })

  it('uses live monitor control mode before profile mode for manual switch gating', () => {
    const scope = effectScope()
    const state = scope.run(() => useControlConsoleActions({
      deviceId: computed(() => 2),
      canManageDevices: computed(() => true),
      canControlDevices: computed(() => true),
      currentRole: computed(() => 'admin'),
      isAdmin: computed(() => true),
      archive: computed(() => ({ name: '设备-CAP-001' })),
      runtimeStatus: computed(() => ({ is_active: true, is_online: true })),
      controlProfile: ref({
        device_id: 2,
        source_status: 'fresh',
        capabilities: baseCapabilities,
        terminal_assignment_scheme: '自动模式',
      } as any),
      controlCapabilities: computed(() => baseCapabilities),
      controlLogs: ref([]),
      monitorControlMode: computed(() => ({
        value: '手动',
        source: 'telemetry',
        state: 'live',
      })),
      loadPage: vi.fn().mockResolvedValue(undefined),
    }))

    expect(state!.currentControlModeLabel.value).toBe('手动')
    expect(state!.canRunManualSwitch.value).toBe(true)
    scope.stop()
  })

  it('blocks manual switch when latest successful mode log switched back to auto', () => {
    const scope = effectScope()
    const state = scope.run(() => useControlConsoleActions({
      deviceId: computed(() => 2),
      canManageDevices: computed(() => true),
      canControlDevices: computed(() => true),
      currentRole: computed(() => 'admin'),
      isAdmin: computed(() => true),
      archive: computed(() => ({ name: '设备-CAP-001' })),
      runtimeStatus: computed(() => ({ is_active: true, is_online: true })),
      controlProfile: ref({
        device_id: 2,
        source_status: 'fresh',
        capabilities: baseCapabilities,
        terminal_assignment_scheme: '手动模式',
      } as any),
      controlCapabilities: computed(() => baseCapabilities),
      controlLogs: ref([
        {
          id: 81,
          device_id: 2,
          action: 'manual_switch',
          target_status: true,
          created_at: '2026-05-17T21:03:43',
          result: 'success',
          reason: '控制台控制模式切换 -> 自动模式 | 设备回执已处理: 已切回自动模式',
        },
      ] as any),
      monitorControlMode: computed(() => ({
        value: '手动',
        source: 'telemetry',
        state: 'live',
      })),
      loadPage: vi.fn().mockResolvedValue(undefined),
    }))

    expect(state!.currentControlModeLabel.value).toBe('自动')
    expect(state!.canRunManualSwitch.value).toBe(false)
    expect(state!.manualSwitchDisabledReason.value).toContain('当前为自动模式')
    scope.stop()
  })

  it('sends switch_control_mode semantic command for mode switching', async () => {
    const loadPageMock = vi.fn().mockResolvedValue(undefined)
    sendRemoteCommandMock.mockResolvedValue({
      accepted: true,
      status: 'accepted',
      message: '控制模式切换指令已发送',
    })

    const scope = effectScope()
    const state = scope.run(() => useControlConsoleActions({
      deviceId: computed(() => 2),
      canManageDevices: computed(() => true),
      canControlDevices: computed(() => true),
      currentRole: computed(() => 'admin'),
      isAdmin: computed(() => true),
      archive: computed(() => ({ name: '设备-CAP-001' })),
      runtimeStatus: computed(() => ({ is_active: true, is_online: true })),
      controlProfile: ref({
        device_id: 2,
        source_status: 'fresh',
        capabilities: baseCapabilities,
        terminal_assignment_scheme: '自动模式',
      } as any),
      controlCapabilities: computed(() => baseCapabilities),
      controlLogs: ref([]),
      loadPage: loadPageMock,
    }))

    state!.handleActionCard('switch_control_mode')
    await Promise.resolve()
    await Promise.resolve()

    expect(sendRemoteCommandMock).toHaveBeenCalledWith(2, {
      action: 'switch_control_mode',
      reason: '控制台控制模式切换 -> 手动模式',
    })
    expect(loadPageMock).toHaveBeenCalled()
    scope.stop()
  })
})
