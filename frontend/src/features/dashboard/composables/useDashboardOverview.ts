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
import { isDemoModeEnabled, suppressDemoMode } from '@/shared/demoMode'
import { useSocketStore } from '@/stores/useSocketStore'
import {
  FALLBACK_INGESTION_HEALTH,
  FALLBACK_DEVICES,
  FALLBACK_OVERVIEW,
  FALLBACK_PREVIOUS_OVERVIEW,
  FALLBACK_RANKING,
  FALLBACK_TREND,
  FALLBACK_TREND_BY_RANGE,
} from './mockFallback'

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

function hasOverviewData(value: CampusOverview | null) {
  const analysis = value?.analysis_summary
  const hasConsumption = Number(analysis?.total_consumption || 0) > 0
  const hasEnergyMix = Boolean(value?.energy_category_summary?.some((item) => Number(item.total_consumption || 0) > 0))
  return Boolean(value?.analysis_summary && hasConsumption && hasEnergyMix)
}

function hasTrendData(value: PerMediumTrend) {
  return Object.values(value).some((items) => items.some((item) => item.v > 0))
}

function hasDashboardMatrixCoverage(devices: Device[], kind: 'electricity' | 'pv-storage' | 'cool-heat' | 'water-gas') {
  return devices.some((device) => {
    if (kind === 'electricity') {
      return device.energy_type === 'electricity' && device.device_type !== 'storage' && device.device_type !== 'pv'
    }
    if (kind === 'pv-storage') {
      return device.device_type === 'pv' || device.device_type === 'storage' || /光伏|储能|PV/i.test(device.name || '')
    }
    if (kind === 'cool-heat') {
      return device.energy_type === 'cooling' || device.energy_type === 'heat'
    }
    return device.energy_type === 'water' || device.energy_type === 'gas'
  })
}

function mergeFallbackDevices(devices: Device[]) {
  const next = [...devices]
  const missingKinds = (['electricity', 'pv-storage', 'cool-heat', 'water-gas'] as const)
    .filter((kind) => !hasDashboardMatrixCoverage(devices, kind))
  if (missingKinds.length === 0) return next

  for (const device of FALLBACK_DEVICES) {
    if (
      (missingKinds.includes('electricity') && device.energy_type === 'electricity' && device.device_type !== 'storage' && device.device_type !== 'pv') ||
      (missingKinds.includes('pv-storage') && (device.device_type === 'pv' || device.device_type === 'storage')) ||
      (missingKinds.includes('cool-heat') && (device.energy_type === 'cooling' || device.energy_type === 'heat')) ||
      (missingKinds.includes('water-gas') && (device.energy_type === 'water' || device.energy_type === 'gas'))
    ) {
      next.push(device)
    }
  }
  return next
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
  const perMediumTrendByRange = ref<Record<'today' | 'yest' | 'week' | 'month', PerMediumTrend>>({
    today: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
    yest: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
    week: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
    month: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
  })
  const deviceList = ref<Device[]>([])
  const storageSOC = ref<number | null>(null)
  const pvCurrentPower = ref<number | null>(null)
  const demoMode = ref(false)
  const loading = reactive({ overview: false, trend: false, devices: false })
  const realSource = reactive({
    overview: false,
    previousOverview: false,
    trend: false,
    ingestion: false,
    devices: false,
    pvStorage: false,
  })

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

  const isMock = computed(() => demoMode.value)

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

  const applyDashboardDemoData = () => {
    demoMode.value = true
    overview.value = FALLBACK_OVERVIEW
    previousOverview.value = FALLBACK_PREVIOUS_OVERVIEW
    ingestionHealth.value = FALLBACK_INGESTION_HEALTH
    perMediumTrend.value = FALLBACK_TREND
    perMediumTrendByRange.value = FALLBACK_TREND_BY_RANGE
    deviceList.value = FALLBACK_DEVICES
    pvCurrentPower.value = 286
    storageSOC.value = 74
    realSource.overview = false
    realSource.previousOverview = false
    realSource.trend = false
    realSource.ingestion = false
    realSource.devices = false
    realSource.pvStorage = false
  }

  const loadDevices = async () => {
    if (isDemoModeEnabled()) {
      applyDashboardDemoData()
      return
    }
    loading.devices = true
    try {
      const devices = await getDevices({ silent: true })
      deviceList.value = devices
      realSource.devices = devices.length > 0
      if (devices.length > 0) demoMode.value = false
    } catch {
      deviceList.value = []
      realSource.devices = false
    } finally {
      loading.devices = false
    }
  }

  const loadOverview = async () => {
    if (isDemoModeEnabled()) {
      applyDashboardDemoData()
      return
    }
    loading.overview = true
    try {
      const data = await getCampusOverview({}, { silent: true })
      overview.value = hasOverviewData(data) ? data : null
      realSource.overview = hasOverviewData(data)
      if (realSource.overview) demoMode.value = false
      if (!realSource.overview && demoMode.value) overview.value = FALLBACK_OVERVIEW
    } catch {
      overview.value = demoMode.value ? FALLBACK_OVERVIEW : null
      realSource.overview = false
    } finally {
      loading.overview = false
    }
  }

  const loadPreviousOverview = async () => {
    if (isDemoModeEnabled()) {
      previousOverview.value = FALLBACK_PREVIOUS_OVERVIEW
      realSource.previousOverview = false
      return
    }
    try {
      const data = await getCampusOverview(buildPrevWindow(), { silent: true })
      previousOverview.value = hasOverviewData(data) ? data : null
      realSource.previousOverview = hasOverviewData(data)
      if (realSource.previousOverview) demoMode.value = false
      if (!realSource.previousOverview && demoMode.value) previousOverview.value = FALLBACK_PREVIOUS_OVERVIEW
    } catch {
      previousOverview.value = demoMode.value ? FALLBACK_PREVIOUS_OVERVIEW : null
      realSource.previousOverview = false
    }
  }

  const loadTrend = async () => {
    if (isDemoModeEnabled()) {
      demoMode.value = true
      perMediumTrend.value = FALLBACK_TREND
      perMediumTrendByRange.value = FALLBACK_TREND_BY_RANGE
      realSource.trend = false
      return
    }
    loading.trend = true
    try {
      const data: EnergyOverview = await getEnergyOverview({
        ...build24hWindow(),
        granularity: 'hour',
        include_analysis: true,
      }, { silent: true })
      const trendItems = data.trend?.items || []
      const nextTrend = bucketByHour(trendItems as Array<{ timestamp?: string; energy_breakdown?: Record<string, number> | null; total_consumption?: number }>)
      perMediumTrend.value = hasTrendData(nextTrend) ? nextTrend : { electricity: [], cooling: [], heat: [], water: [], gas: [] }
      perMediumTrendByRange.value = hasTrendData(nextTrend)
        ? {
            today: nextTrend,
            yest: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
            week: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
            month: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
          }
        : {
            today: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
            yest: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
            week: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
            month: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
          }
      realSource.trend = hasTrendData(nextTrend)
      if (realSource.trend) demoMode.value = false
      if (!realSource.trend && demoMode.value) {
        perMediumTrend.value = FALLBACK_TREND
        perMediumTrendByRange.value = FALLBACK_TREND_BY_RANGE
      }
    } catch {
      perMediumTrend.value = demoMode.value ? FALLBACK_TREND : { electricity: [], cooling: [], heat: [], water: [], gas: [] }
      perMediumTrendByRange.value = demoMode.value
        ? FALLBACK_TREND_BY_RANGE
        : {
            today: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
            yest: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
            week: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
            month: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
          }
      realSource.trend = false
    } finally {
      loading.trend = false
    }
  }

  const loadIngestionHealth = async () => {
    if (isDemoModeEnabled()) {
      demoMode.value = true
      ingestionHealth.value = FALLBACK_INGESTION_HEALTH
      realSource.ingestion = false
      return
    }
    try {
      const items = await getIngestionHealthOverview({ silent: true })
      ingestionHealth.value = items
      realSource.ingestion = items.length > 0
      if (items.length > 0) demoMode.value = false
      if (items.length === 0 && demoMode.value) ingestionHealth.value = FALLBACK_INGESTION_HEALTH
    } catch {
      ingestionHealth.value = demoMode.value ? FALLBACK_INGESTION_HEALTH : []
      realSource.ingestion = false
    }
  }

  const loadPvStorage = async () => {
    if (isDemoModeEnabled() || demoMode.value) {
      pvCurrentPower.value = 286
      storageSOC.value = 74
      realSource.pvStorage = false
      return
    }
    const pv = pvDevices.value
    const storage = storageDevices.value
    if (pv.length === 0 && storage.length === 0) {
      if (isMock.value) {
        pvCurrentPower.value = 286
        storageSOC.value = 74
        realSource.pvStorage = false
      } else {
        pvCurrentPower.value = null
        storageSOC.value = null
        realSource.pvStorage = false
      }
      return
    }
    const allCalls = [
      ...pv.map((d) => getDeviceMonitorOverview(d.id!, { silent: true }).catch(() => null)),
      ...storage.map((d) => getDeviceMonitorOverview(d.id!, { silent: true }).catch(() => null)),
    ]
    const results = await Promise.all(allCalls)
    const pvResults = results.slice(0, pv.length)
    const storageResults = results.slice(pv.length)

    if (pv.length > 0) {
      let total = 0
      let any = false
      for (const r of pvResults) {
        if (!r?.realtime) continue
        const value = Number(r.realtime.flow_rate)
        if (Number.isFinite(value)) {
          total += Math.abs(value)
          any = true
        }
      }
      pvCurrentPower.value = any ? total : null
      realSource.pvStorage = any
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
      realSource.pvStorage = realSource.pvStorage || count > 0
    } else {
      storageSOC.value = null
    }
  }

  const refreshAll = async () => {
    if (isDemoModeEnabled()) {
      applyDashboardDemoData()
      return
    }
    demoMode.value = false
    await Promise.all([loadOverview(), loadTrend(), loadIngestionHealth()])
    await loadPvStorage()
  }

  const exitDemoMode = () => {
    suppressDemoMode()
    demoMode.value = false
    overview.value = null
    previousOverview.value = null
    ingestionHealth.value = []
    perMediumTrend.value = { electricity: [], cooling: [], heat: [], water: [], gas: [] }
    perMediumTrendByRange.value = {
      today: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
      yest: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
      week: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
      month: { electricity: [], cooling: [], heat: [], water: [], gas: [] },
    }
    deviceList.value = []
    pvCurrentPower.value = null
    storageSOC.value = null
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
    socketStore.connect({ silent: true })
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
    perMediumTrendByRange,
    rankings,
    prevRankingMap,
    deviceList,
    pvDevices,
    storageDevices,
    pvCurrentPower,
    storageSOC,
    samplingOnline,
    samplingTotal,
    isMock,
    loading,
    refreshAll,
    exitDemoMode,
  }
}
