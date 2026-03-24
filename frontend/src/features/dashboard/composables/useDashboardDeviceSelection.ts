import { computed, ref } from 'vue'
import { getDevices, type Device } from '@/api/device'

export function useDashboardDeviceSelection() {
  const currentDeviceId = ref<number | undefined>(undefined)
  const deviceList = ref<Device[]>([])

  const currentDevice = computed(() =>
    deviceList.value.find((device) => device.id === currentDeviceId.value)
  )

  const totalDevices = computed(() => deviceList.value.length)
  const onlineDevices = computed(() => deviceList.value.filter((device) => device.is_active).length)

  const loadDeviceList = async () => {
    try {
      const devices = await getDevices()
      deviceList.value = devices

      if (!currentDeviceId.value && devices.length > 0) {
        const loadDevice = devices.find((device) => device.device_type === 'load')
        currentDeviceId.value = loadDevice?.id || devices[0].id
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
    totalDevices,
    onlineDevices,
    loadDeviceList
  }
}
