import { computed, effectScope, ref, nextTick } from 'vue'
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
import type { MonitorOverview } from '@/api/deviceMonitor'

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

  it('sets load error and skips control profile for pending archive devices', async () => {
    getDeviceMonitorOverviewMock.mockResolvedValue({
      archive: {
        id: 31,
        name: '待完善设备-CAP-NEW',
        device_type: 'capacitor_bank_controller',
        device_subtype: 'capacitor_bank_controller',
        archive_status: 'pending',
      },
      runtime_status: {
        device_id: 31,
        is_online: false,
      },
    })

    const scope = effectScope()
    const state = scope.run(() => useControlConsoleData({
      deviceId: computed(() => 31),
      enableLifecycle: false,
    }))

    expect(state).toBeTruthy()
    await state!.loadPage()

    expect(state!.loadError.value).toBe('请先补全设备档案后再进入监控或控制台。')
    expect(getDeviceMonitorControlLogsMock).not.toHaveBeenCalled()
    expect(getCompensationCapBankControlProfileMock).not.toHaveBeenCalled()
    scope.stop()
  })

  it('degrades gracefully when control profile request fails', async () => {
    getDeviceMonitorOverviewMock.mockResolvedValue({
      archive: {
        id: 2,
        name: '测试补偿柜',
        device_type: 'capacitor_bank_controller',
        device_subtype: 'capacitor_bank_controller',
      },
      runtime_status: {
        device_id: 2,
        is_online: true,
      },
    })
    getCompensationCapBankControlProfileMock.mockRejectedValue(new Error('参数档案接口异常'))
    getDeviceMonitorControlLogsMock.mockResolvedValue({ items: [] })

    const scope = effectScope()
    const state = scope.run(() => useControlConsoleData({
      deviceId: computed(() => 2),
      enableLifecycle: false,
    }))

    expect(state).toBeTruthy()
    await state!.loadPage()

    expect(state!.loadError.value).toBe('')
    expect(state!.profileWarning.value).toBe('参数档案接口异常')
    expect(state!.isCapacitorBankController.value).toBe(true)
    expect(state!.controlProfile.value?.capabilities.supports_remote_control).toBe(true)
    expect(state!.controlProfile.value?.capabilities.supports_write).toBe(false)
    expect(state!.controlProfile.value?.source_status).toBe('unknown')
    scope.stop()
  })

  it('loads embedded console data from an existing overview without fetching overview again', async () => {
    getCompensationCapBankControlProfileMock.mockResolvedValue({
      device_id: 2,
      source_status: 'fresh',
      capabilities: {
        supports_read: true,
        supports_write: true,
        supports_remote_control: true,
      },
      split_capacity_expansion: {
        phase_a_groups: [],
        phase_b_groups: [],
        phase_c_groups: [],
      },
      common_capacity_expansion: {
        common_1_groups: [],
        common_2_groups: [],
        common_3_groups: [],
      },
    })
    getDeviceMonitorControlLogsMock.mockResolvedValue({ items: [{ id: 1, result: 'success' }] })

    const scope = effectScope()
    const state = scope.run(() => useControlConsoleData({
      deviceId: computed(() => 2),
      enableLifecycle: false,
    }))

    expect(state).toBeTruthy()
    const overview: MonitorOverview = {
      archive: {
        id: 2,
        name: '测试补偿柜',
        device_type: 'capacitor_bank_controller',
        device_subtype: 'capacitor_bank_controller',
      },
      runtime_status: {
        device_id: 2,
        is_online: true,
      },
      realtime: null,
      recent_alarms: [],
      recent_control_logs: [],
      ingestion_health: {},
      compensation_monitor: null,
    }
    await state!.loadPageWithOverview(overview)

    expect(getDeviceMonitorOverviewMock).not.toHaveBeenCalled()
    expect(getDeviceMonitorControlLogsMock).toHaveBeenCalledWith(2, { limit: 10, hours: 168 })
    expect(state!.loadError.value).toBe('')
    expect(state!.controlLogs.value).toEqual([{ id: 1, result: 'success' }])
    expect(state!.isCapacitorBankController.value).toBe(true)
    scope.stop()
  })

  it('does not auto load on device id changes when lifecycle is disabled', async () => {
    const deviceId = ref(2)
    const scope = effectScope()
    const state = scope.run(() => useControlConsoleData({
      deviceId: computed(() => deviceId.value),
      enableLifecycle: false,
    }))

    expect(state).toBeTruthy()
    deviceId.value = 3
    await nextTick()
    await Promise.resolve()

    expect(getDeviceMonitorOverviewMock).not.toHaveBeenCalled()
    scope.stop()
  })

  it('refreshes when websocket emits current device control log update', async () => {
    getDeviceMonitorOverviewMock.mockResolvedValue({
      archive: {
        id: 2,
        name: '测试补偿柜',
        device_type: 'capacitor_bank_controller',
        device_subtype: 'capacitor_bank_controller',
      },
      runtime_status: {
        device_id: 2,
        is_online: true,
      },
    })
    getCompensationCapBankControlProfileMock.mockResolvedValue({
      device_id: 2,
      source_status: 'fresh',
      capabilities: {
        supports_read: true,
        supports_write: true,
        supports_remote_control: true,
      },
      split_capacity_expansion: {
        phase_a_groups: [],
        phase_b_groups: [],
        phase_c_groups: [],
      },
      common_capacity_expansion: {
        common_1_groups: [],
        common_2_groups: [],
        common_3_groups: [],
      },
    })
    getDeviceMonitorControlLogsMock.mockResolvedValue({ items: [] })
    const socketMessage = ref(null as any)

    const scope = effectScope()
    const state = scope.run(() => useControlConsoleData({
      deviceId: computed(() => 2),
      enableLifecycle: false,
      socketMessage,
    }))

    await state!.loadPage()
    expect(getDeviceMonitorOverviewMock).toHaveBeenCalledTimes(1)

    socketMessage.value = {
      type: 'device_control_log_update',
      data: {
        device_id: 2,
        command_id: '91',
        result: 'success',
      },
    }
    await nextTick()
    await Promise.resolve()

    expect(getDeviceMonitorOverviewMock).toHaveBeenCalledTimes(2)
    scope.stop()
  })

  it('ignores websocket control log updates for other devices', async () => {
    getDeviceMonitorOverviewMock.mockResolvedValue({
      archive: {
        id: 2,
        name: '测试补偿柜',
        device_type: 'capacitor_bank_controller',
        device_subtype: 'capacitor_bank_controller',
      },
      runtime_status: {
        device_id: 2,
        is_online: true,
      },
    })
    getCompensationCapBankControlProfileMock.mockResolvedValue({
      device_id: 2,
      source_status: 'fresh',
      capabilities: {
        supports_read: true,
        supports_write: true,
        supports_remote_control: true,
      },
      split_capacity_expansion: {
        phase_a_groups: [],
        phase_b_groups: [],
        phase_c_groups: [],
      },
      common_capacity_expansion: {
        common_1_groups: [],
        common_2_groups: [],
        common_3_groups: [],
      },
    })
    getDeviceMonitorControlLogsMock.mockResolvedValue({ items: [] })
    const socketMessage = ref(null as any)

    const scope = effectScope()
    const state = scope.run(() => useControlConsoleData({
      deviceId: computed(() => 2),
      enableLifecycle: false,
      socketMessage,
    }))

    await state!.loadPage()
    socketMessage.value = {
      type: 'device_control_log_update',
      data: {
        device_id: 3,
        command_id: '91',
        result: 'success',
      },
    }
    await nextTick()
    await Promise.resolve()

    expect(getDeviceMonitorOverviewMock).toHaveBeenCalledTimes(1)
    scope.stop()
  })
})
