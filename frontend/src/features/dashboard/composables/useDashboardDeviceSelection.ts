import { computed, ref } from 'vue'
import { getDevices, type Device } from '@/api/device'

export function useDashboardDeviceSelection() {
  const currentDeviceId = ref<number | undefined>(undefined)
  const deviceList = ref<Device[]>([])
  const selectableDevices = computed(() =>
    deviceList.value.filter((device): device is Device & { id: number } => typeof device.id === 'number')
  )

  const currentDevice = computed(() =>
    deviceList.value.find((device) => device.id === currentDeviceId.value)
  )

  const totalDevices = computed(() => deviceList.value.length)
  const onlineDevices = computed(() => deviceList.value.filter((device) => device.is_active).length)

  const loadDeviceList = async () => {
    try {
      const devices = await getDevices()
      deviceList.value = devices

      const availableIds = new Set(selectableDevices.value.map((device) => device.id))
      if (currentDeviceId.value && !availableIds.has(currentDeviceId.value)) {
        currentDeviceId.value = undefined
      }

      if (!currentDeviceId.value && selectableDevices.value.length > 0) {
        const loadDevice = selectableDevices.value.find((device) => device.device_type === 'load')
        currentDeviceId.value = loadDevice?.id || selectableDevices.value[0].id
      }

      return devices
    } catch (error) {
      console.error('加载设备失败:', error)
      return []
    }
  }

  return {
    currentDeviceId,
    currentDevice,
    deviceList,
    selectableDevices,
    totalDevices,
    onlineDevices,
    loadDeviceList
  }
}
