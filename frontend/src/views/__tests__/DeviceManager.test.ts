import { beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import DeviceManager from '../DeviceManager.vue'

const {
  getDevicesMock,
  createDeviceMock,
  updateDeviceMock,
  deleteDeviceMock,
  toggleDeviceStatusMock,
  getDeviceTypesMock,
  getCompensationSvgOperationsProfileMock,
  notifyDevicesUpdatedMock,
  successMock,
  errorMock,
  warningMock,
  confirmMock,
  routerPushMock,
} = vi.hoisted(() => ({
  getDevicesMock: vi.fn(),
  createDeviceMock: vi.fn(),
  updateDeviceMock: vi.fn(),
  deleteDeviceMock: vi.fn(),
  toggleDeviceStatusMock: vi.fn(),
  getDeviceTypesMock: vi.fn(),
  getCompensationSvgOperationsProfileMock: vi.fn(),
  notifyDevicesUpdatedMock: vi.fn(),
  successMock: vi.fn(),
  errorMock: vi.fn(),
  warningMock: vi.fn(),
  confirmMock: vi.fn(),
  routerPushMock: vi.fn(),
}))

vi.mock('@/api/device', () => ({
  getDevices: getDevicesMock,
  createDevice: createDeviceMock,
  updateDevice: updateDeviceMock,
  deleteDevice: deleteDeviceMock,
  toggleDeviceStatus: toggleDeviceStatusMock,
  getDeviceTypes: getDeviceTypesMock,
  FALLBACK_DEVICE_TYPE_CONFIGS: [
    {
      device_type: 'load',
      category: 'load',
      energy_type: 'electricity',
      name_zh: '用电设备',
      name_en: 'Load',
      unit: 'kW',
      default_capacity: 100,
      required_fields: [],
      optional_fields: [],
      icon: '⚡',
      color: '#FF9800',
    },
    {
      device_type: 'water_meter',
      category: 'water_meter',
      energy_type: 'water',
      name_zh: '水表',
      name_en: 'Water Meter',
      unit: 'm³/h',
      default_capacity: 50,
      required_fields: [],
      optional_fields: [],
      icon: '💧',
      color: '#2196F3',
    },
  ],
  notifyDevicesUpdated: notifyDevicesUpdatedMock,
}))

vi.mock('@/api/compensation', () => ({
  getCompensationSvgOperationsProfile: getCompensationSvgOperationsProfileMock,
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: routerPushMock,
  }),
}))

vi.mock('@/shared/composables/usePermissions', () => ({
  usePermissions: () => ({
    canManageDevices: true,
    canControlDevices: true,
    hasScopedAccess: false,
  }),
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual<typeof import('element-plus')>('element-plus')
  const ElMessage = Object.assign(
    vi.fn((payload?: unknown) => payload),
    {
      success: successMock,
      error: errorMock,
      warning: warningMock,
    }
  )

  return {
    ...actual,
    ElMessage,
    ElMessageBox: {
      confirm: confirmMock,
    },
  }
})

function mountView() {
  return shallowMount(DeviceManager, {
    global: {
      stubs: {
        'el-button': true,
        'el-dialog': true,
        'el-form': true,
        'el-form-item': true,
        'el-input': true,
        'el-select': true,
        'el-option': true,
        'el-switch': true,
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
}

describe('DeviceManager view', () => {
  beforeEach(() => {
    getDevicesMock.mockReset()
    createDeviceMock.mockReset()
    updateDeviceMock.mockReset()
    deleteDeviceMock.mockReset()
    toggleDeviceStatusMock.mockReset()
    getDeviceTypesMock.mockReset()
    getCompensationSvgOperationsProfileMock.mockReset()
    notifyDevicesUpdatedMock.mockReset()
    successMock.mockReset()
    errorMock.mockReset()
    warningMock.mockReset()
    confirmMock.mockReset()
    routerPushMock.mockReset()
  })

  it('loads device types and devices on mount', async () => {
    getDeviceTypesMock.mockResolvedValue([
      {
        device_type: 'load',
        category: 'load',
        energy_type: 'electricity',
        name_zh: '用电设备',
        name_en: 'Load',
        unit: 'kW',
        default_capacity: 100,
        required_fields: [],
        optional_fields: [],
        icon: '⚡',
        color: '#FF9800',
      },
    ])
    getDevicesMock.mockResolvedValue([
      { id: 2, name: 'B', sn: 'SN-2', device_type: 'load', location: '二区', is_active: true },
      { id: 1, name: 'A', sn: 'SN-1', device_type: 'load', location: '一区', is_active: false },
    ])

    const wrapper = mountView()
    await flushAsync()

    const vm = wrapper.vm as unknown as {
      deviceTypes: Array<{ device_type: string }>
      tableData: Array<{ id?: number; name: string }>
    }
    expect(getDeviceTypesMock).toHaveBeenCalledTimes(1)
    expect(getDevicesMock).toHaveBeenCalledTimes(1)
    expect(vm.deviceTypes[0].device_type).toBe('load')
    expect(vm.tableData.map((item) => item.id)).toEqual([1, 2])
  })

  it('falls back to default device types when type loading fails', async () => {
    getDeviceTypesMock.mockRejectedValue(new Error('unavailable'))
    getDevicesMock.mockResolvedValue([])

    const wrapper = mountView()
    await flushAsync()

    const vm = wrapper.vm as unknown as {
      deviceTypes: Array<{ device_type: string }>
    }
    expect(vm.deviceTypes.map((item) => item.device_type)).toContain('load')
    expect(vm.deviceTypes.map((item) => item.device_type)).toContain('water_meter')
  })

  it('opens create dialog with reset defaults', async () => {
    getDeviceTypesMock.mockResolvedValue([
      {
        device_type: 'solar',
        category: 'solar',
        energy_type: 'electricity',
        name_zh: '光伏发电',
        name_en: 'Solar',
        unit: 'kW',
        default_capacity: 50,
        required_fields: [],
        optional_fields: [],
        icon: '☀️',
        color: '#FFC107',
      },
    ])
    getDevicesMock.mockResolvedValue([])

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      dialogTitle: string
      dialogVisible: boolean
      formData: { name: string; sn: string; device_type: string; is_active: boolean }
      openDialog: (row?: unknown) => void
    }

    vm.openDialog()

    expect(vm.dialogTitle).toBe('新增设备')
    expect(vm.dialogVisible).toBe(true)
    expect(vm.formData.name).toBe('')
    expect(vm.formData.sn).toBe('')
    expect(vm.formData.device_type).toBe('solar')
    expect(vm.formData.is_active).toBe(true)
  })

  it('keeps compensation as one primary type and exposes subtype choices separately', async () => {
    getDeviceTypesMock.mockResolvedValue([
      {
        device_type: 'svg',
        category: 'compensation',
        energy_type: 'electricity',
        name_zh: '无功功率补偿设备',
        subtype_name_zh: 'SVG',
        name_en: 'Static Var Generator',
        unit: 'kVAR',
        default_capacity: 200,
        required_fields: [],
        optional_fields: [],
        icon: '⚡',
        color: '#FF6F00',
      },
      {
        device_type: 'capacitor_bank_controller',
        category: 'compensation',
        energy_type: 'electricity',
        name_zh: '无功功率补偿设备',
        subtype_name_zh: '电容补偿控制器',
        name_en: 'Capacitor Bank Controller',
        unit: 'kVAR',
        default_capacity: 200,
        required_fields: [],
        optional_fields: [],
        icon: '⚙️',
        color: '#D97706',
      },
    ])
    getDevicesMock.mockResolvedValue([])

    const wrapper = mountView()
    await flushAsync()

    const vm = wrapper.vm as unknown as {
      typeOptions: Array<{ key: string }>
      selectedTypeKey: string
      subtypeOptions: Array<{ device_type: string }>
    }

    expect(vm.typeOptions.map((item) => item.key)).toEqual(['compensation'])
    vm.selectedTypeKey = 'compensation'
    await flushAsync()
    expect(vm.subtypeOptions.map((item) => item.device_type)).toEqual(['svg', 'capacitor_bank_controller'])
  })

  it('opens control console for capacitor bank controller devices', async () => {
    getDeviceTypesMock.mockResolvedValue([])
    getDevicesMock.mockResolvedValue([])

    const wrapper = mountView()
    await flushAsync()

    const vm = wrapper.vm as unknown as {
      openDeviceConsole: (row: { id?: number }) => void
    }

    vm.openDeviceConsole({ id: 16 })
    expect(routerPushMock).toHaveBeenCalledWith('/devices/16/console')
  })

  it('creates a device after successful validation', async () => {
    getDeviceTypesMock.mockResolvedValue([])
    getDevicesMock.mockResolvedValue([])
    createDeviceMock.mockResolvedValue({ id: 3 })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      formRef: { validate: (cb: (valid: boolean) => Promise<void> | void) => Promise<void> }
      formData: {
        id?: number
        name: string
        sn: string
        device_type: string
        location: string
        is_active: boolean
        description?: string
      }
      dialogVisible: boolean
      handleSubmit: () => Promise<void>
    }

    vm.formRef = {
      validate: async (cb) => {
        await cb(true)
      },
    }
    vm.dialogVisible = true
    vm.formData.id = undefined
    vm.formData.name = '新设备'
    vm.formData.sn = 'SN-NEW'
    vm.formData.device_type = 'load'
    vm.formData.location = '井下一区'
    vm.formData.is_active = true
    vm.formData.description = 'desc'

    await vm.handleSubmit()

    expect(createDeviceMock).toHaveBeenCalledWith(expect.objectContaining({
      name: '新设备',
      sn: 'SN-NEW',
      device_type: 'load',
      location: '井下一区',
    }))
    expect(successMock).toHaveBeenCalledWith('设备创建成功')
    expect(vm.dialogVisible).toBe(false)
  })

  it('updates an existing device after successful validation', async () => {
    getDeviceTypesMock.mockResolvedValue([])
    getDevicesMock.mockResolvedValue([])
    updateDeviceMock.mockResolvedValue({ id: 9 })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      formRef: { validate: (cb: (valid: boolean) => Promise<void> | void) => Promise<void> }
      formData: {
        id?: number
        name: string
        sn: string
        device_type: string
        location: string
        is_active: boolean
      }
      handleSubmit: () => Promise<void>
    }

    vm.formRef = {
      validate: async (cb) => {
        await cb(true)
      },
    }
    vm.formData.id = 9
    vm.formData.name = '已存在设备'
    vm.formData.sn = 'SN-9'
    vm.formData.device_type = 'load'
    vm.formData.location = '井下二层'
    vm.formData.is_active = false

    await vm.handleSubmit()

    expect(updateDeviceMock).toHaveBeenCalledWith(9, expect.objectContaining({
      id: 9,
      name: '已存在设备',
    }))
    expect(successMock).toHaveBeenCalledWith('设备更新成功')
  })

  it('deletes a device after confirmation', async () => {
    getDeviceTypesMock.mockResolvedValue([])
    getDevicesMock.mockResolvedValue([])
    confirmMock.mockResolvedValue(undefined)
    deleteDeviceMock.mockResolvedValue(undefined)

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      handleDelete: (row: { id?: number; name: string }) => void
    }

    vm.handleDelete({ id: 6, name: '待删设备' })
    await flushAsync()

    expect(confirmMock).toHaveBeenCalledTimes(1)
    expect(deleteDeviceMock).toHaveBeenCalledWith(6)
    expect(successMock).toHaveBeenCalledWith('删除成功')
  })

  it('sends remote toggle command and resolves true on success', async () => {
    getDeviceTypesMock.mockResolvedValue([])
    getDevicesMock.mockResolvedValue([])
    confirmMock.mockResolvedValue(undefined)
    toggleDeviceStatusMock.mockResolvedValue({ id: 3 })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      handleStatusChange: (newVal: boolean, row: { id?: number; name: string; is_active: boolean }) => Promise<boolean>
    }

    await expect(vm.handleStatusChange(true, { id: 3, name: '主提升机', is_active: false })).resolves.toBe(true)
    expect(toggleDeviceStatusMock).toHaveBeenCalledWith(3, true)
  })
})
