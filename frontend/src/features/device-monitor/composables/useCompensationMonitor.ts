import { computed, onBeforeUnmount, ref } from 'vue'
import type { ComputedRef, Ref } from 'vue'
import type { DeviceStatusEvent, DeviceTrendResponse } from '@/api/deviceMonitor'
import {
  getCompensationCapacitorBankControlProfile,
  getCompensationCapacitorBankTelemetryHistory,
  getCompensationCapacitorBankTelemetryLatest,
  getCompensationSvgOperationsProfile,
  getCompensationSvgTelemetryHistory,
  getCompensationSvgTelemetryLatest,
  type CompensationCapacitorBankControlProfile,
  type CompensationCapacitorBankTelemetry,
  type CompensationSvgOperationsProfile,
  type CompensationSvgTelemetry,
} from '@/api/compensation'
import type { CompensationMonitor, MonitorOverview } from '@/api/deviceMonitor'
import { resolveCompensationSubtype } from '@/shared/compensationDevices'
import { getDeviceCategoryLabel, getDeviceSubtypeLabel } from '@/shared/deviceTypeLabels'
import {
  calculateHistoryLimit,
  getTrendMaxPoints,
  sampleTimeSeriesByTimestamp,
} from '@/features/device-monitor/components/compensation/trendSampling'
import {
  buildCapacitorBankControlSummaryView,
  buildCompensationExtendedHint,
  buildCompensationHeaderView,
  buildCompensationModuleStatusView,
  buildCompensationOverviewMetrics,
  buildCompensationProfileItems,
  buildCompensationSemanticView,
  buildCompensationStatusItems,
  buildCompensationTrendView,
  describeCompensationSource,
} from '@/features/device-monitor/components/compensation/viewMapping'
import type {
  CompensationEventItem,
  CompensationHeaderModel,
  CompensationMetric,
  CompensationProfileItem,
  CompensationStatusItem,
  CompensationTone,
  CompensationTrendModel,
  CompensationTrendOption,
  CompensationTrendTab,
  ModuleStatusModel,
} from '@/features/device-monitor/components/compensation/types'

export interface UseCompensationMonitorInput {
  deviceId: ComputedRef<number>
  overview: Ref<MonitorOverview | null>
  trend: Ref<DeviceTrendResponse | null>
  statusHistory: Ref<DeviceStatusEvent[]>
  timeRange: Ref<[Date, Date] | null>
  compensationTrendTab: Ref<CompensationTrendTab>
  canControlDevices: ComputedRef<boolean>
}

export const REALTIME_FRESH_THRESHOLD_MS = 120_000
const EVENT_TIMELINE_LIMIT = 20

export function isTimestampFresh(
  timestamp: string | null | undefined,
  thresholdMs: number = REALTIME_FRESH_THRESHOLD_MS,
  now: number = Date.now(),
): boolean {
  if (!timestamp) return false
  const parsed = Date.parse(timestamp)
  if (Number.isNaN(parsed)) return false
  return now - parsed <= thresholdMs
}

function defaultTimeRange(): [Date, Date] {
  const end = new Date()
  const start = new Date(end.getTime() - 60 * 60 * 1000)
  return [start, end]
}

function toApiDate(value: Date) {
  const year = value.getFullYear()
  const month = `${value.getMonth() + 1}`.padStart(2, '0')
  const day = `${value.getDate()}`.padStart(2, '0')
  const hours = `${value.getHours()}`.padStart(2, '0')
  const minutes = `${value.getMinutes()}`.padStart(2, '0')
  const seconds = `${value.getSeconds()}`.padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
}

function displayValueWithState(value: number | string | null | undefined, emptyText: string, digits: number = 1) {
  if (value === null || value === undefined || value === '') return emptyText
  if (typeof value === 'number') return Number(value).toFixed(digits)
  return String(value)
}

function normalizePowerFactorTarget(value?: number | null) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null
  const numeric = Number(value)
  return numeric > 2 ? numeric / 100 : numeric
}

function formatIngestionStatus(status?: string | null) {
  if (status === 'online') return '在线采集'
  if (status === 'degraded') return '采集波动'
  if (status === 'offline') return '离线'
  return '未知'
}

function ingestionTone(status?: string | null): CompensationTone {
  if (status === 'online') return 'success'
  if (status === 'degraded') return 'warning'
  if (status === 'offline') return 'danger'
  return 'neutral'
}

function formatDateTime(value?: string | null) {
  if (!value) return '暂无数据'
  const date = new Date(value)
  return `${date.getFullYear()}-${`${date.getMonth() + 1}`.padStart(2, '0')}-${`${date.getDate()}`.padStart(2, '0')} ${`${date.getHours()}`.padStart(2, '0')}:${`${date.getMinutes()}`.padStart(2, '0')}:${`${date.getSeconds()}`.padStart(2, '0')}`
}

function formatTimeOnly(value?: string | null) {
  if (!value) return '--:--'
  return new Date(value).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

function statusText(flag: boolean | undefined, offlineText: string) {
  return flag ? '运行中' : offlineText
}

function historyTone(status?: string, eventType?: string): CompensationTone {
  if (status === 'success' || status === 'resolved') return 'success'
  if (status === 'running') return 'info'
  if (status === 'accepted') return 'warning'
  if (status === 'active' || status === 'failed' || status === 'timeout' || status === 'rejected') return 'danger'
  if (eventType === 'control') return 'info'
  return 'warning'
}

function historyTag(status?: string, eventType?: string) {
  if (eventType === 'alarm_resolution') return '已处理'
  if (status === 'resolved') return '已恢复'
  if (status === 'success') return '已处理'
  if (status === 'running') return '执行中'
  if (status === 'accepted') return '已入队'
  if (status === 'timeout') return '超时'
  if (status === 'rejected') return '拒绝'
  if (status === 'active') return '告警'
  return '事件'
}

function severityText(detail?: string | null) {
  const normalized = detail || ''
  if (normalized.includes('critical')) return '严重'
  if (normalized.includes('warning')) return '警告'
  if (normalized.includes('info')) return '提示'
  return '事件'
}

function alarmTitleBase(title: string) {
  return title
    .replace(/^告警已处理[:：]\s*/, '')
    .replace(/^报警已处理[:：]\s*/, '')
    .replace(/[:：].*$/, '')
    .trim()
}

function alarmGroupKey(item: DeviceStatusEvent) {
  return `${item.event_type}:${item.status}:${alarmTitleBase(item.title)}:${severityText(item.detail)}`
}

function durationText(start: string, end: string) {
  const startAt = Date.parse(start)
  const endAt = Date.parse(end)
  if (Number.isNaN(startAt) || Number.isNaN(endAt) || endAt <= startAt) return '不足 1 分钟'
  const minutes = Math.max(1, Math.round((endAt - startAt) / 60_000))
  if (minutes < 60) return `${minutes} 分钟`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest ? `${hours} 小时 ${rest} 分钟` : `${hours} 小时`
}

function compareTimestampDesc(a: string, b: string) {
  return Date.parse(b) - Date.parse(a)
}

export function buildCompensationEventTimeline(history: DeviceStatusEvent[]): CompensationEventItem[] {
  if (!history.length) {
    return [
      {
        time: '--:--',
        title: '当前时间范围内暂无真实运行事件',
        detail: '尚未采集到补偿器控制/告警事件，页面不再用示例事件替代真实记录。',
        tone: 'info' as CompensationTone,
        tag: '待采集',
        isMock: true,
      },
    ]
  }

  const groupedAlarms = new Map<string, DeviceStatusEvent[]>()
  const nonAlarmEvents: DeviceStatusEvent[] = []
  for (const item of history) {
    if (item.event_type === 'alarm') {
      const key = alarmGroupKey(item)
      groupedAlarms.set(key, [...(groupedAlarms.get(key) || []), item])
    } else {
      nonAlarmEvents.push(item)
    }
  }

  const alarmEvents = Array.from(groupedAlarms.values()).map((items) => {
    const ordered = [...items].sort((a, b) => compareTimestampDesc(a.timestamp, b.timestamp))
    const latest = ordered[0]
    const earliest = ordered[ordered.length - 1]
    const tone = historyTone(latest.status, latest.event_type)
    const countText = ordered.length > 1 ? `，累计 ${ordered.length} 次` : ''
    return {
      time: formatTimeOnly(latest.timestamp),
      title: alarmTitleBase(latest.title),
      detail: `级别：${severityText(latest.detail)} · 首次 ${formatTimeOnly(earliest.timestamp)} · 最近 ${formatTimeOnly(latest.timestamp)} · 持续 ${durationText(earliest.timestamp, latest.timestamp)}${countText}`,
      tone: tone === 'danger' ? 'warning' : tone,
      tag: latest.status === 'active' ? '持续中' : historyTag(latest.status, latest.event_type),
      sortAt: latest.timestamp,
    }
  })

  const otherEvents = nonAlarmEvents.map((item) => ({
    time: formatTimeOnly(item.timestamp),
    title: item.title,
    detail: item.detail || '无附加说明',
    tone: historyTone(item.status, item.event_type),
    tag: historyTag(item.status, item.event_type),
    sortAt: item.timestamp,
  }))

  return [...alarmEvents, ...otherEvents]
    .sort((a, b) => compareTimestampDesc(a.sortAt, b.sortAt))
    .slice(0, EVENT_TIMELINE_LIMIT)
    .map(({ sortAt: _sortAt, ...item }) => item)
}

export function useCompensationMonitor(input: UseCompensationMonitorInput) {
  const compensationSvgTelemetry = ref<CompensationSvgTelemetry | null>(null)
  const compensationSvgProfile = ref<CompensationSvgOperationsProfile | null>(null)
  const compensationSvgTelemetryHistory = ref<CompensationSvgTelemetry[]>([])
  const compensationCapacitorBankTelemetry = ref<CompensationCapacitorBankTelemetry | null>(null)
  const compensationCapacitorBankTelemetryHistory = ref<CompensationCapacitorBankTelemetry[]>([])
  const compensationCapacitorBankControlProfile = ref<CompensationCapacitorBankControlProfile | null>(null)

  let requestToken = 0

  const archive = computed(() => input.overview.value?.archive)
  const runtimeStatus = computed(() => input.overview.value?.runtime_status)
  const realtime = computed(() => input.overview.value?.realtime)
  const compensationMonitor = computed<CompensationMonitor | null>(
    () => input.overview.value?.compensation_monitor || null,
  )

  const compensationSubtype = computed(() =>
    resolveCompensationSubtype(archive.value?.device_type, archive.value?.device_subtype) || '',
  )
  const isCompensationDevice = computed(() => Boolean(compensationSubtype.value))
  const isSvgDevice = computed(() => compensationSubtype.value === 'svg')
  const compensationCategoryLabel = computed(() => getDeviceCategoryLabel('compensation'))
  const compensationSubtypeLabel = computed(() => getDeviceSubtypeLabel(compensationSubtype.value))
  const compensationUnitLabel = computed(() => (isSvgDevice.value ? '模块' : '回路'))

  const compensationTrendTabs = computed<CompensationTrendOption[]>(() => {
    if (compensationSubtype.value === 'capacitor_bank_controller') {
      return [
        { label: '补偿效果', value: 'effect' },
        { label: '三相有功', value: 'phase_active_power' },
        { label: '三相无功', value: 'phase_reactive_power' },
        { label: '三相PF', value: 'phase_power_factor' },
        { label: '三相电压', value: 'phase_voltage' },
        { label: '三相电流', value: 'phase_current' },
        { label: '谐波趋势', value: 'harmonic' },
        { label: '投切回放', value: 'switching' },
        { label: '温度/健康度', value: 'health' },
      ]
    }
    return [
      { label: '补偿效果', value: 'effect' },
      { label: '电压', value: 'voltage' },
      { label: '电流', value: 'current' },
      { label: '温度/健康度', value: 'health' },
    ]
  })

  const capacitorBankCircuitSummary = computed(() => {
    if (compensationSubtype.value !== 'capacitor_bank_controller') return null
    const summary = compensationMonitor.value?.circuit_summary
    if (!summary) return null
    return {
      runningCount: Number(summary.running_count || 0),
      totalCount: Number(summary.total_count || 24),
      hasRealtimeState: Boolean(summary.has_realtime_state),
      source: describeCompensationSource('circuit_summary', summary.source, 'capacitor_bank_controller'),
      state: summary.state,
    }
  })

  const fallbackCompensation = computed(() =>
    buildCompensationSemanticView({
      subtype: isSvgDevice.value ? 'svg' : compensationSubtype.value === 'capacitor_bank_controller' ? 'capacitor_bank_controller' : 'unknown',
      monitor: compensationMonitor.value,
      targetPowerFactor: normalizePowerFactorTarget(compensationCapacitorBankControlProfile.value?.switch_on_power_factor),
      svgProfileModuleCount: compensationSvgProfile.value?.module_count,
      svgTelemetryAutoMode: compensationSvgTelemetry.value?.auto_mode,
      svgCabinetTemperature: compensationSvgTelemetry.value?.cabinet_temp,
      capacitorBankTemperature: compensationCapacitorBankTelemetry.value?.temperature,
      realtimeTemperature: realtime.value?.temperature,
      canControlDevices: input.canControlDevices.value,
      isOnline: runtimeStatus.value?.is_online,
    }),
  )

  const isRealtimeFresh = computed(() => isTimestampFresh(realtime.value?.timestamp))

  const compensationStatusText = computed(() => {
    const pf = realtime.value?.power_factor
    if (!runtimeStatus.value?.is_online || !isRealtimeFresh.value) return '离线'
    if (pf === null || pf === undefined) return '待判断'
    if (pf < 0.9) return '欠补偿'
    if (pf > 0.99) return '过补偿'
    return '正常补偿'
  })

  const compensationStatusTone = computed<CompensationTone>(() => {
    if (!runtimeStatus.value?.is_online || !isRealtimeFresh.value) return 'neutral'
    if (compensationStatusText.value === '欠补偿') return 'warning'
    if (compensationStatusText.value === '过补偿') return 'danger'
    if (compensationStatusText.value === '正常补偿') return 'success'
    return 'info'
  })

  const compensationHeaderModel = computed<CompensationHeaderModel>(() =>
    buildCompensationHeaderView({
      title: archive.value?.name || '补偿器1',
      serial: archive.value?.sn || 'SN2323',
      location: archive.value?.location || '未配置安装位置',
      deviceStatus: runtimeStatus.value?.label || statusText(runtimeStatus.value?.is_online, '运行状态未知'),
      isOnline: runtimeStatus.value?.is_online,
      controlMode: fallbackCompensation.value.controlMode,
      controlModeState: fallbackCompensation.value.controlModeState,
      compensationStatusText: compensationStatusText.value,
      compensationStatusTone: compensationStatusTone.value,
    }),
  )

  const hasReactivePowerField = computed(() =>
    Object.prototype.hasOwnProperty.call(realtime.value || {}, 'reactive_power'),
  )

  const compensationReactiveHint = computed(() => {
    if (!hasReactivePowerField.value) return '当前接口未返回无功功率字段'
    if (realtime.value?.reactive_power === null) return '当前无实时无功功率数据'
    return '实时采集值'
  })

  const gridFrequencyTelemetryValue = computed<number | null | undefined>(() =>
    isSvgDevice.value
      ? compensationSvgTelemetry.value?.frequency
      : compensationCapacitorBankTelemetry.value?.frequency,
  )

  const compensationOverviewView = computed(() => {
    const temperature = fallbackCompensation.value.cabinetTemperature
    return buildCompensationOverviewMetrics({
      isSvgDevice: isSvgDevice.value,
      reactivePowerValue: displayValueWithState(realtime.value?.reactive_power, '暂无数据'),
      reactivePowerHint: compensationReactiveHint.value,
      reactivePowerMissing: realtime.value?.reactive_power === null || realtime.value?.reactive_power === undefined,
      powerFactorValue: displayValueWithState(realtime.value?.power_factor, '暂无数据', 2),
      powerFactorHint: realtime.value?.power_factor == null
        ? '实时值缺失'
        : fallbackCompensation.value.targetPowerFactor == null
          ? '目标 PF 暂无参数'
          : `目标 PF ${fallbackCompensation.value.targetPowerFactor.toFixed(2)}`,
      powerFactorMissing: realtime.value?.power_factor == null,
      voltageValue: displayValueWithState(realtime.value?.voltage, '通讯中断'),
      voltageMissing: realtime.value?.voltage == null,
      currentValue: displayValueWithState(realtime.value?.current, '通讯中断'),
      currentMissing: realtime.value?.current == null,
      activePowerValue: displayValueWithState(realtime.value?.flow_rate, '暂无数据'),
      activePowerMissing: realtime.value?.flow_rate == null,
      capacityUsageValue: fallbackCompensation.value.compensationCapacityUsage,
      capacityUsageSource: fallbackCompensation.value.capacityUsageSource,
      capacityUsageState: fallbackCompensation.value.capacityUsageState,
      controlMode: fallbackCompensation.value.controlMode,
      controlModeSource: fallbackCompensation.value.controlModeSource,
      controlModeState: fallbackCompensation.value.controlModeState,
      cabinetTemperatureValue: displayValueWithState(temperature, '暂无数据'),
      cabinetTemperature: temperature,
      cabinetTemperatureSource: fallbackCompensation.value.cabinetTemperatureSource,
      cabinetTemperatureHealthText: fallbackCompensation.value.cabinetTemperatureHealthText,
      cabinetTemperatureHealthHint: fallbackCompensation.value.cabinetTemperatureHealthHint,
      cabinetTemperatureHealthTone: fallbackCompensation.value.cabinetTemperatureHealthTone,
      gridFrequencyValue: displayValueWithState(gridFrequencyTelemetryValue.value, '暂无数据', 2),
      gridFrequencyMissing: gridFrequencyTelemetryValue.value == null,
    })
  })

  const compensationCoreMetric = computed<CompensationMetric>(() => compensationOverviewView.value.coreMetric)
  const compensationPfMetric = computed<CompensationMetric>(() => ({
    ...compensationOverviewView.value.pfMetric,
    tone: compensationStatusTone.value,
  }))
  const compensationMetrics = computed<CompensationMetric[]>(() => compensationOverviewView.value.metrics)

  const moduleStatusModel = computed<ModuleStatusModel>(() =>
    buildCompensationModuleStatusView({
      subtype: isSvgDevice.value ? 'svg' : compensationSubtype.value === 'capacitor_bank_controller' ? 'capacitor_bank_controller' : 'unknown',
      isSvgDevice: isSvgDevice.value,
      unitLabel: compensationUnitLabel.value,
      fallbackRunningModuleCount: fallbackCompensation.value.runningModuleCount,
      fallbackTotalModuleCount: fallbackCompensation.value.totalModuleCount,
      capacitorBankCircuitSummary: capacitorBankCircuitSummary.value,
      svgTelemetry: compensationSvgTelemetry.value,
    }),
  )

  const compensationExtendedHint = computed(() =>
    buildCompensationExtendedHint({
      capacityUsageSource: fallbackCompensation.value.capacityUsageSource,
      capacityUsageState: fallbackCompensation.value.capacityUsageState,
      controlModeSource: fallbackCompensation.value.controlModeSource,
      controlModeState: fallbackCompensation.value.controlModeState,
      cabinetTemperature: fallbackCompensation.value.cabinetTemperature,
      isSvgDevice: isSvgDevice.value,
    }),
  )

  const compensationTrendModel = computed<CompensationTrendModel>(() =>
    buildCompensationTrendView({
      subtype: isSvgDevice.value ? 'svg' : compensationSubtype.value === 'capacitor_bank_controller' ? 'capacitor_bank_controller' : 'unknown',
      isSvgDevice: isSvgDevice.value,
      activeTab: input.compensationTrendTab.value,
      timeRange: input.timeRange.value || defaultTimeRange(),
      trendPoints: input.trend.value?.points || [],
      realtime: realtime.value,
      archive: archive.value,
      fallbackCompensation: fallbackCompensation.value,
      svgTelemetryHistory: compensationSvgTelemetryHistory.value,
      capacitorBankTelemetryHistory: compensationCapacitorBankTelemetryHistory.value,
      svgTelemetry: compensationSvgTelemetry.value,
      capacitorBankTelemetry: compensationCapacitorBankTelemetry.value,
    }),
  )

  const compensationEvents = computed<CompensationEventItem[]>(() => {
    return buildCompensationEventTimeline(input.statusHistory.value)
  })

  const compensationStatusItems = computed<CompensationStatusItem[]>(() =>
    buildCompensationStatusItems({
      isSvgDevice: isSvgDevice.value,
      subtypeLabel: compensationSubtypeLabel.value || '未定义',
      deviceStatus: runtimeStatus.value?.label || '状态未知',
      isActive: runtimeStatus.value?.is_active,
      isOnline: runtimeStatus.value?.is_online,
      ingestionStatus: formatIngestionStatus(runtimeStatus.value?.ingestion_status),
      ingestionTone: ingestionTone(runtimeStatus.value?.ingestion_status),
      unresolvedAlarmCount: runtimeStatus.value?.unresolved_alarm_count ?? 0,
      controlMode: fallbackCompensation.value.controlMode,
      controlModeSource: fallbackCompensation.value.controlModeSource,
      controlSource: fallbackCompensation.value.controlSource,
      capacityUsageSource: fallbackCompensation.value.capacityUsageSource,
      capacityUsageState: fallbackCompensation.value.capacityUsageState,
      cabinetTemperature: fallbackCompensation.value.cabinetTemperature,
      cabinetTemperatureSource: fallbackCompensation.value.cabinetTemperatureSource,
      latestSampleText: formatDateTime(
        isSvgDevice.value
          ? compensationSvgTelemetry.value?.timestamp
          : compensationCapacitorBankTelemetry.value?.timestamp,
      ),
      canControlDevices: input.canControlDevices.value,
      switchPermission: fallbackCompensation.value.switchPermission,
      profileSourceStatus: compensationMonitor.value?.profile_status?.source_status,
      runningModuleCount: !isSvgDevice.value ? moduleStatusModel.value.runningModuleCount : undefined,
      totalModuleCount: !isSvgDevice.value ? moduleStatusModel.value.totalModuleCount : undefined,
      svgTelemetry: compensationSvgTelemetry.value,
      capacitorBankTelemetry: compensationCapacitorBankTelemetry.value,
    }),
  )

  const compensationProfileItems = computed<CompensationProfileItem[]>(() =>
    buildCompensationProfileItems({
      archive: archive.value,
      categoryLabel: compensationCategoryLabel.value || '无功功率补偿设备',
      subtypeLabel: compensationSubtypeLabel.value || '未定义',
      svgProfile: compensationSvgProfile.value,
    }),
  )

  const capacitorBankControlSummaryView = computed(() =>
    buildCapacitorBankControlSummaryView({
      profile: compensationCapacitorBankControlProfile.value,
    }),
  )

  async function loadSVGTelemetry() {
    try {
      compensationSvgTelemetry.value = await getCompensationSvgTelemetryLatest(input.deviceId.value)
    } catch {
      compensationSvgTelemetry.value = null
    }
    try {
      const [start, end] = input.timeRange.value || defaultTimeRange()
      const maxPoints = getTrendMaxPoints(start, end, input.compensationTrendTab.value)
      const records = await getCompensationSvgTelemetryHistory(input.deviceId.value, {
        start: toApiDate(start),
        end: toApiDate(end),
        limit: calculateHistoryLimit(start, end),
      })
      const sortedRecords = [...records].sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      )
      compensationSvgTelemetryHistory.value = sampleTimeSeriesByTimestamp(sortedRecords, maxPoints)
    } catch {
      compensationSvgTelemetryHistory.value = []
    }
  }

  async function loadSVGProfile() {
    try {
      compensationSvgProfile.value = await getCompensationSvgOperationsProfile(input.deviceId.value)
    } catch {
      compensationSvgProfile.value = null
    }
  }

  async function loadCapBankTelemetry() {
    try {
      compensationCapacitorBankTelemetry.value = await getCompensationCapacitorBankTelemetryLatest(input.deviceId.value)
    } catch {
      compensationCapacitorBankTelemetry.value = null
    }
    try {
      const [start, end] = input.timeRange.value || defaultTimeRange()
      const maxPoints = getTrendMaxPoints(start, end, input.compensationTrendTab.value)
      const records = await getCompensationCapacitorBankTelemetryHistory(input.deviceId.value, {
        start: toApiDate(start),
        end: toApiDate(end),
        limit: calculateHistoryLimit(start, end),
      })
      const sortedRecords = [...records].sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      )
      compensationCapacitorBankTelemetryHistory.value = sampleTimeSeriesByTimestamp(sortedRecords, maxPoints)
    } catch {
      compensationCapacitorBankTelemetryHistory.value = []
    }
  }

  async function loadCapBankControlProfile() {
    try {
      compensationCapacitorBankControlProfile.value = await getCompensationCapacitorBankControlProfile(input.deviceId.value)
    } catch {
      compensationCapacitorBankControlProfile.value = null
    }
  }

  async function refreshCompensationData() {
    const token = ++requestToken
    try {
      if (isSvgDevice.value) {
        await loadSVGTelemetry()
        if (token !== requestToken) return
      }
      if (compensationSubtype.value === 'capacitor_bank_controller') {
        await Promise.all([loadCapBankTelemetry(), loadCapBankControlProfile()])
        if (token !== requestToken) return
      }
    } catch {
      // axios 统一处理
    }
  }

  onBeforeUnmount(() => {
    requestToken++
  })

  return {
    compensationSvgTelemetry,
    compensationSvgProfile,
    compensationSvgTelemetryHistory,
    compensationCapacitorBankTelemetry,
    compensationCapacitorBankTelemetryHistory,
    compensationCapacitorBankControlProfile,
    compensationSubtype,
    isCompensationDevice,
    isSvgDevice,
    compensationCategoryLabel,
    compensationSubtypeLabel,
    compensationUnitLabel,
    compensationTrendTabs,
    capacitorBankCircuitSummary,
    fallbackCompensation,
    compensationStatusText,
    compensationStatusTone,
    compensationHeaderModel,
    hasReactivePowerField,
    compensationReactiveHint,
    compensationOverviewView,
    compensationCoreMetric,
    compensationPfMetric,
    compensationMetrics,
    moduleStatusModel,
    compensationExtendedHint,
    compensationTrendModel,
    compensationEvents,
    compensationStatusItems,
    compensationProfileItems,
    capacitorBankControlSummaryView,
    loadSVGTelemetry,
    loadSVGProfile,
    loadCapBankTelemetry,
    loadCapBankControlProfile,
    refreshCompensationData,
  }
}
