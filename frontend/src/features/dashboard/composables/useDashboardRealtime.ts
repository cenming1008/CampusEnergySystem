import { computed, reactive, watch, type Ref } from 'vue'
import { getAnalysis, getHistory } from '@/api/telemetry'
import type { Device } from '@/api/device'

interface TelemetryMessage {
  type?: string
  data?: {
    device_id?: number
    power?: number
    current?: number
    voltage?: number
    timestamp?: string
  }
}

export function useDashboardRealtime(options: {
  currentDeviceId: Ref<number | undefined>
  deviceList: Ref<Device[]>
  latestMessage: Ref<TelemetryMessage | null>
}) {
  const { currentDeviceId, deviceList, latestMessage } = options

  const realTimeData = reactive({
    power: 0,
    energy: 0,
    current: 0,
    voltage: 0
  })

  const energyTrendData = reactive<{ times: string[]; values: number[] }>({
    times: [],
    values: []
  })

  const isStorageDevice = computed(() => {
    const device = deviceList.value.find((item) => item.id === currentDeviceId.value)
    return device?.device_type === 'storage'
  })

  const storageStatus = computed(() => {
    if (!isStorageDevice.value) return ''
    return realTimeData.power < 0 ? '充电中' : '放电中'
  })

  const displayPower = computed(() => Math.abs(realTimeData.power))
  const displayCurrent = computed(() => Math.abs(realTimeData.current))
  const displayEnergy = computed(() => Math.abs(realTimeData.energy))

  const updateRealtimeMetrics = (data: Partial<typeof realTimeData>) => {
    realTimeData.power = data.power ?? realTimeData.power
    realTimeData.energy = data.energy ?? realTimeData.energy
    realTimeData.current = data.current ?? realTimeData.current
    realTimeData.voltage = data.voltage ?? realTimeData.voltage
  }

  const loadDeviceData = async () => {
    if (!currentDeviceId.value) return

    try {
      const analysis = await getAnalysis(currentDeviceId.value)
      updateRealtimeMetrics({
        power: analysis.current_power || 0,
        energy: analysis.today_energy || 0,
        current: analysis.current || 0,
        voltage: analysis.voltage || 0
      })

      await loadEnergyTrend()
    } catch (error) {
      console.error('加载设备数据失败:', error)
    }
  }

  const loadEnergyTrend = async () => {
    if (!currentDeviceId.value) return

    try {
      const history = await getHistory(currentDeviceId.value, 100)

      if (history && history.length > 0) {
        const sortedHistory = [...history].reverse()
        energyTrendData.times = sortedHistory.map((item: any) => item.timestamp?.substring(11, 19) || '')
        energyTrendData.values = sortedHistory.map((item: any) => Math.abs(item.flow_rate || 0))
      } else {
        energyTrendData.times = []
        energyTrendData.values = []
      }
    } catch (error) {
      console.error('加载负荷曲线失败:', error)
    }
  }

  watch(latestMessage, (message) => {
    if (message?.type !== 'telemetry_update' || !message.data) return

    if (message.data.device_id !== currentDeviceId.value) return

    updateRealtimeMetrics({
      power: message.data.power || 0,
      current: message.data.current || 0,
      voltage: message.data.voltage || 0
    })

    const time = message.data.timestamp?.substring(11, 19) || new Date().toTimeString().substring(0, 8)
    const power = Math.abs(message.data.power || 0)

    energyTrendData.times.push(time)
    energyTrendData.values.push(power)

    if (energyTrendData.times.length > 100) {
      energyTrendData.times.shift()
      energyTrendData.values.shift()
    }
  })

  return {
    displayCurrent,
    displayEnergy,
    displayPower,
    energyTrendData,
    isStorageDevice,
    realTimeData,
    storageStatus,
    loadDeviceData,
    loadEnergyTrend,
    updateRealtimeMetrics
  }
}
