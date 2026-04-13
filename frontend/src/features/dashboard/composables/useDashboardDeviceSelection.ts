import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { DEVICES_UPDATED_EVENT, getDeviceTypes, getDevices, type Device, type DeviceTypeConfig } from '@/api/device'

export function useDashboardDeviceSelection() {
  const currentDeviceId = ref<number | undefined>(undefined)
  const deviceList = ref<Device[]>([])
  const deviceTypes = ref<DeviceTypeConfig[]>([])
  const selectableDevices = computed(() =>
    deviceList.value.filter((device): device is Device & { id: number } => typeof device.id === 'number')
  )

  const currentDevice = computed(() =>
    deviceList.value.find((device) => device.id === currentDeviceId.value)
  )

  const totalDevices = computed(() => deviceList.value.length)
  const onlineDevices = computed(() => deviceList.value.filter((device) => device.is_active).length)

  const loadDeviceList = async (options?: { forceTypes?: boolean }) => {
    try {
      const [devices, types] = await Promise.all([
        getDevices(),
        getDeviceTypes({ force: options?.forceTypes }),
      ])

      deviceList.value = devices
      deviceTypes.value = types

      const availableIds = new Set(selectableDevices.value.map((device) => device.id))
      if (currentDeviceId.value && !availableIds.has(currentDeviceId.value)) {
        currentDeviceId.value = undefined
      }

      if (!currentDeviceId.value && selectableDevices.value.length > 0) {
        const loadDevice = selectableDevices.value.find((device) => device.device_type === 'load')
        currentDeviceId.value = loadDevice?.id || selectableDevices.value[0].id
      }

      return devices
    } catch {
      return []
    }
  }

  const handleDevicesUpdated = () => {
    void loadDeviceList({ forceTypes: true })
  }

  onMounted(() => {
    if (typeof window === 'undefined') return
    window.addEventListener(DEVICES_UPDATED_EVENT, handleDevicesUpdated)
  })

  onBeforeUnmount(() => {
    if (typeof window === 'undefined') return
    window.removeEventListener(DEVICES_UPDATED_EVENT, handleDevicesUpdated)
  })

  return {
    currentDeviceId,
    currentDevice,
    deviceList,
    deviceTypes,
    selectableDevices,
    totalDevices,
    onlineDevices,
    loadDeviceList
  }
}
