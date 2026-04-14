import { beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Report from '../Report.vue'
import { useAuthStore } from '@/stores/useAuthStore'

const {
  getDevicesMock,
  downloadReportMock,
  successMock,
  warningMock,
  errorMock,
} = vi.hoisted(() => ({
  getDevicesMock: vi.fn(),
  downloadReportMock: vi.fn(),
  successMock: vi.fn(),
  warningMock: vi.fn(),
  errorMock: vi.fn(),
}))

vi.mock('@/api/device', () => ({
  getDevices: getDevicesMock,
}))

vi.mock('@/api/report', () => ({
  downloadReport: downloadReportMock,
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
})
