import { beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Report from '../Report.vue'
import { useAuthStore } from '@/stores/useAuthStore'

const {
  getDevicesMock,
  downloadReportMock,
  getDeviceHistoryFieldsMock,
  buildReportDownloadNameMock,
  successMock,
  warningMock,
  errorMock,
} = vi.hoisted(() => ({
  getDevicesMock: vi.fn(),
  downloadReportMock: vi.fn(),
  getDeviceHistoryFieldsMock: vi.fn(),
  buildReportDownloadNameMock: vi.fn(() => 'report.csv'),
  successMock: vi.fn(),
  warningMock: vi.fn(),
  errorMock: vi.fn(),
}))

vi.mock('@/api/device', () => ({
  getDevices: getDevicesMock,
}))

vi.mock('@/api/report', () => ({
  downloadReport: downloadReportMock,
  getDeviceHistoryFields: getDeviceHistoryFieldsMock,
  buildReportDownloadName: buildReportDownloadNameMock,
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
  }
})

function mountReport() {
  return shallowMount(Report, {
    global: {
      stubs: {
        'el-alert': {
          props: ['title', 'type'],
          template: '<div class="el-alert-stub" :data-title="title" :data-type="type" />',
        },
        'el-button': {
          emits: ['click'],
          template: '<button class="el-button-stub" @click="$emit(\'click\')"><slot /></button>',
        },
        'el-form': true,
        'el-form-item': true,
        'el-radio-group': true,
        'el-radio-button': true,
        'el-select': true,
        'el-option': true,
        'el-date-picker': true,
        'el-input-number': true,
        'el-checkbox-group': true,
        'el-checkbox': true,
        'el-icon': true,
      },
    },
  })
}

describe('Report view', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    getDevicesMock.mockReset()
    downloadReportMock.mockReset()
    getDeviceHistoryFieldsMock.mockReset()
    buildReportDownloadNameMock.mockClear()
    buildReportDownloadNameMock.mockReturnValue('report.csv')
    successMock.mockReset()
    warningMock.mockReset()
    errorMock.mockReset()
  })

  it('loads devices on mount and shows scoped export hint', async () => {
    const authStore = useAuthStore()
    authStore.locationScope = '1,2'
    getDevicesMock.mockResolvedValue([
      { id: 1, name: '一号设备', sn: 'SN-001', device_type: 'meter', is_active: true },
    ])

    const wrapper = mountReport()
    await Promise.resolve()

    expect(getDevicesMock).toHaveBeenCalledTimes(1)
    const alert = wrapper.find('.el-alert-stub')
    expect(alert.attributes('data-type')).toBe('warning')
    expect(alert.attributes('data-title')).toContain('当前账号位置范围为 1,2')
  })

  it('normalizes reversed date range before exporting csv', async () => {
    getDevicesMock.mockResolvedValue([])
    downloadReportMock.mockResolvedValue(new Blob(['csv-content'], { type: 'text/csv' }))
    const createObjectURLMock = vi.fn(() => 'blob:report')
    const revokeObjectURLMock = vi.fn()
    vi.spyOn(window.URL, 'createObjectURL').mockImplementation(createObjectURLMock)
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(revokeObjectURLMock)

    const wrapper = mountReport()
    await Promise.resolve()
    ;(wrapper.vm as unknown as {
      filters: {
        start_time?: string
        end_time?: string
      }
      handleDownload: () => Promise<void>
    }).filters.start_time = '2026-03-26T18:00:00'
    ;(wrapper.vm as unknown as {
      filters: {
        start_time?: string
        end_time?: string
      }
    }).filters.end_time = '2026-03-26T08:00:00'

    await (wrapper.vm as unknown as { handleDownload: () => Promise<void> }).handleDownload()

    expect(downloadReportMock).toHaveBeenCalledTimes(1)
    expect(downloadReportMock).toHaveBeenCalledWith(expect.objectContaining({
      start_time: '2026-03-26T08:00:00',
      end_time: '2026-03-26T18:00:00',
    }))
    expect(createObjectURLMock).toHaveBeenCalledTimes(1)
  })

  it('shows warning when device loading fails', async () => {
    getDevicesMock.mockRejectedValue(new Error('network'))

    mountReport()
    await Promise.resolve()
    await Promise.resolve()

    expect(warningMock).toHaveBeenCalledWith('设备列表加载失败，仍可导出全量权限范围数据')
  })

  it('requires a selected device before exporting device history', async () => {
    getDevicesMock.mockResolvedValue([])
    const wrapper = mountReport()
    await Promise.resolve()
    ;(wrapper.vm as unknown as {
      filters: {
        report_type: string
      }
      handleDownload: () => Promise<void>
    }).filters.report_type = 'device_history'

    await (wrapper.vm as unknown as { handleDownload: () => Promise<void> }).handleDownload()

    expect(downloadReportMock).not.toHaveBeenCalled()
    expect(warningMock).toHaveBeenCalledWith('请选择要导出的设备')
  })

  it('exports device history with the selected device id', async () => {
    getDevicesMock.mockResolvedValue([
      { id: 8, name: '无功补偿控制器', sn: 'CAP-001', device_type: 'compensation', is_active: true },
    ])
    downloadReportMock.mockResolvedValue(new Blob(['csv-content'], { type: 'text/csv' }))
    vi.spyOn(window.URL, 'createObjectURL').mockImplementation(() => 'blob:report')
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(vi.fn())

    const wrapper = mountReport()
    await Promise.resolve()
    ;(wrapper.vm as unknown as {
      filters: {
        report_type: string
        device_id?: number
      }
      handleDownload: () => Promise<void>
    }).filters.report_type = 'device_history'
    ;(wrapper.vm as unknown as {
      filters: {
        device_id?: number
      }
    }).filters.device_id = 8
    ;(wrapper.vm as unknown as { selectedFieldKeys: string[] }).selectedFieldKeys = ['device_name']

    await (wrapper.vm as unknown as { handleDownload: () => Promise<void> }).handleDownload()

    expect(downloadReportMock).toHaveBeenCalledWith(expect.objectContaining({
      report_type: 'device_history',
      device_id: 8,
    }))
    expect(buildReportDownloadNameMock).toHaveBeenCalledWith(expect.objectContaining({
      report_type: 'device_history',
      device_id: 8,
    }))
  })

  it('loads device history field config and selects default fields', async () => {
    getDevicesMock.mockResolvedValue([
      { id: 8, name: '无功补偿控制器', sn: 'CAP-001', device_type: 'compensation', is_active: true },
    ])
    getDeviceHistoryFieldsMock.mockResolvedValue({
      device_id: 8,
      template: 'capacitor_bank_controller',
      required_fields: ['timestamp'],
      default_fields: ['device_name', 'reactive_power_a'],
      groups: [
        {
          key: 'compensation_effect',
          label: '补偿效果',
          fields: [
            { key: 'reactive_power_a', label: 'A相无功(kvar)', default: true },
            { key: 'power_factor_a', label: 'A相功率因数', default: false },
          ],
        },
      ],
    })

    const wrapper = mountReport()
    await Promise.resolve()
    ;(wrapper.vm as unknown as {
      filters: {
        report_type: string
        device_id?: number
      }
      loadDeviceHistoryFields: () => Promise<void>
    }).filters.report_type = 'device_history'
    ;(wrapper.vm as unknown as {
      filters: {
        device_id?: number
      }
    }).filters.device_id = 8

    await (wrapper.vm as unknown as { loadDeviceHistoryFields: () => Promise<void> }).loadDeviceHistoryFields()

    expect(getDeviceHistoryFieldsMock).toHaveBeenCalledWith(8)
    expect((wrapper.vm as unknown as { selectedFieldKeys: string[] }).selectedFieldKeys).toEqual(['device_name', 'reactive_power_a'])
    expect((wrapper.vm as unknown as { deviceHistoryFieldConfig: { template: string } | null }).deviceHistoryFieldConfig?.template).toBe('capacitor_bank_controller')
  })

  it('passes selected fields when exporting device history', async () => {
    getDevicesMock.mockResolvedValue([])
    downloadReportMock.mockResolvedValue(new Blob(['csv-content'], { type: 'text/csv' }))
    vi.spyOn(window.URL, 'createObjectURL').mockImplementation(() => 'blob:report')
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(vi.fn())

    const wrapper = mountReport()
    await Promise.resolve()
    ;(wrapper.vm as unknown as {
      filters: {
        report_type: string
        device_id?: number
      }
      selectedFieldKeys: string[]
      handleDownload: () => Promise<void>
    }).filters.report_type = 'device_history'
    ;(wrapper.vm as unknown as {
      filters: {
        device_id?: number
      }
    }).filters.device_id = 8
    ;(wrapper.vm as unknown as { selectedFieldKeys: string[] }).selectedFieldKeys = ['device_name', 'reactive_power_a']

    await (wrapper.vm as unknown as { handleDownload: () => Promise<void> }).handleDownload()

    expect(downloadReportMock).toHaveBeenCalledWith(expect.objectContaining({
      report_type: 'device_history',
      device_id: 8,
      fields: 'device_name,reactive_power_a',
    }))
  })

  it('blocks device history export when no fields are selected', async () => {
    getDevicesMock.mockResolvedValue([])
    const wrapper = mountReport()
    await Promise.resolve()
    ;(wrapper.vm as unknown as {
      filters: {
        report_type: string
        device_id?: number
      }
      selectedFieldKeys: string[]
      handleDownload: () => Promise<void>
    }).filters.report_type = 'device_history'
    ;(wrapper.vm as unknown as {
      filters: {
        device_id?: number
      }
    }).filters.device_id = 8
    ;(wrapper.vm as unknown as { selectedFieldKeys: string[] }).selectedFieldKeys = []

    await (wrapper.vm as unknown as { handleDownload: () => Promise<void> }).handleDownload()

    expect(downloadReportMock).not.toHaveBeenCalled()
    expect(warningMock).toHaveBeenCalledWith('请至少选择一个导出字段')
  })
})
