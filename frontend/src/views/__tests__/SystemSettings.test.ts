import { beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import SystemSettings from '../SystemSettings.vue'

const {
  requestGetMock,
  requestPostMock,
  cleanupDataMock,
  getCleanupStatsMock,
  cleanupAllDataMock,
  successMock,
  errorMock,
  confirmMock,
} = vi.hoisted(() => ({
  requestGetMock: vi.fn(),
  requestPostMock: vi.fn(),
  cleanupDataMock: vi.fn(),
  getCleanupStatsMock: vi.fn(),
  cleanupAllDataMock: vi.fn(),
  successMock: vi.fn(),
  errorMock: vi.fn(),
  confirmMock: vi.fn(),
}))

vi.mock('@/utils/request', () => ({
  default: {
    get: requestGetMock,
    post: requestPostMock,
  },
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
        'el-switch': true,
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
    cleanupDataMock.mockReset()
    getCleanupStatsMock.mockReset()
    cleanupAllDataMock.mockReset()
    successMock.mockReset()
    errorMock.mockReset()
    confirmMock.mockReset()
    localStorage.clear()
  })

  it('loads devices, system status, metrics and can load cleanup stats', async () => {
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
      systemStatus: { status?: string } | null
      metricsText: string
      ingestionRecords: Array<{ id: number }>
      loadCleanupStats: () => Promise<void>
      cleanupStats: { energy_data?: { total?: number } } | null
    }
    await vm.loadCleanupStats()

    expect(requestGetMock).toHaveBeenCalledWith('/health')
    expect(requestGetMock).toHaveBeenCalledWith('/metrics', expect.objectContaining({
      responseType: 'text',
    }))
    expect(getCleanupStatsMock.mock.calls.length).toBeGreaterThanOrEqual(1)
    expect(vm.systemStatus?.status).toBe('healthy')
    expect(vm.metricsText).toContain('mine_http_requests_total')
    expect(vm.ingestionRecords[0].id).toBe(9)
    expect(vm.cleanupStats?.energy_data?.total).toBe(100)
  })

  it('cleans historical data and refreshes cleanup stats', async () => {
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
      statistics: 0,
      mqtt_ingestion: 5,
      audit_event: 3,
      svg_telemetry: 1,
      capacitor_bank_telemetry: 2,
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
      message: expect.stringContaining('清理完成！共删除 18 条记录'),
    }))
    expect(vm.cleanupStats?.energy_data?.total).toBe(20)
  })

  it('cleans all data only after double confirmation', async () => {
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
      statistics: 0,
      mqtt_ingestion: 0,
      audit_event: 0,
      svg_telemetry: 0,
      capacitor_bank_telemetry: 0,
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
      message: expect.stringContaining('清除完成！共删除 99 条记录'),
    }))
  })

  it('renders cleanup stats with mqtt, audit and compensation telemetry categories', async () => {
    requestGetMock.mockResolvedValue({})
    getCleanupStatsMock.mockResolvedValue({
      energy_data: { total: 20 },
      mqtt_ingestion: { total: 8 },
      audit_event: { total: 6 },
      svg_telemetry: { total: 4 },
      capacitor_bank_telemetry: { total: 2 },
      carbon_emission: { total: 1 },
      alarm_data: { total: 0 },
    })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      loadCleanupStats: () => Promise<void>
      cleanupStats: {
        mqtt_ingestion?: { total?: number }
        audit_event?: { total?: number }
        svg_telemetry?: { total?: number }
        capacitor_bank_telemetry?: { total?: number }
      } | null
    }
    await vm.loadCleanupStats()

    expect(vm.cleanupStats?.mqtt_ingestion?.total).toBe(8)
    expect(vm.cleanupStats?.audit_event?.total).toBe(6)
    expect(vm.cleanupStats?.svg_telemetry?.total).toBe(4)
    expect(vm.cleanupStats?.capacitor_bank_telemetry?.total).toBe(2)
  })

  it('toggles global demo data mode from system settings', async () => {
    requestGetMock.mockImplementation(async (url: string) => {
      if (url === '/metrics') return ''
      if (url === '/devices/ingestion-records') return { items: [] }
      return {}
    })
    getCleanupStatsMock.mockResolvedValue({})
    localStorage.setItem('campus-ems-demo-suppressed', '1')

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      demoModeEnabled: boolean
      demoModeStatusText: string
      handleDemoModeChange: (enabled: boolean) => void
    }

    expect(vm.demoModeEnabled).toBe(false)
    expect(vm.demoModeStatusText).toBe('已关闭，不使用演示数据')

    vm.handleDemoModeChange(true)
    expect(localStorage.getItem('campus-ems-demo-suppressed')).toBeNull()
    expect(successMock).toHaveBeenCalledWith(expect.stringContaining('已开启演示数据模式'))
    expect(vm.demoModeStatusText).toBe('已开启，使用演示数据')

    vm.handleDemoModeChange(false)
    expect(localStorage.getItem('campus-ems-demo-suppressed')).toBe('1')
    expect(successMock).toHaveBeenCalledWith(expect.stringContaining('已关闭演示数据模式'))
  })
})
