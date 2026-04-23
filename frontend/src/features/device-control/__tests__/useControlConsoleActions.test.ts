import { computed, effectScope, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const {
  warningMock,
  successMock,
  errorMock,
  confirmMock,
  writeProfileMock,
} = vi.hoisted(() => ({
  warningMock: vi.fn(),
  successMock: vi.fn(),
  errorMock: vi.fn(),
  confirmMock: vi.fn(),
  writeProfileMock: vi.fn(),
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
  sendCompensationCapacitorBankRemoteCommand: vi.fn(),
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
})
