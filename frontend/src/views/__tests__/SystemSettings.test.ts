import { beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import SystemSettings from '../SystemSettings.vue'

const {
  requestGetMock,
  requestPostMock,
  requestDeleteMock,
  getDevicesMock,
  cleanupDataMock,
  getCleanupStatsMock,
  cleanupAllDataMock,
  successMock,
  warningMock,
  errorMock,
  confirmMock,
} = vi.hoisted(() => ({
  requestGetMock: vi.fn(),
  requestPostMock: vi.fn(),
  requestDeleteMock: vi.fn(),
  getDevicesMock: vi.fn(),
  cleanupDataMock: vi.fn(),
  getCleanupStatsMock: vi.fn(),
  cleanupAllDataMock: vi.fn(),
  successMock: vi.fn(),
  warningMock: vi.fn(),
  errorMock: vi.fn(),
  confirmMock: vi.fn(),
}))

vi.mock('@/utils/request', () => ({
  default: {
    get: requestGetMock,
    post: requestPostMock,
    delete: requestDeleteMock,
  },
}))

vi.mock('@/api/device', () => ({
  getDevices: getDevicesMock,
}))

vi.mock('@/api/dataCleanup', () => ({
  cleanupData: cleanupDataMock,
  getCleanupStats: getCleanupStatsMock,
  cleanupAllData: cleanupAllDataMock,
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual<typeof import('element-plus')>('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: successMock,
      warning: warningMock,
      error: errorMock,
    },
    ElMessageBox: {
      confirm: confirmMock,
    },
  }
})

function mountView() {
  return shallowMount(SystemSettings, {
    global: {
      stubs: {
        'el-tabs': true,
        'el-tab-pane': true,
        'el-form': true,
        'el-form-item': true,
        'el-select': true,
        'el-option': true,
        'el-input-number': true,
        'el-checkbox': true,
        'el-button': true,
        'el-empty': true,
        'el-alert': true,
        'el-divider': true,
        'el-icon': true,
        'el-table': true,
        'el-table-column': true,
        'el-tag': true,
      },
      directives: {
        loading: () => undefined,
      },
    },
  })
}

async function flushAsync() {
  await Promise.resolve()
  await Promise.resolve()
  await Promise.resolve()
}

describe('SystemSettings view', () => {
  beforeEach(() => {
    requestGetMock.mockReset()
    requestPostMock.mockReset()
    requestDeleteMock.mockReset()
    getDevicesMock.mockReset()
    cleanupDataMock.mockReset()
    getCleanupStatsMock.mockReset()
    cleanupAllDataMock.mockReset()
    successMock.mockReset()
    warningMock.mockReset()
    errorMock.mockReset()
    confirmMock.mockReset()
    localStorage.clear()
  })

  it('loads devices, system status, metrics and can load cleanup stats', async () => {
    getDevicesMock.mockResolvedValue([
      { id: 1, name: '一号设备', sn: 'SN-1', device_type: 'load', is_active: true },
    ])
    requestGetMock.mockImplementation(async (url: string) => {
      if (url === '/health') {
        return { status: 'healthy', services: { database: 'healthy' } }
      }
      if (url === '/devices/ingestion-records') {
        return { items: [{ id: 9, topic: 'mine/device/1', status: 'success' }] }
      }
      if (url === '/metrics') {
        return 'mine_http_requests_total 10'
      }
      return {}
    })
    getCleanupStatsMock.mockResolvedValue({
      energy_data: { total: 100 },
      alarm_data: { total: 5 },
    })

    const wrapper = mountView()
    await flushAsync()

    const vm = wrapper.vm as unknown as {
      deviceList: Array<{ name: string }>
      systemStatus: { status?: string } | null
      metricsText: string
      ingestionRecords: Array<{ id: number }>
      loadCleanupStats: () => Promise<void>
      cleanupStats: { energy_data?: { total?: number } } | null
    }
    await vm.loadCleanupStats()

    expect(getDevicesMock).toHaveBeenCalledTimes(1)
    expect(requestGetMock).toHaveBeenCalledWith('/health')
    expect(requestGetMock).toHaveBeenCalledWith('/metrics', expect.objectContaining({
      responseType: 'text',
    }))
    expect(getCleanupStatsMock.mock.calls.length).toBeGreaterThanOrEqual(1)
    expect(vm.deviceList[0].name).toBe('一号设备')
    expect(vm.systemStatus?.status).toBe('healthy')
    expect(vm.metricsText).toContain('mine_http_requests_total')
    expect(vm.ingestionRecords[0].id).toBe(9)
    expect(vm.cleanupStats?.energy_data?.total).toBe(100)
  })

  it('warns when generating device data without selecting a device', async () => {
    getDevicesMock.mockResolvedValue([])
    requestGetMock.mockResolvedValue({})
    getCleanupStatsMock.mockResolvedValue({})

    const wrapper = mountView()
    await flushAsync()

    await (wrapper.vm as unknown as { generateDeviceData: () => Promise<void> }).generateDeviceData()

    expect(warningMock).toHaveBeenCalledWith('请选择设备')
    expect(requestPostMock).not.toHaveBeenCalled()
  })

  it('generates device data for the selected device', async () => {
    getDevicesMock.mockResolvedValue([])
    requestGetMock.mockResolvedValue({})
    getCleanupStatsMock.mockResolvedValue({})
    requestPostMock.mockResolvedValue({ message: '生成完成' })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      generateForm: {
        device_id?: number
        days: number
        interval_minutes: number
        data_type: string
        clear_existing: boolean
      }
      generateDeviceData: () => Promise<void>
    }
    vm.generateForm.device_id = 7
    vm.generateForm.days = 30
    vm.generateForm.interval_minutes = 15
    vm.generateForm.data_type = 'solar'
    vm.generateForm.clear_existing = true

    await vm.generateDeviceData()

    expect(requestPostMock).toHaveBeenCalledWith('/data-generator/generate/device/7', {
      days: 30,
      interval_minutes: 15,
      data_type: 'solar',
      clear_existing: true,
    })
    expect(successMock).toHaveBeenCalledWith('生成完成')
  })

  it('generates data for all devices after confirmation', async () => {
    getDevicesMock.mockResolvedValue([])
    requestGetMock.mockResolvedValue({})
    getCleanupStatsMock.mockResolvedValue({})
    confirmMock.mockResolvedValue(undefined)
    requestPostMock.mockResolvedValue({ message: '批量生成完成' })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      generateForm: {
        days: number
        interval_minutes: number
        clear_existing: boolean
      }
      generateAllData: () => Promise<void>
    }
    vm.generateForm.days = 10
    vm.generateForm.interval_minutes = 60
    vm.generateForm.clear_existing = false

    await vm.generateAllData()

    expect(confirmMock).toHaveBeenCalledTimes(1)
    expect(requestPostMock).toHaveBeenCalledWith('/data-generator/generate/all', {
      days: 10,
      interval_minutes: 60,
      clear_existing: false,
    })
    expect(successMock).toHaveBeenCalledWith('批量生成完成')
  })

  it('clears selected device data after confirmation', async () => {
    getDevicesMock.mockResolvedValue([])
    requestGetMock.mockImplementation(async (url: string) => {
      if (url === '/data-generator/stats/5') {
        return { total_count: 12, days: 2 }
      }
      return {}
    })
    getCleanupStatsMock.mockResolvedValue({})
    confirmMock.mockResolvedValue(undefined)
    requestDeleteMock.mockResolvedValue({ message: 'ok' })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      selectedDeviceForStats?: number
      clearDeviceData: () => Promise<void>
      dataStats: { total_count?: number } | null
    }
    vm.selectedDeviceForStats = 5

    await vm.clearDeviceData()
    await flushAsync()

    expect(requestDeleteMock).toHaveBeenCalledWith('/data-generator/clear/5')
    expect(successMock).toHaveBeenCalledWith('数据已清除')
    expect(vm.dataStats?.total_count).toBe(12)
  })

  it('cleans historical data and refreshes cleanup stats', async () => {
    getDevicesMock.mockResolvedValue([])
    requestGetMock.mockResolvedValue({})
    getCleanupStatsMock.mockResolvedValueOnce({}).mockResolvedValueOnce({
      energy_data: { total: 20 },
      alarm_data: { total: 2 },
    })
    confirmMock.mockResolvedValue(undefined)
    cleanupDataMock.mockResolvedValue({
      status: 'success',
      total_deleted: 18,
      energy_data: 12,
      alarm_data: 4,
      carbon_emission: 2,
      errors: [],
    })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      cleanupHours: number
      handleCleanupData: () => Promise<void>
      cleanupStats: { energy_data?: { total?: number } } | null
    }
    vm.cleanupHours = 6

    await vm.handleCleanupData()

    expect(cleanupDataMock).toHaveBeenCalledWith(6)
    expect(successMock).toHaveBeenCalledWith(expect.objectContaining({
      message: '清理完成！共删除 18 条记录',
    }))
    expect(vm.cleanupStats?.energy_data?.total).toBe(20)
  })

  it('cleans all data only after double confirmation', async () => {
    getDevicesMock.mockResolvedValue([])
    requestGetMock.mockResolvedValue({})
    getCleanupStatsMock.mockResolvedValueOnce({}).mockResolvedValueOnce({
      energy_data: { total: 0 },
      alarm_data: { total: 0 },
    })
    confirmMock.mockResolvedValue(undefined)
    cleanupAllDataMock.mockResolvedValue({
      status: 'success',
      total_deleted: 99,
      energy_data: 80,
      alarm_data: 10,
      carbon_emission: 9,
      errors: [],
    })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      handleCleanupAllData: () => Promise<void>
    }

    await vm.handleCleanupAllData()

    expect(confirmMock).toHaveBeenCalledTimes(2)
    expect(cleanupAllDataMock).toHaveBeenCalledTimes(1)
    expect(successMock).toHaveBeenCalledWith(expect.objectContaining({
      message: '清除完成！共删除 99 条记录',
    }))
  })
})
