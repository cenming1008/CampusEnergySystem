import { computed, defineComponent, effectScope, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useStorageMonitor } from '../useStorageMonitor'

const {
  getStorageTelemetryLatestMock,
  getStorageTelemetryHistoryMock,
} = vi.hoisted(() => ({
  getStorageTelemetryLatestMock: vi.fn(),
  getStorageTelemetryHistoryMock: vi.fn(),
}))

vi.mock('@/api/storage', () => ({
  getStorageTelemetryLatest: getStorageTelemetryLatestMock,
  getStorageTelemetryHistory: getStorageTelemetryHistoryMock,
}))

describe('useStorageMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
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
})
