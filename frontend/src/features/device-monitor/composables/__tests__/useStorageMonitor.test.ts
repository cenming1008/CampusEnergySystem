import { computed, defineComponent, effectScope, ref } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useStorageMonitor } from '../useStorageMonitor'

const {
  getStorageTelemetryLatestMock,
  getStorageTelemetryHistoryMock,
  getStorageProfileMock,
  getStorageControlCapabilitiesMock,
  sendStorageControlMock,
  updateStorageProfileMock,
  getDeviceMonitorControlLogsMock,
} = vi.hoisted(() => ({
  getStorageTelemetryLatestMock: vi.fn(),
  getStorageTelemetryHistoryMock: vi.fn(),
  getStorageProfileMock: vi.fn(),
  getStorageControlCapabilitiesMock: vi.fn(),
  sendStorageControlMock: vi.fn(),
  updateStorageProfileMock: vi.fn(),
  getDeviceMonitorControlLogsMock: vi.fn(),
}))

vi.mock('@/api/storage', () => ({
  getStorageTelemetryLatest: getStorageTelemetryLatestMock,
  getStorageTelemetryHistory: getStorageTelemetryHistoryMock,
  getStorageProfile: getStorageProfileMock,
  getStorageControlCapabilities: getStorageControlCapabilitiesMock,
  sendStorageControl: sendStorageControlMock,
  updateStorageProfile: updateStorageProfileMock,
}))

vi.mock('@/api/deviceMonitor', () => ({
  getDeviceMonitorControlLogs: getDeviceMonitorControlLogsMock,
}))

describe('useStorageMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
    getStorageProfileMock.mockResolvedValue({
      device_id: 2,
      rated_energy_kwh: 500,
      rated_power_kw: 250,
      charge_efficiency: 0.95,
      discharge_efficiency: 0.95,
      soc_min: 10,
      soc_max: 90,
      soc_soft_min: 15,
      soc_soft_max: 85,
      data_source: 'configured',
      ems_auto_enabled: false,
    })
    getStorageControlCapabilitiesMock.mockResolvedValue({
      commands: ['set_active_power', 'set_control_mode', 'stop'],
      sources: ['manual', 'rule', 'day_ahead'],
      control_modes: ['auto', 'manual'],
      power_sign: { charge: 'positive', discharge: 'negative' },
      ems_auto_enabled: false,
      ems_global_enabled: false,
    })
    getDeviceMonitorControlLogsMock.mockResolvedValue({ items: [] })
  })

  it('does not start its own polling when lifecycle is disabled by the monitor page', async () => {
    vi.useFakeTimers()
    getStorageTelemetryLatestMock.mockResolvedValue({
      device_id: 2,
      timestamp: '2026-05-20T10:00:00+08:00',
      soc: 80,
    })

    const Harness = defineComponent({
      setup() {
        useStorageMonitor({
          deviceId: computed(() => 2),
          overview: ref(null),
          timeRange: ref(null),
          enableLifecycle: false,
        })
        return {}
      },
      template: '<div />',
    })

    const wrapper = mount(Harness)
    await vi.advanceTimersByTimeAsync(5000)

    expect(getStorageTelemetryLatestMock).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('refreshes latest telemetry when called explicitly', async () => {
    getStorageTelemetryLatestMock.mockResolvedValue({
      device_id: 2,
      timestamp: '2026-05-20T10:00:00+08:00',
      soc: 80,
    })

    const scope = effectScope()
    const monitor = scope.run(() => useStorageMonitor({
      deviceId: computed(() => 2),
      overview: ref(null),
      timeRange: ref(null),
      enableLifecycle: false,
    }))

    await monitor!.refreshStorageData()

    expect(getStorageTelemetryLatestMock).toHaveBeenCalledTimes(1)
    expect(monitor!.latestTelemetry.value?.soc).toBe(80)
    scope.stop()
  })

  it.each([
    ['simulated', '仿真数据', 80, '充电'],
    ['real', '真实设备', -80, '放电'],
  ])('maps %s telemetry to source and signed target labels', async (dataSource, label, target, direction) => {
    getStorageTelemetryLatestMock.mockResolvedValue({
      device_id: 2,
      timestamp: '2026-07-17T10:00:00+08:00',
      data_source: dataSource,
      target_active_power: target,
    })
    const scope = effectScope()
    const monitor = scope.run(() => useStorageMonitor({
      deviceId: computed(() => 2),
      overview: ref(null),
      timeRange: ref(null),
      enableLifecycle: false,
    }))!

    await monitor.refreshStorageData()

    expect(monitor.dataSourceLabel.value).toBe(label)
    expect(monitor.targetPowerDirectionLabel.value).toBe(direction)
    scope.stop()
  })

  it('keeps the requested manual power sign and records accepted without fabricating success', async () => {
    sendStorageControlMock.mockResolvedValue({
      accepted: true,
      status: 'accepted',
      command_id: '42',
      message: '储能控制命令已入队',
    })
    const scope = effectScope()
    const monitor = scope.run(() => useStorageMonitor({
      deviceId: computed(() => 2),
      overview: ref(null),
      timeRange: ref(null),
      enableLifecycle: false,
    }))!

    await monitor.sendManualPower(-80)

    expect(sendStorageControlMock).toHaveBeenCalledWith(2, {
      command: 'set_active_power',
      source: 'manual',
      target_active_power: -80,
    })
    expect(monitor.commandTimeline.value[0]).toMatchObject({
      commandId: '42',
      result: 'accepted',
    })
    expect(monitor.commandTimeline.value[0].result).not.toBe('success')
    scope.stop()
  })

  it('refreshes the command timeline from the websocket control-log event', async () => {
    const socketMessage = ref<Record<string, unknown> | null>(null)
    getDeviceMonitorControlLogsMock.mockResolvedValueOnce({
      items: [{
        id: 42,
        device_id: 2,
        action: 'set_active_power',
        target_status: true,
        result: 'accepted',
        reason: '{"target_active_power":-80}',
        created_at: '2026-07-17T10:00:00+08:00',
      }],
    }).mockResolvedValueOnce({
      items: [{
        id: 42,
        device_id: 2,
        action: 'set_active_power',
        target_status: true,
        result: 'running',
        reason: '{"target_active_power":-80}',
        created_at: '2026-07-17T10:00:00+08:00',
      }],
    })
    const scope = effectScope()
    const monitor = scope.run(() => useStorageMonitor({
      deviceId: computed(() => 2),
      overview: ref(null),
      timeRange: ref(null),
      socketMessage,
      enableLifecycle: false,
    }))!
    await monitor.loadControlLogs()

    socketMessage.value = {
      type: 'device_control_log_update',
      data: { device_id: 2, command_id: '42', result: 'running' },
    }
    await flushPromises()

    expect(getDeviceMonitorControlLogsMock).toHaveBeenCalledTimes(2)
    expect(monitor.commandTimeline.value[0].result).toBe('running')
    scope.stop()
  })
})
