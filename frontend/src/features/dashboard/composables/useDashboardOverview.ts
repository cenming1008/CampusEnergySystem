import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import {
  getCampusOverview,
  type CampusOverview,
  type LocationRankingItem,
} from '@/api/campus'
import { getEnergyOverview, type EnergyOverview } from '@/api/energy'
import {
  getDeviceMonitorOverview,
  getIngestionHealthOverview,
  type DeviceIngestionHealthItem,
} from '@/api/deviceMonitor'
import { getDevices, type Device } from '@/api/device'
import { useSocketStore } from '@/stores/useSocketStore'

const OVERVIEW_REFRESH_MS = 30_000
const PV_STORAGE_REFRESH_MS = 15_000
const HOURS_24_MS = 24 * 60 * 60 * 1000

interface TrendPoint { t: string; v: number }
type PerMediumTrend = Record<string, TrendPoint[]>

const MEDIUM_KEYS = ['electricity', 'cooling', 'heat', 'water', 'gas'] as const

function toApiDateTime(value: Date) {
  const pad = (n: number) => `${n}`.padStart(2, '0')
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}:${pad(value.getSeconds())}`
}

function build24hWindow() {
  const end = new Date()
  const start = new Date(end.getTime() - HOURS_24_MS)
  return { start_time: toApiDateTime(start), end_time: toApiDateTime(end) }
}

function buildPrevWindow() {
  const end = new Date(Date.now() - HOURS_24_MS)
  const start = new Date(end.getTime() - HOURS_24_MS)
  return { start_time: toApiDateTime(start), end_time: toApiDateTime(end) }
}

function bucketByHour(items: Array<{ timestamp?: string; energy_breakdown?: Record<string, number> | null; total_consumption?: number }>): PerMediumTrend {
  const out: PerMediumTrend = {}
  for (const key of MEDIUM_KEYS) out[key] = []
  for (const item of items || []) {
    if (!item.timestamp) continue
    const t = item.timestamp.slice(11, 16)
    const breakdown = item.energy_breakdown || {}
    for (const key of MEDIUM_KEYS) {
      const value = Number(breakdown[key] || 0)
      out[key].push({ t, v: Number.isFinite(value) ? value : 0 })
    }
  }
  return out
}

interface TelemetryMessage {
  type?: string
  data?: {
    device_id?: number
    power?: number
    timestamp?: string
  }
}

export function useDashboardOverview() {
  const overview = ref<CampusOverview | null>(null)
  const previousOverview = ref<CampusOverview | null>(null)
  const ingestionHealth = ref<DeviceIngestionHealthItem[]>([])
  const perMediumTrend = ref<PerMediumTrend>({ electricity: [], cooling: [], heat: [], water: [], gas: [] })
  const deviceList = ref<Device[]>([])
  const storageSOC = ref<number | null>(null)
  const pvCurrentPower = ref<number | null>(null)
  const loading = reactive({ overview: false, trend: false, devices: false })

  const socketStore = useSocketStore()
  const { latestMessage } = storeToRefs(socketStore)

  let overviewTimer: ReturnType<typeof setInterval> | null = null
  let pvStorageTimer: ReturnType<typeof setInterval> | null = null

  const pvDevices = computed(() => deviceList.value.filter(
    (d) => d.device_type === 'pv' || /光伏|PV/i.test(d.name || '')
  ))
  const storageDevices = computed(() => deviceList.value.filter(
    (d) => d.device_type === 'storage' || /储能/.test(d.name || '')
  ))

  const rankings = computed<LocationRankingItem[]>(() => {
    const map = overview.value?.location_rankings || {}
    return (map.area || map.building || []) as LocationRankingItem[]
  })

  const prevRankingMap = computed<Record<number, number>>(() => {
    const map = previousOverview.value?.location_rankings || {}
    const items = (map.area || map.building || []) as LocationRankingItem[]
    const out: Record<number, number> = {}
    for (const item of items) out[item.location_id] = item.total_consumption
    return out
  })

  const ingestionByDevice = computed<Record<number, DeviceIngestionHealthItem>>(() => {
    const out: Record<number, DeviceIngestionHealthItem> = {}
    for (const item of ingestionHealth.value) out[item.device_id] = item
    return out
  })

  const samplingOnline = computed(() => ingestionHealth.value.filter((item) => item.is_online).length)
  const samplingTotal = computed(() => ingestionHealth.value.length || deviceList.value.length)

  const loadDevices = async () => {
    loading.devices = true
    try {
      deviceList.value = await getDevices()
    } catch {
      deviceList.value = []
    } finally {
      loading.devices = false
    }
  }

  const loadOverview = async () => {
    loading.overview = true
    try {
      overview.value = await getCampusOverview()
    } catch {
      overview.value = null
    } finally {
      loading.overview = false
    }
  }

  const loadPreviousOverview = async () => {
    try {
      previousOverview.value = await getCampusOverview(buildPrevWindow())
    } catch {
      previousOverview.value = null
    }
  }

  const loadTrend = async () => {
    loading.trend = true
    try {
      const data: EnergyOverview = await getEnergyOverview({
        ...build24hWindow(),
        granularity: 'hour',
        include_analysis: true,
      })
      const trendItems = data.trend?.items || []
      perMediumTrend.value = bucketByHour(trendItems as Array<{ timestamp?: string; energy_breakdown?: Record<string, number> | null; total_consumption?: number }>)
    } catch {
      perMediumTrend.value = { electricity: [], cooling: [], heat: [], water: [], gas: [] }
    } finally {
      loading.trend = false
    }
  }

  const loadIngestionHealth = async () => {
    try {
      ingestionHealth.value = await getIngestionHealthOverview()
    } catch {
      ingestionHealth.value = []
    }
  }

  const loadPvStorage = async () => {
    const pv = pvDevices.value
    const storage = storageDevices.value
    if (pv.length === 0 && storage.length === 0) {
      pvCurrentPower.value = null
      storageSOC.value = null
      return
    }
    const allCalls = [
      ...pv.map((d) => getDeviceMonitorOverview(d.id!).catch(() => null)),
      ...storage.map((d) => getDeviceMonitorOverview(d.id!).catch(() => null)),
    ]
    const results = await Promise.all(allCalls)
    const pvResults = results.slice(0, pv.length)
    const storageResults = results.slice(pv.length)

    if (pv.length > 0) {
      let total = 0
      let any = false
      for (const r of pvResults) {
        const value = Number(r?.realtime?.flow_rate || 0)
        if (Number.isFinite(value)) {
          total += Math.abs(value)
          any = true
        }
      }
      pvCurrentPower.value = any ? total : null
    } else {
      pvCurrentPower.value = null
    }

    if (storage.length > 0) {
      let socSum = 0
      let count = 0
      for (const r of storageResults) {
        const metric = r?.storage_monitor?.key_metrics?.soc
        const value = typeof metric?.value === 'number' ? metric.value : Number(metric?.value || NaN)
        if (Number.isFinite(value)) {
          socSum += value
          count += 1
        }
      }
      storageSOC.value = count > 0 ? socSum / count : null
    } else {
      storageSOC.value = null
    }
  }

  const refreshAll = async () => {
    await Promise.all([loadOverview(), loadTrend(), loadIngestionHealth()])
    await loadPvStorage()
  }

  watch(latestMessage, (message: TelemetryMessage | null) => {
    if (!message || message.type !== 'telemetry_update' || !message.data) return
    const deviceId = message.data.device_id
    if (typeof deviceId !== 'number') return
    if (pvDevices.value.some((d) => d.id === deviceId)) {
      const power = Math.abs(Number(message.data.power || 0))
      if (Number.isFinite(power)) {
        pvCurrentPower.value = (pvCurrentPower.value || 0) + 0
        pvCurrentPower.value = power
      }
    }
  })

  onMounted(async () => {
    socketStore.connect()
    await loadDevices()
    await refreshAll()
    void loadPreviousOverview()
    overviewTimer = setInterval(() => {
      void loadOverview()
      void loadIngestionHealth()
    }, OVERVIEW_REFRESH_MS)
    pvStorageTimer = setInterval(() => {
      void loadPvStorage()
    }, PV_STORAGE_REFRESH_MS)
  })

  onUnmounted(() => {
    if (overviewTimer) clearInterval(overviewTimer)
    if (pvStorageTimer) clearInterval(pvStorageTimer)
  })

  return {
    overview,
    previousOverview,
    ingestionHealth,
    ingestionByDevice,
    perMediumTrend,
    rankings,
    prevRankingMap,
    deviceList,
    pvDevices,
    storageDevices,
    pvCurrentPower,
    storageSOC,
    samplingOnline,
    samplingTotal,
    loading,
    refreshAll,
  }
}
