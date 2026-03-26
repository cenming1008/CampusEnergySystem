import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { useDashboardDeviceSelection } from '../useDashboardDeviceSelection'

const { getDevicesMock } = vi.hoisted(() => ({
  getDevicesMock: vi.fn(),
}))

vi.mock('@/api/device', () => ({
  getDevices: getDevicesMock,
}))

describe('useDashboardDeviceSelection', () => {
  beforeEach(() => {
    getDevicesMock.mockReset()
  })

  it('prefers a load device as the default selection after loading', async () => {
    getDevicesMock.mockResolvedValue([
      { id: 1, name: '水表', sn: 'W-1', device_type: 'water_meter', is_active: true },
      { id: 2, name: '主负载', sn: 'L-1', device_type: 'load', is_active: true },
    ])

    const state = useDashboardDeviceSelection()
    const devices = await state.loadDeviceList()
    await nextTick()

    expect(devices).toHaveLength(2)
    expect(state.totalDevices.value).toBe(2)
    expect(state.onlineDevices.value).toBe(2)
    expect(state.currentDeviceId.value).toBe(2)
    expect(state.currentDevice.value?.name).toBe('主负载')
  })

  it('clears stale selection when selected device is no longer returned', async () => {
    getDevicesMock.mockResolvedValueOnce([
      { id: 2, name: '主负载', sn: 'L-1', device_type: 'load', is_active: true },
    ])
    const state = useDashboardDeviceSelection()
    await state.loadDeviceList()
    expect(state.currentDeviceId.value).toBe(2)

    getDevicesMock.mockResolvedValueOnce([
      { id: 3, name: '备用电表', sn: 'M-1', device_type: 'meter', is_active: false },
    ])
    await state.loadDeviceList()
    await nextTick()

    expect(state.currentDeviceId.value).toBe(3)
    expect(state.currentDevice.value?.name).toBe('备用电表')
    expect(state.onlineDevices.value).toBe(0)
  })
})
