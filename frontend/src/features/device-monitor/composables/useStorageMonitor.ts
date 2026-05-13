import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { ComputedRef, Ref } from 'vue'
import type { MonitorOverview } from '@/api/deviceMonitor'
import {
  getStorageTelemetryHistory,
  getStorageTelemetryLatest,
  type StorageTelemetry,
} from '@/api/storage'
import type { StorageMetric, StorageRunState, StorageTone } from '@/features/device-monitor/components/storage/types'

const REFRESH_INTERVAL_MS = 5000

export interface UseStorageMonitorInput {
  deviceId: ComputedRef<number>
  overview: Ref<MonitorOverview | null>
  timeRange: Ref<[Date, Date] | null>
}

function toApiDate(value: Date) {
  const pad = (n: number) => `${n}`.padStart(2, '0')
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}:${pad(value.getSeconds())}`
}

function defaultTimeRange(): [Date, Date] {
  const end = new Date()
  const start = new Date(end.getTime() - 60 * 60 * 1000)
  return [start, end]
}

function displayNum(value: number | null | undefined, unit = '', digits = 1): string {
  if (value === null || value === undefined) return '--'
  return `${Number(value).toFixed(digits)}${unit ? ' ' + unit : ''}`
}

function formatDateTime(value?: string | null) {
  if (!value) return '暂无数据'
  const d = new Date(value)
  const pad = (n: number) => `${n}`.padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

export function useStorageMonitor(input: UseStorageMonitorInput) {
  const latestTelemetry = ref<StorageTelemetry | null>(null)
  const telemetryHistory = ref<StorageTelemetry[]>([])

  let requestToken = 0
  let refreshTimer: ReturnType<typeof setInterval> | null = null

  const archive = computed(() => input.overview.value?.archive)
  const runtimeStatus = computed(() => input.overview.value?.runtime_status)
  const storageMonitor = computed(() => input.overview.value?.storage_monitor ?? null)

  const isStorageDevice = computed(
    () => archive.value?.device_category === 'storage',
  )

  // ── run state ────────────────────────────────────────────────
  const runStateRaw = computed<StorageRunState>(() => {
    const raw = latestTelemetry.value?.run_state
    const valid: StorageRunState[] = ['charging', 'discharging', 'idle', 'standby', 'fault']
    return (valid.includes(raw as StorageRunState) ? raw : 'unknown') as StorageRunState
  })

  const runStateLabel = computed(() => {
    const map: Record<StorageRunState, string> = {
      charging: '充电中',
      discharging: '放电中',
      idle: '空闲',
      standby: '待机',
      fault: '故障',
      unknown: '未知',
    }
    return map[runStateRaw.value]
  })

  // ── SOC / power ──────────────────────────────────────────────
  const socValue = computed(() =>
    displayNum(latestTelemetry.value?.soc, '', 1),
  )
  const socState = computed(() =>
    latestTelemetry.value?.soc != null ? 'live' : 'missing',
  )

  const activePower = computed(() => latestTelemetry.value?.active_power ?? null)
  const powerValue = computed(() => displayNum(activePower.value, '', 1))
  const powerState = computed(() => activePower.value != null ? 'live' : 'missing')

  const powerDirection = computed<'charging' | 'discharging' | 'idle' | 'unknown'>(() => {
    const p = activePower.value
    if (p === null || p === undefined) return 'unknown'
    if (p > 0.5) return 'charging'
    if (p < -0.5) return 'discharging'
    return 'idle'
  })

  // ── secondary metrics grid ───────────────────────────────────
  const overviewMetrics = computed<StorageMetric[]>(() => [
    {
      key: 'soh',
      label: '健康状态（SOH）',
      value: displayNum(latestTelemetry.value?.soh, '%'),
      state: latestTelemetry.value?.soh != null ? 'live' : 'missing',
    },
    {
      key: 'charge_today',
      label: '今日充电量',
      value: displayNum(latestTelemetry.value?.charge_energy_today),
      unit: 'kWh',
      state: latestTelemetry.value?.charge_energy_today != null ? 'live' : 'missing',
    },
    {
      key: 'discharge_today',
      label: '今日放电量',
      value: displayNum(latestTelemetry.value?.discharge_energy_today),
      unit: 'kWh',
      state: latestTelemetry.value?.discharge_energy_today != null ? 'live' : 'missing',
    },
    {
      key: 'cycle_count',
      label: '循环次数',
      value: latestTelemetry.value?.cycle_count != null
        ? String(latestTelemetry.value.cycle_count)
        : '--',
      unit: '次',
      state: latestTelemetry.value?.cycle_count != null ? 'live' : 'missing',
    },
  ])

  // ── status panel fields ──────────────────────────────────────
  const controlModeLabel = computed(() => {
    const m = latestTelemetry.value?.control_mode
    if (m === 'auto') return '自动'
    if (m === 'manual') return '手动'
    return m ?? '--'
  })

  const ingestionTone = computed<StorageTone>(() => {
    const s = runtimeStatus.value?.ingestion_status
    if (s === 'online') return 'success'
    if (s === 'degraded') return 'warning'
    if (s === 'offline') return 'danger'
    return 'neutral'
  })

  const ingestionStatusLabel = computed(() => {
    const s = runtimeStatus.value?.ingestion_status
    if (s === 'online') return '在线采集'
    if (s === 'degraded') return '采集波动'
    if (s === 'offline') return '离线'
    return '未知'
  })

  const latestSampleText = computed(() =>
    formatDateTime(latestTelemetry.value?.timestamp),
  )

  // ── data loading ─────────────────────────────────────────────
  async function loadLatestTelemetry() {
    try {
      latestTelemetry.value = await getStorageTelemetryLatest(input.deviceId.value)
    } catch {
      latestTelemetry.value = null
    }
  }

  async function loadTelemetryHistory() {
    try {
      const [start, end] = input.timeRange.value || defaultTimeRange()
      const records = await getStorageTelemetryHistory(input.deviceId.value, {
        start: toApiDate(start),
        end: toApiDate(end),
        limit: 200,
      })
      telemetryHistory.value = [...records].sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      )
    } catch {
      telemetryHistory.value = []
    }
  }

  async function refreshStorageData() {
    const token = ++requestToken
    await loadLatestTelemetry()
    if (token !== requestToken) return
  }

  onMounted(() => {
    refreshTimer = setInterval(() => void refreshStorageData(), REFRESH_INTERVAL_MS)
  })

  onBeforeUnmount(() => {
    requestToken++
    if (refreshTimer) clearInterval(refreshTimer)
  })

  return {
    latestTelemetry,
    telemetryHistory,
    isStorageDevice,
    storageMonitor,
    runtimeStatus,
    runStateRaw,
    runStateLabel,
    socValue,
    socState,
    powerValue,
    powerState,
    powerDirection,
    overviewMetrics,
    controlModeLabel,
    ingestionTone,
    ingestionStatusLabel,
    latestSampleText,
    loadLatestTelemetry,
    loadTelemetryHistory,
    refreshStorageData,
  }
}
