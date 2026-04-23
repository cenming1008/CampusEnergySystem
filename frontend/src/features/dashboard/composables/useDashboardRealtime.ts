import { computed, reactive, ref, watch, type Ref } from 'vue'
import { getAnalysis, getHistory, type DeviceAnalysis } from '@/api/telemetry'
import type { Device } from '@/api/device'

const DASHBOARD_TREND_WINDOW_MS = 60 * 60 * 1000

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

interface HistoryPoint {
  timestamp?: string
  flow_rate?: number | null
}

function updateTrendFromHistory(
  energyTrendData: { times: string[]; values: number[]; timestamps: number[] },
  history: HistoryPoint[]
) {
  if (history.length === 0) {
    energyTrendData.times = []
    energyTrendData.values = []
    energyTrendData.timestamps = []
    return
  }

  const sortedHistory = [...history].sort((left, right) => {
    const leftTimestamp = left.timestamp ? new Date(left.timestamp).getTime() : 0
    const rightTimestamp = right.timestamp ? new Date(right.timestamp).getTime() : 0
    return leftTimestamp - rightTimestamp
  })
  energyTrendData.times = sortedHistory.map((item) => item.timestamp?.substring(11, 19) || '')
  energyTrendData.values = sortedHistory.map((item) => Math.abs(item.flow_rate || 0))
  energyTrendData.timestamps = sortedHistory.map((item) => {
    const timestamp = item.timestamp ? new Date(item.timestamp).getTime() : Number.NaN
    return Number.isNaN(timestamp) ? 0 : timestamp
  })
}

function toApiDateTime(value: Date) {
  const year = value.getFullYear()
  const month = `${value.getMonth() + 1}`.padStart(2, '0')
  const day = `${value.getDate()}`.padStart(2, '0')
  const hours = `${value.getHours()}`.padStart(2, '0')
  const minutes = `${value.getMinutes()}`.padStart(2, '0')
  const seconds = `${value.getSeconds()}`.padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
}

function buildDashboardTrendRange() {
  const end = new Date()
  const start = new Date(end.getTime() - DASHBOARD_TREND_WINDOW_MS)
  return {
    start_time: toApiDateTime(start),
    end_time: toApiDateTime(end),
  }
}

function trimTrendToRecentWindow(
  energyTrendData: { times: string[]; values: number[]; timestamps: number[] },
  now: Date = new Date()
) {
  const cutoff = now.getTime() - DASHBOARD_TREND_WINDOW_MS

  while (energyTrendData.timestamps.length > 0 && energyTrendData.timestamps[0] < cutoff) {
    energyTrendData.timestamps.shift()
    energyTrendData.times.shift()
    energyTrendData.values.shift()
  }
}

export function useDashboardRealtime(options: {
  currentDeviceId: Ref<number | undefined>
  deviceList: Ref<Device[]>
  latestMessage: Ref<TelemetryMessage | null>
  pauseRealtime?: Ref<boolean>
}) {
  const { currentDeviceId, deviceList, latestMessage, pauseRealtime } = options

  const realTimeData = reactive({
    power: 0,
    energy: 0,
    current: 0,
    voltage: 0
  })

  const energyTrendData = reactive<{ times: string[]; values: number[]; timestamps: number[] }>({
    times: [],
    values: [],
    timestamps: []
  })
  const loading = reactive({
    device: false,
    trend: false
  })
  const analysisSnapshot = ref<DeviceAnalysis | null>(null)
  let requestToken = 0

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
    const deviceId = currentDeviceId.value
    const token = ++requestToken
    loading.device = true

    try {
      const [analysis, history] = await Promise.all([
        getAnalysis(deviceId),
        getHistory(deviceId, 240, buildDashboardTrendRange())
      ])

      if (token !== requestToken || currentDeviceId.value !== deviceId) return
      analysisSnapshot.value = analysis

      updateRealtimeMetrics({
        power: analysis.current_power || 0,
        energy: analysis.today_energy || 0,
        current: analysis.current || 0,
        voltage: analysis.voltage || 0
      })

      loading.trend = true
      updateTrendFromHistory(energyTrendData, history as HistoryPoint[])
    } catch {
      if (token === requestToken) {
        analysisSnapshot.value = null
        updateRealtimeMetrics({
          power: 0,
          energy: 0,
          current: 0,
          voltage: 0
        })
        energyTrendData.times = []
        energyTrendData.values = []
        energyTrendData.timestamps = []
      }
    } finally {
      if (token === requestToken) {
        loading.device = false
        loading.trend = false
      }
    }
  }

  const loadEnergyTrend = async () => {
    if (!currentDeviceId.value) return

    try {
      loading.trend = true
      const history = await getHistory(currentDeviceId.value, 240, buildDashboardTrendRange())
      updateTrendFromHistory(energyTrendData, history as HistoryPoint[])
    } catch {
      // 负荷曲线加载失败
    } finally {
      loading.trend = false
    }
  }

  watch(latestMessage, (message) => {
    if (pauseRealtime?.value) return
    if (message?.type !== 'telemetry_update' || !message.data) return

    if (message.data.device_id !== currentDeviceId.value) return

    updateRealtimeMetrics({
      power: message.data.power || 0,
      current: message.data.current || 0,
      voltage: message.data.voltage || 0
    })

    const time = message.data.timestamp?.substring(11, 19) || new Date().toTimeString().substring(0, 8)
    const power = Math.abs(message.data.power || 0)
    const timestamp = message.data.timestamp ? new Date(message.data.timestamp).getTime() : Date.now()

    energyTrendData.times.push(time)
    energyTrendData.values.push(power)
    energyTrendData.timestamps.push(Number.isNaN(timestamp) ? Date.now() : timestamp)
    trimTrendToRecentWindow(energyTrendData)
  })

  return {
    analysisSnapshot,
    displayCurrent,
    displayEnergy,
    displayPower,
    energyTrendData,
    isStorageDevice,
    loading,
    realTimeData,
    storageStatus,
    loadDeviceData,
    loadEnergyTrend,
    updateRealtimeMetrics
  }
}
