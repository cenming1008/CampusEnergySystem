import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { ComputedRef, Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getDeviceMonitorControlLogs } from '@/api/deviceMonitor'
import type { DeviceControlLog, MonitorOverview } from '@/api/deviceMonitor'
import {
  getStorageControlCapabilities,
  getStorageProfile,
  getStorageTelemetryHistory,
  getStorageTelemetryLatest,
  sendStorageControl,
  updateStorageProfile,
  type StorageAssetProfile,
  type StorageAssetProfileUpdate,
  type StorageControlCapabilities,
  type StorageControlRequest,
  type StorageTelemetry,
} from '@/api/storage'
import type {
  StorageCommandTimelineItem,
  StorageMetric,
  StorageRunState,
  StorageTone,
} from '@/features/device-monitor/components/storage/types'

const REFRESH_INTERVAL_MS = 5000

export interface UseStorageMonitorInput {
  deviceId: ComputedRef<number>
  overview: Ref<MonitorOverview | null>
  timeRange: Ref<[Date, Date] | null>
  canControl?: ComputedRef<boolean>
  isAdmin?: ComputedRef<boolean>
  socketMessage?: Ref<{
    type?: string
    data?: { device_id?: number; command_id?: string; result?: string }
  } | null>
  refreshOverview?: () => Promise<void>
  enableLifecycle?: boolean
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
  const assetProfile = ref<StorageAssetProfile | null>(null)
  const controlCapabilities = ref<StorageControlCapabilities | null>(null)
  const controlLogs = ref<DeviceControlLog[]>([])
  const localAcceptedCommands = ref<StorageCommandTimelineItem[]>([])
  const controlSubmitting = ref(false)

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

  const targetPower = computed(() => latestTelemetry.value?.target_active_power ?? null)
  const targetPowerDirectionLabel = computed(() => {
    const target = targetPower.value
    if (target == null) return '--'
    if (target > 0) return '充电'
    if (target < 0) return '放电'
    return '待机'
  })
  const powerDeviation = computed(() => {
    if (activePower.value == null || targetPower.value == null) return null
    return activePower.value - targetPower.value
  })
  const dataSourceLabel = computed(() => {
    if (latestTelemetry.value?.data_source === 'simulated') return '仿真数据'
    if (latestTelemetry.value?.data_source === 'real') return '真实设备'
    return '数据来源未知'
  })
  const commandSourceLabel = computed(() => {
    const source = latestTelemetry.value?.command_source
    if (source === 'manual') return '人工控制'
    if (source === 'rule') return '规则 EMS'
    if (source === 'day_ahead') return '日前计划'
    if (source === 'scenario') return '仿真场景'
    return source || '--'
  })
  const currentPlanLabel = computed(() =>
    latestTelemetry.value?.command_source === 'day_ahead' ? '日前计划执行中' : '--',
  )
  const canControl = computed(() => input.canControl?.value ?? true)
  const canManageAuto = computed(() => input.isAdmin?.value ?? false)
  const autoAuthorized = computed(() => Boolean(assetProfile.value?.ems_auto_enabled))

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

  function parseReason(reason?: string | null): Record<string, unknown> {
    if (!reason) return {}
    try {
      const parsed = JSON.parse(reason)
      return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
        ? parsed as Record<string, unknown>
        : { legacy_reason: reason }
    } catch {
      return { legacy_reason: reason }
    }
  }

  function resultLabel(result?: string) {
    const labels: Record<string, string> = {
      accepted: '已接收',
      running: '执行中',
      success: '执行成功',
      failed: '执行失败',
      rejected: '已拒绝',
      timeout: '执行超时',
    }
    return labels[result || ''] || result || '未知'
  }

  function toTimelineItem(log: DeviceControlLog): StorageCommandTimelineItem {
    const reason = parseReason(log.reason)
    const target = reason.target_active_power
    const mode = reason.control_mode
    const actionLabel = log.action === 'set_active_power'
      ? `设置功率 ${typeof target === 'number' ? target.toFixed(1) : '--'} kW`
      : log.action === 'set_control_mode'
        ? `切换为${mode === 'auto' ? '自动' : mode === 'manual' ? '手动' : '--'}模式`
        : log.action === 'stop'
          ? '停止充放电'
          : log.action
    const detail = reason.receipt_detail
      || reason.timeout_detail
      || reason.operator_reason
      || reason.legacy_reason
      || ''
    return {
      commandId: String(log.id),
      actionLabel,
      result: log.result || 'accepted',
      resultLabel: resultLabel(log.result),
      detail: String(detail),
      createdAt: formatDateTime(log.created_at),
    }
  }

  const backendCommandTimeline = computed(() => controlLogs.value.map(toTimelineItem))
  const commandTimeline = computed(() => {
    const backendIds = new Set(backendCommandTimeline.value.map(item => item.commandId))
    return [
      ...localAcceptedCommands.value.filter(item => !backendIds.has(item.commandId)),
      ...backendCommandTimeline.value,
    ].slice(0, 20)
  })
  const commandPending = computed(() =>
    commandTimeline.value.some(item => ['accepted', 'running'].includes(item.result)),
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

  async function loadAssetProfile() {
    try {
      assetProfile.value = await getStorageProfile(input.deviceId.value)
    } catch {
      assetProfile.value = null
    }
  }

  async function loadControlCapabilities() {
    try {
      controlCapabilities.value = await getStorageControlCapabilities(input.deviceId.value)
    } catch {
      controlCapabilities.value = null
    }
  }

  async function loadControlLogs() {
    try {
      const response = await getDeviceMonitorControlLogs(input.deviceId.value, {
        limit: 20,
        hours: 168,
      })
      controlLogs.value = response.items
    } catch {
      controlLogs.value = []
    }
  }

  async function loadWorkbench() {
    await Promise.all([loadAssetProfile(), loadControlCapabilities(), loadControlLogs()])
  }

  async function issueControl(body: StorageControlRequest) {
    if (!canControl.value || commandPending.value || controlSubmitting.value) return
    controlSubmitting.value = true
    try {
      const response = await sendStorageControl(input.deviceId.value, body)
      localAcceptedCommands.value.unshift({
        commandId: response.command_id,
        actionLabel: body.command === 'set_active_power'
          ? `设置功率 ${Number(body.target_active_power).toFixed(1)} kW`
          : body.command === 'set_control_mode'
            ? `切换为${body.control_mode === 'auto' ? '自动' : '手动'}模式`
            : '停止充放电',
        result: response.status,
        resultLabel: resultLabel(response.status),
        detail: response.message,
        createdAt: formatDateTime(new Date().toISOString()),
      })
      await Promise.all([
        loadControlLogs(),
        loadLatestTelemetry(),
        input.refreshOverview?.() ?? Promise.resolve(),
      ])
      ElMessage.success('储能控制命令已接收，等待设备执行回执')
    } catch {
      ElMessage.error('储能控制命令下发失败')
    } finally {
      controlSubmitting.value = false
    }
  }

  async function sendManualPower(target: number) {
    await issueControl({
      command: 'set_active_power',
      source: 'manual',
      target_active_power: target,
    })
  }

  async function setControlMode(mode: 'auto' | 'manual') {
    await issueControl({ command: 'set_control_mode', source: 'manual', control_mode: mode })
  }

  async function stopStorage() {
    await issueControl({ command: 'stop', source: 'manual' })
  }

  function profileUpdateBody(profile: StorageAssetProfile): StorageAssetProfileUpdate {
    return {
      rated_energy_kwh: profile.rated_energy_kwh,
      rated_power_kw: profile.rated_power_kw,
      max_charge_power_kw: profile.max_charge_power_kw,
      max_discharge_power_kw: profile.max_discharge_power_kw,
      charge_efficiency: profile.charge_efficiency,
      discharge_efficiency: profile.discharge_efficiency,
      soc_min: profile.soc_min,
      soc_max: profile.soc_max,
      soc_soft_min: profile.soc_soft_min,
      soc_soft_max: profile.soc_soft_max,
      rated_ac_voltage: profile.rated_ac_voltage,
      rated_dc_voltage: profile.rated_dc_voltage,
      battery_type: profile.battery_type,
      bms_model: profile.bms_model,
      pcs_model: profile.pcs_model,
      protocol_version: profile.protocol_version,
      installation_location: profile.installation_location,
      commission_date: profile.commission_date,
      data_source: profile.data_source,
      ems_auto_enabled: profile.ems_auto_enabled,
    }
  }

  async function setAutoAuthorization(enabled: boolean) {
    if (!canManageAuto.value || !assetProfile.value || commandPending.value) return
    controlSubmitting.value = true
    try {
      assetProfile.value = await updateStorageProfile(input.deviceId.value, {
        ...profileUpdateBody(assetProfile.value),
        ems_auto_enabled: enabled,
      })
      await loadControlCapabilities()
      ElMessage.success(enabled ? '已允许 EMS 自动控制' : '已关闭 EMS 自动控制')
    } catch {
      ElMessage.error('EMS 自动控制授权更新失败')
    } finally {
      controlSubmitting.value = false
    }
  }

  async function refreshStorageData() {
    const token = ++requestToken
    await loadLatestTelemetry()
    if (token !== requestToken) return
  }

  if (input.socketMessage) {
    watch(
      () => input.socketMessage?.value,
      (message) => {
        if (message?.type !== 'device_control_log_update') return
        if (Number(message.data?.device_id) !== Number(input.deviceId.value)) return
        void loadControlLogs()
      },
    )
  }

  if (input.enableLifecycle !== false) {
    onMounted(() => {
      void loadWorkbench()
      refreshTimer = setInterval(() => void refreshStorageData(), REFRESH_INTERVAL_MS)
    })
    onBeforeUnmount(() => {
      requestToken++
      if (refreshTimer) clearInterval(refreshTimer)
    })
  }

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
    targetPower,
    targetPowerDirectionLabel,
    powerDeviation,
    dataSourceLabel,
    commandSourceLabel,
    currentPlanLabel,
    overviewMetrics,
    controlModeLabel,
    ingestionTone,
    ingestionStatusLabel,
    latestSampleText,
    assetProfile,
    controlCapabilities,
    controlLogs,
    commandTimeline,
    commandPending,
    controlSubmitting,
    canControl,
    canManageAuto,
    autoAuthorized,
    loadLatestTelemetry,
    loadTelemetryHistory,
    loadAssetProfile,
    loadControlCapabilities,
    loadControlLogs,
    loadWorkbench,
    refreshStorageData,
    sendManualPower,
    setControlMode,
    stopStorage,
    setAutoAuthorization,
  }
}
