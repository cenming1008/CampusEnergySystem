import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import { useDashboardRealtime } from '../useDashboardRealtime'

const { getAnalysisMock, getHistoryMock } = vi.hoisted(() => ({
  getAnalysisMock: vi.fn(),
  getHistoryMock: vi.fn(),
}))

vi.mock('@/api/telemetry', () => ({
  getAnalysis: getAnalysisMock,
  getHistory: getHistoryMock,
}))

describe('useDashboardRealtime', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-03-26T12:40:00'))
    getAnalysisMock.mockReset()
    getHistoryMock.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('loads analysis and history into realtime metrics and trend data', async () => {
    getAnalysisMock.mockResolvedValue({
      current_power: 65.2,
      today_energy: 180.4,
      current: 12.4,
      voltage: 219.5,
    })
    getHistoryMock.mockResolvedValue([
      { timestamp: '2026-03-26T10:00:00', flow_rate: 40 },
      { timestamp: '2026-03-26T11:00:00', flow_rate: 50 },
    ])

    const state = useDashboardRealtime({
      currentDeviceId: ref(1),
      deviceList: ref([{ id: 1, name: '主负载', sn: 'L-1', device_type: 'load', is_active: true }]),
      latestMessage: ref(null),
    })

    await state.loadDeviceData()

    expect(state.realTimeData.power).toBe(65.2)
    expect(state.realTimeData.energy).toBe(180.4)
    expect(state.realTimeData.current).toBe(12.4)
    expect(state.realTimeData.voltage).toBe(219.5)
    expect(state.energyTrendData.times).toEqual(['10:00:00', '11:00:00'])
    expect(state.energyTrendData.values).toEqual([40, 50])
  })

  it('applies websocket telemetry updates only for the active device', async () => {
    const latestMessage = ref(null as null | {
      type?: string
      data?: { device_id?: number; power?: number; current?: number; voltage?: number; timestamp?: string }
    })
    const state = useDashboardRealtime({
      currentDeviceId: ref(7),
      deviceList: ref([{ id: 7, name: '七号设备', sn: 'D-7', device_type: 'load', is_active: true }]),
      latestMessage,
    })

    latestMessage.value = {
      type: 'telemetry_update',
      data: {
        device_id: 7,
        power: -88.6,
        current: 9.5,
        voltage: 221.1,
        timestamp: '2026-03-26T12:34:56',
      },
    }
    await nextTick()

    expect(state.realTimeData.power).toBe(-88.6)
    expect(state.displayPower.value).toBe(88.6)
    expect(state.realTimeData.current).toBe(9.5)
    expect(state.energyTrendData.times.at(-1)).toBe('12:34:56')
    expect(state.energyTrendData.values.at(-1)).toBe(88.6)

    latestMessage.value = {
      type: 'telemetry_update',
      data: {
        device_id: 8,
        power: 10,
        timestamp: '2026-03-26T12:35:00',
      },
    }
    await nextTick()

    expect(state.realTimeData.power).toBe(-88.6)
    expect(state.energyTrendData.times).toHaveLength(1)
  })
})
