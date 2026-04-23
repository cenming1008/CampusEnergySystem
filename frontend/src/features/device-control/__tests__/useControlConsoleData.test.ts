import { computed, effectScope } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const {
  getDeviceMonitorOverviewMock,
  getDeviceMonitorControlLogsMock,
  getCompensationCapBankControlProfileMock,
} = vi.hoisted(() => ({
  getDeviceMonitorOverviewMock: vi.fn(),
  getDeviceMonitorControlLogsMock: vi.fn(),
  getCompensationCapBankControlProfileMock: vi.fn(),
}))

vi.mock('@/api/deviceMonitor', () => ({
  getDeviceMonitorOverview: getDeviceMonitorOverviewMock,
  getDeviceMonitorControlLogs: getDeviceMonitorControlLogsMock,
}))

vi.mock('@/api/compensation', () => ({
  getCompensationCapacitorBankControlProfile: getCompensationCapBankControlProfileMock,
}))

import { useControlConsoleData } from '../useControlConsoleData'

describe('useControlConsoleData', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('sets load error when device is not capacitor bank controller', async () => {
    getDeviceMonitorOverviewMock.mockResolvedValue({
      archive: {
        id: 2,
        name: '测试设备',
        device_type: 'svg',
        device_subtype: 'svg',
      },
      runtime_status: {
        device_id: 2,
        is_online: true,
      },
    })
    getCompensationCapBankControlProfileMock.mockResolvedValue({
      device_id: 2,
      source_status: 'empty',
      capabilities: {
        supports_read: false,
        supports_write: false,
        supports_remote_control: false,
      },
    })
    getDeviceMonitorControlLogsMock.mockResolvedValue({ items: [] })

    const scope = effectScope()
    const state = scope.run(() => useControlConsoleData({
      deviceId: computed(() => 2),
      enableLifecycle: false,
    }))

    expect(state).toBeTruthy()
    await state!.loadPage()

    expect(state!.loadError.value).toBe('当前设备不是电容补偿控制器，暂不支持进入控制台。')
    expect(state!.isCapacitorBankController.value).toBe(false)
    scope.stop()
  })
})
