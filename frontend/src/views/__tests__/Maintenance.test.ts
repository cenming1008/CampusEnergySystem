import { beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import Maintenance from '../Maintenance.vue'

const {
  getMaintenanceDetailMock,
  getMaintenanceListMock,
  getMaintenanceTypesMock,
  getMaintenanceStatusesMock,
  createMaintenanceMock,
  startMaintenanceMock,
  completeMaintenanceMock,
  cancelMaintenanceMock,
  deleteMaintenanceMock,
  getUpcomingMaintenanceMock,
  getOverdueMaintenanceMock,
  getMaintenanceStatisticsMock,
  getDeviceMaintenanceHistoryMock,
  updateMaintenanceMock,
  getDevicesMock,
  successMock,
  warningMock,
  errorMock,
  confirmMock,
  promptMock,
} = vi.hoisted(() => ({
  getMaintenanceDetailMock: vi.fn(),
  getMaintenanceListMock: vi.fn(),
  getMaintenanceTypesMock: vi.fn(),
  getMaintenanceStatusesMock: vi.fn(),
  createMaintenanceMock: vi.fn(),
  startMaintenanceMock: vi.fn(),
  completeMaintenanceMock: vi.fn(),
  cancelMaintenanceMock: vi.fn(),
  deleteMaintenanceMock: vi.fn(),
  getUpcomingMaintenanceMock: vi.fn(),
  getOverdueMaintenanceMock: vi.fn(),
  getMaintenanceStatisticsMock: vi.fn(),
  getDeviceMaintenanceHistoryMock: vi.fn(),
  updateMaintenanceMock: vi.fn(),
  getDevicesMock: vi.fn(),
  successMock: vi.fn(),
  warningMock: vi.fn(),
  errorMock: vi.fn(),
  confirmMock: vi.fn(),
  promptMock: vi.fn(),
}))

vi.mock('@/api/maintenance', () => ({
  getMaintenanceDetail: getMaintenanceDetailMock,
  getMaintenanceList: getMaintenanceListMock,
  getMaintenanceTypes: getMaintenanceTypesMock,
  getMaintenanceStatuses: getMaintenanceStatusesMock,
  createMaintenance: createMaintenanceMock,
  startMaintenance: startMaintenanceMock,
  completeMaintenance: completeMaintenanceMock,
  cancelMaintenance: cancelMaintenanceMock,
  deleteMaintenance: deleteMaintenanceMock,
  getUpcomingMaintenance: getUpcomingMaintenanceMock,
  getOverdueMaintenance: getOverdueMaintenanceMock,
  getMaintenanceStatistics: getMaintenanceStatisticsMock,
  getDeviceMaintenanceHistory: getDeviceMaintenanceHistoryMock,
  updateMaintenance: updateMaintenanceMock,
}))

vi.mock('@/api/device', () => ({
  getDevices: getDevicesMock,
}))

vi.mock('@/shared/composables/usePermissions', () => ({
  usePermissions: () => ({
    canManageMaintenance: true,
    canOperateMaintenance: true,
    hasScopedAccess: false,
  }),
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
      prompt: promptMock,
    },
  }
})

function mountView() {
  return shallowMount(Maintenance, {
    global: {
      stubs: {
        'el-button': true,
        'el-tag': true,
        'el-select': true,
        'el-option': true,
        'el-tabs': true,
        'el-tab-pane': true,
        'el-table': true,
        'el-table-column': true,
        'el-dialog': true,
        'el-form': true,
        'el-form-item': true,
        'el-input': true,
        'el-input-number': true,
        'el-alert': true,
        'el-date-picker': true,
        'el-icon': true,
        Calendar: true,
        Loading: true,
        CircleCheck: true,
        Warning: true,
        Plus: true,
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

describe('Maintenance view', () => {
  beforeEach(() => {
    getMaintenanceDetailMock.mockReset()
    getMaintenanceListMock.mockReset()
    getMaintenanceTypesMock.mockReset()
    getMaintenanceStatusesMock.mockReset()
    createMaintenanceMock.mockReset()
    startMaintenanceMock.mockReset()
    completeMaintenanceMock.mockReset()
    cancelMaintenanceMock.mockReset()
    deleteMaintenanceMock.mockReset()
    getUpcomingMaintenanceMock.mockReset()
    getOverdueMaintenanceMock.mockReset()
    getMaintenanceStatisticsMock.mockReset()
    getDeviceMaintenanceHistoryMock.mockReset()
    updateMaintenanceMock.mockReset()
    getDevicesMock.mockReset()
    successMock.mockReset()
    warningMock.mockReset()
    errorMock.mockReset()
    confirmMock.mockReset()
    promptMock.mockReset()
  })

  it('loads base data and maintenance lists', async () => {
    getDevicesMock.mockResolvedValue([{ id: 1, name: '一号设备', sn: 'SN-1', device_type: 'load', is_active: true }])
    getMaintenanceTypesMock.mockResolvedValue({ data: [{ value: 'routine', label: '例行维护', description: '' }] })
    getMaintenanceStatusesMock.mockResolvedValue({ data: [{ value: 'scheduled', label: '计划中', description: '' }] })
    getMaintenanceListMock.mockResolvedValue([{ id: 11, device_id: 1, maintenance_type: 'routine', status: 'scheduled', scheduled_time: '2026-03-26T10:00:00', title: '月检', created_at: '2026-03-26T08:00:00' }])
    getUpcomingMaintenanceMock.mockResolvedValue([{ id: 12, device_id: 1, maintenance_type: 'routine', status: 'scheduled', scheduled_time: '2026-03-27T10:00:00', title: '周检', created_at: '2026-03-26T08:00:00' }])
    getOverdueMaintenanceMock.mockResolvedValue([])
    getMaintenanceStatisticsMock.mockResolvedValue({ data: { completed_count: 3, by_status: { scheduled: 1 }, by_type: {}, total_count: 4, total_cost: 0, avg_duration_hours: 0, overdue_count: 0 } })

    const wrapper = mountView()
    await flushAsync()

    const vm = wrapper.vm as unknown as {
      deviceList: Array<{ name: string }>
      typeList: Array<{ value: string }>
      statusList: Array<{ value: string }>
      maintenanceList: Array<{ id: number }>
      upcomingList: Array<{ id: number }>
      statistics: { completed_count?: number } | null
      loadBaseData: () => Promise<void>
      loadData: () => Promise<void>
    }
    await vm.loadBaseData()
    await vm.loadData()

    expect(getDevicesMock.mock.calls.length).toBeGreaterThanOrEqual(1)
    expect(getMaintenanceListMock.mock.calls.length).toBeGreaterThanOrEqual(1)
    expect(vm.deviceList[0].name).toBe('一号设备')
    expect(vm.typeList[0].value).toBe('routine')
    expect(vm.statusList[0].value).toBe('scheduled')
    expect(vm.maintenanceList[0].id).toBe(11)
    expect(vm.upcomingList[0].id).toBe(12)
    expect(vm.statistics?.completed_count).toBe(3)
  })

  it('warns when required fields are missing for create', async () => {
    getDevicesMock.mockResolvedValue([])
    getMaintenanceTypesMock.mockResolvedValue({ data: [] })
    getMaintenanceStatusesMock.mockResolvedValue({ data: [] })
    getMaintenanceListMock.mockResolvedValue([])
    getUpcomingMaintenanceMock.mockResolvedValue([])
    getOverdueMaintenanceMock.mockResolvedValue([])
    getMaintenanceStatisticsMock.mockResolvedValue({ data: null })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      dialogType: 'create' | 'edit' | 'complete'
      formData: { device_id: number; title: string; scheduled_time: string }
      handleSubmit: () => Promise<void>
    }
    vm.dialogType = 'create'
    vm.formData.device_id = 0
    vm.formData.title = ''
    vm.formData.scheduled_time = ''

    await vm.handleSubmit()

    expect(warningMock).toHaveBeenCalledWith('请填写必要信息')
    expect(createMaintenanceMock).not.toHaveBeenCalled()
  })

  it('creates a maintenance plan and reloads data', async () => {
    getDevicesMock.mockResolvedValue([{ id: 2, name: '二号设备', sn: 'SN-2', device_type: 'load', is_active: true }])
    getMaintenanceTypesMock.mockResolvedValue({ data: [] })
    getMaintenanceStatusesMock.mockResolvedValue({ data: [] })
    getMaintenanceListMock.mockResolvedValue([])
    getUpcomingMaintenanceMock.mockResolvedValue([])
    getOverdueMaintenanceMock.mockResolvedValue([])
    getMaintenanceStatisticsMock.mockResolvedValue({ data: null })
    createMaintenanceMock.mockResolvedValue({ id: 20 })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      dialogType: 'create' | 'edit' | 'complete'
      dialogVisible: boolean
      formData: {
        device_id: number
        maintenance_type: string
        scheduled_time: string
        title: string
        description?: string
        operator?: string
      }
      handleSubmit: () => Promise<void>
    }
    vm.dialogType = 'create'
    vm.dialogVisible = true
    vm.formData.device_id = 2
    vm.formData.maintenance_type = 'routine'
    vm.formData.scheduled_time = '2026-03-30T10:00:00'
    vm.formData.title = '季度保养'
    vm.formData.description = '更换润滑油'
    vm.formData.operator = '张三'

    await vm.handleSubmit()

    expect(createMaintenanceMock).toHaveBeenCalledWith(expect.objectContaining({
      device_id: 2,
      title: '季度保养',
      operator: '张三',
    }))
    expect(successMock).toHaveBeenCalledWith('维护计划创建成功')
    expect(vm.dialogVisible).toBe(false)
  })

  it('loads detail into edit dialog and updates maintenance', async () => {
    getDevicesMock.mockResolvedValue([])
    getMaintenanceTypesMock.mockResolvedValue({ data: [] })
    getMaintenanceStatusesMock.mockResolvedValue({ data: [] })
    getMaintenanceListMock.mockResolvedValue([])
    getUpcomingMaintenanceMock.mockResolvedValue([])
    getOverdueMaintenanceMock.mockResolvedValue([])
    getMaintenanceStatisticsMock.mockResolvedValue({ data: null })
    getMaintenanceDetailMock.mockResolvedValue({
      id: 7,
      device_id: 1,
      maintenance_type: 'repair',
      status: 'scheduled',
      scheduled_time: '2026-04-01T09:00:00',
      title: '更换轴承',
      description: '轴承磨损',
      operator: '李四',
      created_at: '2026-03-26T08:00:00',
    })
    updateMaintenanceMock.mockResolvedValue({ id: 7 })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      dialogVisible: boolean
      editFormData: { id: number; title?: string; scheduled_time?: string; description?: string; operator?: string }
      openEditDialog: (record: { id: number }) => Promise<void>
      handleSubmit: () => Promise<void>
    }

    await vm.openEditDialog({ id: 7 })
    expect(vm.dialogVisible).toBe(true)
    expect(vm.editFormData.id).toBe(7)
    expect(vm.editFormData.title).toBe('更换轴承')

    await vm.handleSubmit()

    expect(updateMaintenanceMock).toHaveBeenCalledWith(7, expect.objectContaining({
      title: '更换轴承',
      operator: '李四',
    }))
    expect(successMock).toHaveBeenCalledWith('维护计划已更新')
  })

  it('completes maintenance with completion form data', async () => {
    getDevicesMock.mockResolvedValue([])
    getMaintenanceTypesMock.mockResolvedValue({ data: [] })
    getMaintenanceStatusesMock.mockResolvedValue({ data: [] })
    getMaintenanceListMock.mockResolvedValue([])
    getUpcomingMaintenanceMock.mockResolvedValue([])
    getOverdueMaintenanceMock.mockResolvedValue([])
    getMaintenanceStatisticsMock.mockResolvedValue({ data: null })
    completeMaintenanceMock.mockResolvedValue({ id: 9 })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      dialogType: 'create' | 'edit' | 'complete'
      dialogVisible: boolean
      completeFormData: { id: number; result?: string; cost?: number; parts_replaced?: string; next_maintenance_date?: string }
      handleSubmit: () => Promise<void>
    }
    vm.dialogType = 'complete'
    vm.dialogVisible = true
    vm.completeFormData.id = 9
    vm.completeFormData.result = '运行恢复正常'
    vm.completeFormData.cost = 500
    vm.completeFormData.parts_replaced = '轴承'
    vm.completeFormData.next_maintenance_date = '2026-06-01'

    await vm.handleSubmit()

    expect(completeMaintenanceMock).toHaveBeenCalledWith(9, {
      result: '运行恢复正常',
      cost: 500,
      parts_replaced: '轴承',
      next_maintenance_date: '2026-06-01',
    })
    expect(successMock).toHaveBeenCalledWith('维护已完成')
    expect(vm.dialogVisible).toBe(false)
  })

  it('starts maintenance and reloads data', async () => {
    getDevicesMock.mockResolvedValue([])
    getMaintenanceTypesMock.mockResolvedValue({ data: [] })
    getMaintenanceStatusesMock.mockResolvedValue({ data: [] })
    getMaintenanceListMock.mockResolvedValue([])
    getUpcomingMaintenanceMock.mockResolvedValue([])
    getOverdueMaintenanceMock.mockResolvedValue([])
    getMaintenanceStatisticsMock.mockResolvedValue({ data: null })
    startMaintenanceMock.mockResolvedValue({ id: 13 })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      handleStart: (record: { id: number }) => Promise<void>
    }

    await vm.handleStart({ id: 13 })

    expect(startMaintenanceMock).toHaveBeenCalledWith(13)
    expect(successMock).toHaveBeenCalledWith('维护已开始')
  })

  it('cancels maintenance after prompt confirmation', async () => {
    getDevicesMock.mockResolvedValue([])
    getMaintenanceTypesMock.mockResolvedValue({ data: [] })
    getMaintenanceStatusesMock.mockResolvedValue({ data: [] })
    getMaintenanceListMock.mockResolvedValue([])
    getUpcomingMaintenanceMock.mockResolvedValue([])
    getOverdueMaintenanceMock.mockResolvedValue([])
    getMaintenanceStatisticsMock.mockResolvedValue({ data: null })
    promptMock.mockResolvedValue({ value: '用户取消' })
    cancelMaintenanceMock.mockResolvedValue({ id: 14 })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      handleCancel: (record: { id: number }) => Promise<void>
    }

    await vm.handleCancel({ id: 14 })

    expect(promptMock).toHaveBeenCalledTimes(1)
    expect(cancelMaintenanceMock).toHaveBeenCalledWith(14, '用户取消')
    expect(successMock).toHaveBeenCalledWith('维护已取消')
  })

  it('deletes maintenance after confirmation', async () => {
    getDevicesMock.mockResolvedValue([])
    getMaintenanceTypesMock.mockResolvedValue({ data: [] })
    getMaintenanceStatusesMock.mockResolvedValue({ data: [] })
    getMaintenanceListMock.mockResolvedValue([])
    getUpcomingMaintenanceMock.mockResolvedValue([])
    getOverdueMaintenanceMock.mockResolvedValue([])
    getMaintenanceStatisticsMock.mockResolvedValue({ data: null })
    confirmMock.mockResolvedValue(undefined)
    deleteMaintenanceMock.mockResolvedValue({ success: true })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      handleDelete: (record: { id: number }) => Promise<void>
    }

    await vm.handleDelete({ id: 15 })

    expect(confirmMock).toHaveBeenCalledTimes(1)
    expect(deleteMaintenanceMock).toHaveBeenCalledWith(15)
    expect(successMock).toHaveBeenCalledWith('删除成功')
  })
})
