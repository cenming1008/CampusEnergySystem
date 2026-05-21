import type {
  CompensationMonitor,
  DeviceArchive,
  DeviceRealtime,
  TrendPoint,
} from '@/api/deviceMonitor'
import type {
  CompensationCapacitorBankControlProfile,
  CompensationCapacitorBankTelemetry,
  CompensationSvgOperationsProfile,
  CompensationSvgTelemetry,
} from '@/api/compensation'
import {
  capacitorBankControlParameterMeta,
  formatCapacitorBankControlValue,
} from '@/features/device-control/capacitorBankControlProfile'
import type {
  CompensationHeaderModel,
  CompensationTag,
  CompensationMetric,
  CompensationProfileItem,
  CompensationStatusItem,
  CompensationTone,
  CompensationTrendModel,
  CompensationTrendTab,
  HarmonicSpectrumKind,
  HarmonicSpectrumModel,
  HarmonicSpectrumPhase,
  ModuleStateTone,
  ModuleStatusModel,
} from './types'

export type CompensationSemanticSourceKind =
  | 'control_mode'
  | 'capacity_utilization'
  | 'circuit_summary'
  | 'temperature'

export type CompensationSemanticSubtype = 'svg' | 'capacitor_bank_controller' | 'unknown'

export interface CompensationSemanticViewInput {
  subtype: CompensationSemanticSubtype
  monitor: CompensationMonitor | null | undefined
  targetPowerFactor?: number | null
  svgProfileModuleCount?: number | null
  svgTelemetryAutoMode?: boolean | null
  svgCabinetTemperature?: number | null
  capacitorBankTemperature?: number | null
  realtimeTemperature?: number | null
  canControlDevices: boolean
  isOnline?: boolean
}

export interface CompensationSemanticView {
  controlMode: string
  controlModeSource: string
  controlModeState: 'live' | 'mock' | 'missing'
  runningModuleCount: number
  totalModuleCount: number
  compensationCapacityUsage: number
  capacityUsageSource: string
  capacityUsageState: 'live' | 'mock' | 'missing'
  controlSource: string
  switchPermission: boolean
  cabinetTemperature: number | null
  cabinetTemperatureSource: string
  cabinetTemperatureHealthText: string
  cabinetTemperatureHealthHint: string
  cabinetTemperatureHealthTone: CompensationTone
  targetPowerFactor: number | null
  dailySwitchCount: number
  hourlySwitchCount: number
  thd: number
  runningHours: number
}

export interface CompensationBaseStatusItemsInput {
  isSvgDevice: boolean
  subtypeLabel: string
  deviceStatus: string
  isActive?: boolean
  isOnline?: boolean
  ingestionStatus: string
  ingestionTone?: CompensationTone
  controlMode: string
  controlModeSource: string
  controlSource: string
  capacityUsageSource: string
  capacityUsageState: 'live' | 'mock' | 'missing'
  cabinetTemperature: number | null
  cabinetTemperatureSource: string
  latestSampleText: string
  canControlDevices: boolean
  switchPermission: boolean
  profileSourceStatus?: string | null
  runningModuleCount?: number
  totalModuleCount?: number
}

export interface CompensationHeaderViewInput {
  title: string
  serial: string
  location: string
  deviceStatus: string
  isOnline?: boolean
  controlMode: string
  controlModeState: 'live' | 'mock' | 'missing'
  compensationStatusText: string
  compensationStatusTone: CompensationTone
}

export interface CompensationOverviewMetricsInput {
  isSvgDevice: boolean
  reactivePowerValue: string
  reactivePowerHint: string
  reactivePowerMissing: boolean
  powerFactorValue: string
  powerFactorHint: string
  powerFactorMissing: boolean
  voltageValue: string
  voltageMissing: boolean
  currentValue: string
  currentMissing: boolean
  activePowerValue: string
  activePowerMissing: boolean
  capacityUsageValue: number
  capacityUsageSource: string
  capacityUsageState: 'live' | 'mock' | 'missing'
  controlMode: string
  controlModeSource: string
  controlModeState: 'live' | 'mock' | 'missing'
  cabinetTemperatureValue: string
  cabinetTemperature: number | null
  cabinetTemperatureSource: string
  cabinetTemperatureHealthText?: string | null
  cabinetTemperatureHealthHint?: string | null
  cabinetTemperatureHealthTone?: CompensationTone
  gridFrequencyValue: string
  gridFrequencyMissing: boolean
}

export interface CompensationModuleStatusInput {
  subtype: CompensationSemanticSubtype
  isSvgDevice: boolean
  unitLabel: string
  fallbackRunningModuleCount: number
  fallbackTotalModuleCount: number
  capacitorBankCircuitSummary?: {
    runningCount: number
    totalCount: number
    hasRealtimeState: boolean
  } | null
  svgTelemetry?: Pick<
    CompensationSvgTelemetry,
    'overtemp_fault' | 'overcurrent_fault' | 'module_fault'
  > | null
}

export interface CompensationExtendedHintInput {
  isSvgDevice: boolean
  capacityUsageSource: string
  capacityUsageState: 'live' | 'mock' | 'missing'
  controlModeSource: string
  controlModeState: 'live' | 'mock' | 'missing'
  cabinetTemperature: number | null
}

export interface CompensationStatusItemsInput extends CompensationBaseStatusItemsInput {
  isSvgDevice: boolean
  unresolvedAlarmCount: number
  svgTelemetry?: Partial<CompensationSvgTelemetry> | null
  capacitorBankTelemetry?: Partial<CompensationCapacitorBankTelemetry> | null
}

export interface CompensationProfileItemsInput {
  archive: Partial<DeviceArchive> | null | undefined
  categoryLabel: string
  subtypeLabel: string
  svgProfile?: Partial<CompensationSvgOperationsProfile> | null
}

export interface CapacitorBankControlSummaryViewInput {
  profile: CompensationCapacitorBankControlProfile | null | undefined
}

export interface CapacitorBankControlSummaryView {
  summaryItems: CompensationProfileItem[]
  capacityExpansionItems: CompensationProfileItem[]
  hasSummaryData: boolean
}

export interface CompensationTrendViewInput {
  subtype: CompensationSemanticSubtype
  isSvgDevice: boolean
  activeTab: CompensationTrendTab
  timeRange: [Date, Date]
  trendPoints: TrendPoint[]
  realtime: Partial<DeviceRealtime> | null | undefined
  archive: Partial<DeviceArchive> | null | undefined
  fallbackCompensation: Pick<CompensationSemanticView, 'targetPowerFactor'>
  svgTelemetryHistory: CompensationSvgTelemetry[]
  capacitorBankTelemetryHistory: CompensationCapacitorBankTelemetry[]
  svgTelemetry: CompensationSvgTelemetry | null | undefined
  capacitorBankTelemetry: CompensationCapacitorBankTelemetry | null | undefined
}

export interface HarmonicSpectrumViewInput {
  activeKind: HarmonicSpectrumKind
  activePhase: HarmonicSpectrumPhase
  telemetry: CompensationCapacitorBankTelemetry | null | undefined
  controlProfile: CompensationCapacitorBankControlProfile | null | undefined
}

function normalizeState(value?: string | null, fallback: CompensationSemanticView['controlModeState'] = 'missing') {
  if (value === 'live' || value === 'mock' || value === 'missing') return value
  return fallback
}

function normalizeSource(source?: string | null) {
  return `${source || ''}`.trim().toLowerCase()
}

function describeTemperatureHealthHint(source?: string | null, value?: string | null) {
  const normalized = normalizeSource(source)
  if (normalized === 'telemetry' && value === '温度告警') return '实时温度告警位'
  if (normalized === 'telemetry') return '实时温度告警位正常'
  if (normalized === 'profile') return '基于参数上限回读判定'
  if (normalized === 'missing') return '当前缺少温度健康度判定依据'
  return '当前缺少温度健康度判定依据'
}

function resolveTemperatureHealthTone(value?: string | null): CompensationTone {
  if (value === '温度告警' || value === '超过上限') return 'danger'
  if (value === '接近上限') return 'warning'
  if (value === '正常') return 'success'
  return 'neutral'
}

function displayValue(value: number | string | null | undefined, emptyText: string, digits: number = 1) {
  if (value === null || value === undefined || value === '') return emptyText
  if (typeof value === 'number') return Number(value).toFixed(digits)
  return String(value)
}

function normalizePowerFactorTarget(value?: number | null) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null
  const numeric = Number(value)
  return numeric > 2 ? numeric / 100 : numeric
}

function booleanStatus(
  value: boolean | null | undefined,
  trueLabel: string,
  falseLabel: string,
  emptyLabel: string = '未知',
) {
  if (value === true) return trueLabel
  if (value === false) return falseLabel
  return emptyLabel
}

function maxTemperature(...values: Array<number | null | undefined>) {
  const nums = values.filter((value): value is number => value !== null && value !== undefined)
  if (!nums.length) return null
  return Math.max(...nums)
}

function statusTemperatureTone(...values: Array<number | null | undefined>): CompensationTone {
  const maxTemp = maxTemperature(...values)
  if (maxTemp === null) return 'neutral'
  if (maxTemp >= 75) return 'danger'
  if (maxTemp >= 60) return 'warning'
  return 'success'
}

function formatCapacitySlotList(values?: number[] | null) {
  if (!values?.length) return '未配置'
  return values.map((value) => `${Number(value).toFixed(1)} kvar`).join(' / ')
}

function displayValueWithUnit(value: number | string | null | undefined, emptyText: string, unit = '', digits = 1) {
  const displayed = displayValue(value, emptyText, digits)
  return unit ? `${displayed} ${unit}` : displayed
}

const harmonicPhaseLabels: Record<HarmonicSpectrumPhase, string> = {
  a: 'A相',
  b: 'B相',
  c: 'C相',
}

const harmonicKindLabels: Record<HarmonicSpectrumKind, string> = {
  voltage: '电压谐波',
  current: '电流谐波',
}

function harmonicUnit(kind: HarmonicSpectrumKind) {
  return kind === 'voltage' ? '%' : 'A'
}

export function getHarmonicSpectrumYAxisMax(kind: HarmonicSpectrumKind) {
  return kind === 'voltage' ? 5 : 50
}

function harmonicThreshold(
  kind: HarmonicSpectrumKind,
  profile: CompensationCapacitorBankControlProfile | null | undefined,
) {
  const raw = kind === 'voltage'
    ? profile?.voltage_harmonic_threshold
    : profile?.current_harmonic_threshold
  if (raw === null || raw === undefined || !Number.isFinite(Number(raw))) return null
  const value = Number(raw)
  if (kind === 'current' && value <= 29) return null
  if (kind === 'voltage' && value <= 2.9) return null
  return value
}

function harmonicSpectrumField(kind: HarmonicSpectrumKind, phase: HarmonicSpectrumPhase) {
  return `${kind}_harmonics_${phase}` as keyof CompensationCapacitorBankTelemetry
}

export function buildHarmonicSpectrumView(input: HarmonicSpectrumViewInput): HarmonicSpectrumModel {
  const field = harmonicSpectrumField(input.activeKind, input.activePhase)
  const rawSpectrum = input.telemetry?.[field]
  const threshold = harmonicThreshold(input.activeKind, input.controlProfile)
  const unit = harmonicUnit(input.activeKind)
  const realBars = Array.isArray(rawSpectrum)
    ? rawSpectrum
        .map((point) => ({
          order: Number(point?.order),
          value: Number(point?.value),
        }))
        .filter((point) => Number.isInteger(point.order) && point.order >= 2 && point.order <= 31 && Number.isFinite(point.value))
        .sort((a, b) => a.order - b.order)
        .map((point) => ({
          ...point,
          exceeded: threshold !== null && point.value >= threshold,
        }))
    : []
  const isEmpty = realBars.length === 0
  const bars: HarmonicSpectrumModel['bars'] = isEmpty
    ? Array.from({ length: 30 }, (_, i) => ({
        order: i + 2,
        value: 0,
        exceeded: false,
        placeholder: true,
      }))
    : realBars
  const peak = realBars.reduce<typeof realBars[number] | null>(
    (current, point) => (current === null || point.value > current.value ? point : current),
    null,
  )
  const exceeded = realBars.some((point) => point.exceeded)

  return {
    bars,
    unit,
    threshold,
    summary: {
      phaseLabel: harmonicPhaseLabels[input.activePhase],
      kindLabel: harmonicKindLabels[input.activeKind],
      unit,
      peakOrder: peak?.order ?? null,
      peakValue: peak?.value ?? null,
      threshold,
      statusText: isEmpty ? '暂无数据' : (exceeded ? '超限' : '正常'),
      statusTone: isEmpty ? 'neutral' : (exceeded ? 'danger' : 'success'),
      timestamp: input.telemetry?.timestamp ?? null,
    },
    empty: isEmpty,
    emptyText: '当前网关未上报 2~31 次谐波谱线',
  }
}

function toShortTimeInRange(timestamp: string | null | undefined, range: [Date, Date]) {
  if (!timestamp) return '--'
  const date = new Date(timestamp)
  const [start, end] = range
  const crossesDay =
    (start.getFullYear() !== end.getFullYear()
      || start.getMonth() !== end.getMonth()
      || start.getDate() !== end.getDate())
    && end.getTime() - start.getTime() > 60 * 60 * 1000

  return crossesDay
    ? `${`${date.getMonth() + 1}`.padStart(2, '0')}/${`${date.getDate()}`.padStart(2, '0')} ${`${date.getHours()}`.padStart(2, '0')}:${`${date.getMinutes()}`.padStart(2, '0')}`
    : `${`${date.getHours()}`.padStart(2, '0')}:${`${date.getMinutes()}`.padStart(2, '0')}`
}

function buildTrendLabels(points: TrendPoint[], range: [Date, Date]) {
  if (points.length) {
    return points.map((point) => toShortTimeInRange(point.timestamp, range))
  }

  const [start, end] = range
  const step = Math.max(1, Math.floor((end.getTime() - start.getTime()) / (8 * 60 * 1000)))
  return Array.from({ length: 8 }).map((_, index) =>
    new Date(start.getTime() + index * step * 60 * 1000).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }),
  )
}

function buildTrendSeriesFromPoints(points: TrendPoint[], metric: 'voltage' | 'current') {
  const values = points
    .map((point) => (metric === 'voltage' ? point.voltage : point.current))
    .filter((value): value is number => value !== null && value !== undefined)

  return {
    values: points.map((point) => (metric === 'voltage' ? point.voltage : point.current) ?? null),
    peak: values.length ? Math.max(...values) : null,
    valley: values.length ? Math.min(...values) : null,
    isMock: false,
  }
}

function trendModelFromSingleSeries(options: {
  labels: string[]
  name: string
  unit: string
  color: string
  values: Array<number | null> | Array<[string, number | null]>
  summaryItems: Array<{ label: string; value: string }>
  isMock: boolean
  hint: string
  emptyText: string
  xAxisType?: 'category' | 'time'
  xAxisMin?: string
  xAxisMax?: string
}): CompensationTrendModel {
  const hasValue = options.values.some((value) =>
    Array.isArray(value) ? value[1] !== null && value[1] !== undefined : value !== null && value !== undefined,
  )
  return {
    labels: options.labels,
    legend: [options.name],
    axes: [{ name: options.unit }],
    series: [{ name: options.name, data: options.values, color: options.color, area: true }],
    xAxisType: options.xAxisType,
    xAxisMin: options.xAxisMin,
    xAxisMax: options.xAxisMax,
    summary: options.summaryItems,
    empty: !hasValue,
    emptyText: options.emptyText,
    hint: options.hint,
    isMock: options.isMock,
  }
}

function hasCapBankHistoryValue(history: CompensationCapacitorBankTelemetry[], key: keyof CompensationCapacitorBankTelemetry) {
  return history.some((point) => point[key] != null)
}

function buildTimedCapBankSeries(
  history: CompensationCapacitorBankTelemetry[],
  key: keyof CompensationCapacitorBankTelemetry,
): Array<[string, number | null]> {
  return history.map((point) => {
    const value = point[key]
    return [point.timestamp, typeof value === 'number' ? value : null]
  })
}

function buildTimedCapBankAggregateSeries(
  history: CompensationCapacitorBankTelemetry[],
  keys: Array<keyof CompensationCapacitorBankTelemetry>,
  mode: 'sum' | 'average',
): Array<[string, number | null]> {
  return history.map((point) => {
    const values = keys
      .map((key) => point[key])
      .filter((value): value is number => typeof value === 'number')

    if (!values.length) return [point.timestamp, null]
    const total = values.reduce((sum, value) => sum + value, 0)
    return [point.timestamp, mode === 'average' ? total / values.length : total]
  })
}

function decodeSwitchingCount(value: number | null | undefined) {
  if (typeof value !== 'number') return null
  let count = 0
  for (let i = 0; i < 8; i += 1) {
    if (value & (1 << i)) count += 1
  }
  return count
}

function buildTimedCapBankSwitchingSeries(
  history: CompensationCapacitorBankTelemetry[],
  key: keyof CompensationCapacitorBankTelemetry | Array<keyof CompensationCapacitorBankTelemetry>,
): Array<[string, number | null]> {
  const keys = Array.isArray(key) ? key : [key]
  return history.map((point) => {
    let total: number | null = null
    for (const k of keys) {
      const rawValue = point[k]
      if (typeof rawValue === 'number') {
        total = (total ?? 0) + (decodeSwitchingCount(rawValue) ?? 0)
      }
    }
    return [point.timestamp, total]
  })
}

export function describeCompensationSource(
  kind: CompensationSemanticSourceKind,
  source: string | null | undefined,
  subtype: CompensationSemanticSubtype,
) {
  const normalized = normalizeSource(source)
  if (kind === 'control_mode') {
    if (normalized === 'telemetry') return 'Win 端控制模式'
    if (normalized === 'profile') return '参数回读'
    if (normalized === 'control_log') return '控制日志回退'
    return '估算/占位'
  }
  if (kind === 'capacity_utilization') {
    if (normalized === 'telemetry') {
      return subtype === 'svg' ? '遥测回读' : '按投切回路回读换算'
    }
    if (normalized === 'profile') return '按参数快照回读换算'
    if (normalized === 'estimated') return '按额定容量估算'
    return '演示占位'
  }
  if (kind === 'circuit_summary') {
    if (normalized === 'telemetry') return '投切回路回读'
    if (normalized === 'profile') return '参数快照回读'
    if (normalized === 'configured_fallback') return '当前无回路回读，按配置总回路展示'
    if (normalized === 'estimated') return '按额定容量估算'
    return '估算/占位'
  }
  if (normalized === 'telemetry' || normalized === 'realtime') return '实时采集'
  if (normalized === 'missing') return '当前缺测'
  return '当前缺测'
}

export function buildCompensationSemanticView(input: CompensationSemanticViewInput): CompensationSemanticView {
  const subtype = input.subtype
  const controlMode = input.monitor?.control_mode
  const circuitSummary = input.monitor?.circuit_summary
  const usageMetric = input.monitor?.key_metrics?.capacity_utilization
  const cabinetTemperatureMetric = input.monitor?.key_metrics?.cabinet_temperature
  const rawTotal = typeof circuitSummary?.total_count === 'number' ? circuitSummary.total_count : 0
  const totalModuleCount = Math.max(
    1,
    rawTotal
      || (subtype === 'svg' ? Number(input.svgProfileModuleCount || 0) : 24)
      || 8,
  )
  const usage = typeof usageMetric?.value === 'number' ? usageMetric.value : 0
  const rawRunning = typeof circuitSummary?.running_count === 'number' ? circuitSummary.running_count : null
  const runningModuleCount = Math.max(
    0,
    Math.min(
      totalModuleCount,
      Number(rawRunning ?? Math.round((usage / 100) * totalModuleCount)),
    ),
  )

  const fallbackControlMode = subtype === 'svg'
    ? (input.svgTelemetryAutoMode === true ? '自动' : input.svgTelemetryAutoMode === false ? '手动' : '待确认')
    : '待确认'
  const normalizedControlMode = controlMode?.value || fallbackControlMode
  const controlModeSource = describeCompensationSource('control_mode', controlMode?.source, subtype)
  const controlModeState = controlMode?.value
    ? normalizeState(controlMode?.state, 'mock')
    : normalizeState(input.svgTelemetryAutoMode != null ? 'live' : 'mock', 'mock')

  const cabinetTemperature = typeof cabinetTemperatureMetric?.value === 'number'
    ? cabinetTemperatureMetric.value
    : subtype === 'svg'
      ? (input.svgCabinetTemperature ?? input.realtimeTemperature ?? null)
      : (input.capacitorBankTemperature ?? input.realtimeTemperature ?? null)
  const temperatureHealthMetric = input.monitor?.key_metrics?.temperature_health
  const cabinetTemperatureHealthText = typeof temperatureHealthMetric?.value === 'string'
    ? temperatureHealthMetric.value
    : '待判断'
  const cabinetTemperatureHealthHint = describeTemperatureHealthHint(
    temperatureHealthMetric?.source,
    cabinetTemperatureHealthText,
  )
  const cabinetTemperatureHealthTone = resolveTemperatureHealthTone(cabinetTemperatureHealthText)

  return {
    controlMode: normalizedControlMode,
    controlModeSource,
    controlModeState,
    runningModuleCount,
    totalModuleCount,
    compensationCapacityUsage: usage,
    capacityUsageSource: describeCompensationSource('capacity_utilization', usageMetric?.source, subtype),
    capacityUsageState: normalizeState(usageMetric?.state),
    controlSource: normalizedControlMode === '自动' ? 'EMS 自动策略' : normalizedControlMode === '手动' ? '现场手动' : '待确认',
    switchPermission: input.canControlDevices && input.isOnline !== false,
    cabinetTemperature,
    cabinetTemperatureSource: describeCompensationSource('temperature', cabinetTemperatureMetric?.source, subtype),
    cabinetTemperatureHealthText,
    cabinetTemperatureHealthHint,
    cabinetTemperatureHealthTone,
    targetPowerFactor: normalizePowerFactorTarget(input.targetPowerFactor),
    dailySwitchCount: 12,
    hourlySwitchCount: 2,
    thd: 3.2,
    runningHours: 3280,
  }
}

function profileStatusValue(sourceStatus?: string | null) {
  if (sourceStatus === 'fresh') return '最新参数'
  if (sourceStatus === 'stale') return '参数可能过期'
  if (sourceStatus === 'empty') return '暂无参数'
  return '状态未知'
}

function profileStatusTone(sourceStatus?: string | null): CompensationTone {
  if (sourceStatus === 'fresh') return 'success'
  if (sourceStatus === 'stale') return 'warning'
  return 'neutral'
}

function platformEnableStatusText(isActive?: boolean) {
  if (isActive === true) return '已启用'
  if (isActive === false) return '已停用'
  return '状态未知'
}

function runtimeStatusTone(deviceStatus?: string | null, isOnline?: boolean): CompensationTone {
  const normalized = `${deviceStatus || ''}`.trim()
  if (!normalized) return isOnline ? 'info' : 'neutral'
  if (normalized.includes('告警')) return 'danger'
  if (normalized.includes('离线')) return 'warning'
  if (normalized.includes('停机') || normalized.includes('停止')) return 'warning'
  if (normalized.includes('运行')) return 'success'
  return isOnline ? 'info' : 'neutral'
}

function shouldShowInternalRuntimeStatus(deviceStatus?: string | null) {
  const normalized = `${deviceStatus || ''}`.trim()
  return Boolean(normalized) && !normalized.includes('离线')
}

function isCapacitorBankCircuitRateSource(source: string) {
  return source.includes('回路') || source.includes('参数快照') || source.includes('配置总回路')
}

function capacityUsageMetricLabel(isSvgDevice: boolean, source: string) {
  if (isSvgDevice) return '补偿容量利用率'
  if (isCapacitorBankCircuitRateSource(source)) return '回路投入率'
  if (source.includes('额定容量估算')) return '容量利用率（估算）'
  return '补偿容量利用率'
}

function capacityUsageSourceLabel(isSvgDevice: boolean, source: string) {
  if (isSvgDevice) return '容量利用率来源'
  if (isCapacitorBankCircuitRateSource(source)) return '回路投入率来源'
  if (source.includes('额定容量估算')) return '容量利用率来源'
  return '补偿容量利用率来源'
}

export function buildCompensationBaseStatusItems(input: CompensationBaseStatusItemsInput): CompensationStatusItem[] {
  const items: CompensationStatusItem[] = [
    {
      label: '技术类型',
      value: input.subtypeLabel || '未定义',
      tone: 'info',
    },
    {
      label: '平台启用状态',
      value: platformEnableStatusText(input.isActive),
      tone: input.isActive ? 'success' : 'warning',
      hint: '表示平台侧是否允许该设备参与监控与控制，不等于柜内回路已实际投入。',
    },
    {
      label: '当前模式',
      value: input.controlMode,
      tone: input.controlMode === '自动' ? 'info' : 'warning',
      hint: input.controlModeSource,
    },
    {
      label: '控制来源',
      value: input.controlSource,
      tone: 'info',
    },
    {
      label: capacityUsageSourceLabel(input.isSvgDevice, input.capacityUsageSource),
      value: input.capacityUsageSource,
      tone: input.capacityUsageState === 'live' ? 'success' : 'warning',
    },
    {
      label: '温度来源',
      value: input.cabinetTemperatureSource,
      tone: input.cabinetTemperature != null ? 'success' : 'warning',
    },
    {
      label: '最近采样',
      value: input.latestSampleText,
      tone: 'info',
      hint: '来自补偿设备专属 latest 快照',
    },
    {
      label: '是否允许投切',
      value: input.switchPermission ? '允许投切' : '禁止投切',
      tone: input.switchPermission ? 'success' : 'danger',
      hint: input.canControlDevices ? '基于当前权限与在线状态判定' : '当前账号无设备控制权限',
    },
  ]

  if (shouldShowInternalRuntimeStatus(input.deviceStatus)) {
    items.splice(2, 0, {
      label: '内部运行状态',
      value: input.deviceStatus || '状态未知',
      tone: runtimeStatusTone(input.deviceStatus, input.isOnline),
      hint: '表示设备当前运行语义，综合在线状态、采集健康度、告警与停机状态判定。',
    })
  }

  items.splice(shouldShowInternalRuntimeStatus(input.deviceStatus) ? 3 : 2, 0, {
    label: '采集状态',
    value: input.ingestionStatus,
    tone: input.ingestionTone,
    hint: '来自 monitor/runtime-status 的接入健康判定',
  })

  if (input.profileSourceStatus) {
    items.push({
      label: '参数快照',
      value: profileStatusValue(input.profileSourceStatus),
      tone: profileStatusTone(input.profileSourceStatus),
      hint: '来自控制器参数回读档案',
    })
  }

  if (
    typeof input.runningModuleCount === 'number'
    && typeof input.totalModuleCount === 'number'
  ) {
    items.push({
      label: '回路状态',
      value: `${input.runningModuleCount} / ${input.totalModuleCount} 回路投入`,
      tone: input.runningModuleCount > 0 ? 'success' : 'warning',
    })
  }

  return items
}

export function buildCompensationHeaderView(input: CompensationHeaderViewInput): CompensationHeaderModel {
  const tags: CompensationTag[] = [
    {
      label: input.controlMode,
      tone: input.controlModeState === 'live'
        ? (input.controlMode === '自动' ? 'info' : 'warning')
        : 'warning',
    },
  ]
  if (input.compensationStatusText !== input.deviceStatus) {
    tags.push({
      label: input.compensationStatusText,
      tone: input.compensationStatusTone,
    })
  }

  return {
    title: input.title,
    serial: input.serial,
    location: input.location,
    deviceStatus: input.deviceStatus,
    deviceStatusTone: input.isOnline ? 'info' : 'neutral',
    tags,
  }
}

export function buildCompensationOverviewMetrics(input: CompensationOverviewMetricsInput): {
  coreMetric: CompensationMetric
  pfMetric: CompensationMetric
  metrics: CompensationMetric[]
} {
  const cabinetTemperatureHint = input.cabinetTemperature == null
    ? `${input.cabinetTemperatureHealthText || '待判断'} · ${input.cabinetTemperatureHealthHint || input.cabinetTemperatureSource}`
    : `${input.cabinetTemperatureHealthText || '待判断'} · ${input.cabinetTemperatureHealthHint || input.cabinetTemperatureSource} · ${input.cabinetTemperatureSource}`
  const usageMetricLabel = capacityUsageMetricLabel(input.isSvgDevice, input.capacityUsageSource)

  return {
    coreMetric: {
      key: 'reactivePower',
      label: '当前无功功率',
      value: input.reactivePowerValue,
      unit: 'kVar',
      hint: input.reactivePowerHint,
      state: input.reactivePowerMissing ? 'missing' : 'live',
      emphasized: true,
    },
    pfMetric: {
      key: 'powerFactor',
      label: '功率因数',
      value: input.powerFactorValue,
      unit: '',
      hint: input.powerFactorHint,
      tone: input.powerFactorMissing ? 'neutral' : undefined,
      state: input.powerFactorMissing ? 'missing' : 'live',
      emphasized: true,
    },
    metrics: [
      {
        key: 'busVoltage',
        label: '母线电压',
        value: input.voltageValue,
        unit: 'V',
        hint: input.voltageMissing ? '实时电压未采集' : '当前母线测量值',
        state: input.voltageMissing ? 'missing' : 'live',
      },
      {
        key: 'lineCurrent',
        label: '线电流',
        value: input.currentValue,
        unit: 'A',
        hint: input.currentMissing ? '实时电流未采集' : '当前线电流测量值',
        state: input.currentMissing ? 'missing' : 'live',
      },
      {
        key: 'activePower',
        label: '有功功率',
        value: input.activePowerValue,
        unit: 'kW',
        hint: input.activePowerMissing ? '实时有功功率未采集' : '当前柜体有功功率',
        state: input.activePowerMissing ? 'missing' : 'live',
      },
      {
        key: 'capacityUsage',
        label: usageMetricLabel,
        value: `${input.capacityUsageValue.toFixed(1)}`,
        unit: '%',
        hint: input.capacityUsageSource,
        tone: input.capacityUsageValue >= 90 ? 'warning' : 'success',
        state: input.capacityUsageState,
      },
      {
        key: 'gridFrequency',
        label: '电网频率',
        value: input.gridFrequencyValue,
        unit: 'Hz',
        hint: input.gridFrequencyMissing ? '电网频率未采集' : '当前电网频率测量值',
        state: input.gridFrequencyMissing ? 'missing' : 'live',
      },
      {
        key: 'controlMode',
        label: '控制模式',
        value: input.controlMode,
        unit: '',
        hint: input.controlModeSource,
        tone: input.controlMode === '自动' ? 'info' : 'warning',
        state: input.controlModeState,
      },
      {
        key: 'cabinetTemperature',
        label: '柜内温度',
        value: input.cabinetTemperatureValue,
        unit: '°C',
        hint: cabinetTemperatureHint,
        tone: input.cabinetTemperatureHealthTone
          || (input.cabinetTemperature == null
            ? 'neutral'
            : input.cabinetTemperature >= 45
              ? 'danger'
              : input.cabinetTemperature >= 40
                ? 'warning'
                : 'success'),
        state: input.cabinetTemperature == null ? 'missing' : 'live',
      },
    ],
  }
}

export function buildCompensationModuleStatusView(input: CompensationModuleStatusInput): ModuleStatusModel {
  if (input.subtype === 'capacitor_bank_controller' && input.capacitorBankCircuitSummary) {
    const totalCount = Math.max(1, input.capacitorBankCircuitSummary.totalCount)
    const runningCount = Math.max(0, Math.min(totalCount, input.capacitorBankCircuitSummary.runningCount))
    const moduleStates: ModuleStateTone[] = Array.from({ length: totalCount }, (_, index) =>
      index < runningCount ? 'running' : 'standby',
    )

    return {
      title: '回路投切状态',
      unitLabel: input.unitLabel,
      runningModuleCount: runningCount,
      totalModuleCount: totalCount,
      moduleStates,
      hint: input.capacitorBankCircuitSummary.hasRealtimeState
        ? '根据最新回路投切寄存器回读统计当前投入回路数。'
        : '当前未获取到回路投切寄存器，已按后端统一监控语义回退展示。',
    }
  }

  const runningCount = Math.max(
    0,
    Math.min(input.fallbackTotalModuleCount, input.fallbackRunningModuleCount),
  )
  const totalCount = Math.max(runningCount, input.fallbackTotalModuleCount)
  const moduleStates: ModuleStateTone[] = Array.from({ length: totalCount }, (_, index) =>
    index < runningCount ? 'running' : 'standby',
  )
  const alarmIndex = totalCount - 2
  const faultIndex = totalCount - 1

  if (input.svgTelemetry?.overtemp_fault || input.svgTelemetry?.overcurrent_fault) {
    moduleStates[Math.max(runningCount, alarmIndex)] = 'alarm'
  }
  if (input.svgTelemetry?.module_fault) {
    moduleStates[Math.max(runningCount, faultIndex)] = 'fault'
  }

  return {
    title: input.isSvgDevice ? '模块运行状态' : '回路投切状态',
    unitLabel: input.unitLabel,
    runningModuleCount: moduleStates.filter((state) => state === 'running').length,
    totalModuleCount: totalCount,
    moduleStates,
    hint: input.svgTelemetry?.module_fault
      ? '红色表示模块故障，黄色表示模块告警，绿色表示运行，灰色表示待机。'
      : '绿色表示运行，灰色表示待机，黄色表示告警，红色表示故障。',
  }
}

export function buildCompensationExtendedHint(input: CompensationExtendedHintInput) {
  const messages: string[] = []
  if (input.capacityUsageState !== 'live') {
    messages.push(`${capacityUsageSourceLabel(input.isSvgDevice, input.capacityUsageSource)}：${input.capacityUsageSource}。`)
  }
  if (input.controlModeState !== 'live') {
    messages.push(`控制模式当前来源：${input.controlModeSource}。`)
  }
  if (input.cabinetTemperature == null) {
    messages.push('柜内温度当前缺测，暂不展示默认温度。')
  }
  return messages.join(' ')
}

export function buildCompensationStatusItems(input: CompensationStatusItemsInput): CompensationStatusItem[] {
  const items = buildCompensationBaseStatusItems(input)
  items.splice(5, 0, {
    label: '未处理告警',
    value: `${input.unresolvedAlarmCount} 条`,
    tone: input.unresolvedAlarmCount > 0 ? 'warning' : 'success',
  })

  if (input.svgTelemetry) {
    const tel = input.svgTelemetry
    items.push(
      {
        label: '断路器状态',
        value: tel.breaker_status === true ? '已合闸' : tel.breaker_status === false ? '已分闸' : '未知',
        tone: tel.breaker_status === true ? 'success' : tel.breaker_status === false ? 'warning' : 'neutral',
      },
      {
        label: '模块状态',
        value: tel.module_status === true ? '正常' : tel.module_status === false ? '故障' : '未知',
        tone: tel.module_status === true ? 'success' : tel.module_status === false ? 'danger' : 'neutral',
      },
      {
        label: '风机状态',
        value: tel.fan_status === true ? '运行' : tel.fan_status === false ? '停止/故障' : '未知',
        tone: tel.fan_status === true ? 'success' : tel.fan_status === false ? 'warning' : 'neutral',
      },
      {
        label: '运行反馈',
        value: booleanStatus(tel.run_status, '运行', '未运行'),
        tone: tel.run_status === true ? 'success' : tel.run_status === false ? 'neutral' : 'info',
      },
      {
        label: '停机反馈',
        value: booleanStatus(tel.stop_status, '已停机', '未停机'),
        tone: tel.stop_status === true ? 'warning' : tel.stop_status === false ? 'success' : 'neutral',
      },
      {
        label: '就地模式',
        value: booleanStatus(tel.local_mode, '就地', '远程'),
        tone: tel.local_mode === true ? 'warning' : tel.local_mode === false ? 'info' : 'neutral',
      },
      {
        label: '通讯状态',
        value: booleanStatus(tel.comm_status, '通讯正常', '通讯异常'),
        tone: tel.comm_status === true ? 'success' : tel.comm_status === false ? 'danger' : 'neutral',
      },
    )
    const faults = [
      tel.overvoltage_fault && '过压',
      tel.undervoltage_fault && '欠压',
      tel.overcurrent_fault && '过流',
      tel.overtemp_fault && '过温',
      tel.module_fault && '模块故障',
      tel.fan_fault && '风机故障',
      tel.comm_fault && '通讯故障',
    ].filter(Boolean) as string[]
    items.push(
      {
        label: '当前故障',
        value: faults.length > 0 ? faults.join(' / ') : '无故障',
        tone: faults.length > 0 ? 'danger' : 'success',
      },
      {
        label: '故障代码',
        value: tel.current_fault_code || '无编码',
        tone: tel.current_fault_code ? 'danger' : 'success',
        hint: '来自 SVG 遥测故障编码',
      },
      {
        label: '告警代码',
        value: tel.current_alarm_code || '无编码',
        tone: tel.current_alarm_code ? 'warning' : 'success',
        hint: '来自 SVG 遥测告警编码',
      },
      {
        label: '柜内 / 模块温度',
        value: `${displayValue(tel.cabinet_temp, '暂无数据')} °C / ${displayValue(tel.module_temp, '暂无数据')} °C`,
        tone: statusTemperatureTone(tel.cabinet_temp, tel.module_temp),
      },
      {
        label: 'IGBT / 散热器温度',
        value: `${displayValue(tel.igbt_temp, '暂无数据')} °C / ${displayValue(tel.heatsink_temp, '暂无数据')} °C`,
        tone: statusTemperatureTone(tel.igbt_temp, tel.heatsink_temp),
      },
    )
    return items
  }

  if (input.capacitorBankTelemetry) {
    const tel = input.capacitorBankTelemetry
    const capFlags = [
      tel.leading_a && 'A超前',
      tel.leading_b && 'B超前',
      tel.leading_c && 'C超前',
      tel.temp_alarm && '温度告警',
      tel.overvoltage_alarm_a && 'A相过压',
      tel.overvoltage_alarm_b && 'B相过压',
      tel.overvoltage_alarm_c && 'C相过压',
    ].filter(Boolean) as string[]
    items.push(
      {
        label: '控制策略',
        value: '按功率因数自动投切',
        tone: 'info',
        hint: '适用于 JKWF 等传统电容补偿控制器的常见控制方式',
      },
      {
        label: '频率 / 温度',
        value: `${displayValue(tel.frequency, '暂无数据', 2)} Hz / ${displayValue(tel.temperature, '暂无数据')} °C`,
        tone: tel.temp_alarm ? 'warning' : 'info',
      },
      {
        label: '当前标志',
        value: capFlags.length ? capFlags.join(' / ') : '无异常标志',
        tone: capFlags.length ? 'warning' : 'success',
      },
    )
    return items
  }

  if (!input.isSvgDevice) {
    items.push({
      label: '控制策略',
      value: '按功率因数自动投切',
      tone: 'info',
      hint: '适用于 JKWF 等传统电容补偿控制器的常见控制方式',
    })
  }

  return items
}

export function buildCompensationProfileItems(input: CompensationProfileItemsInput): CompensationProfileItem[] {
  const archive = input.archive
  const prof = input.svgProfile
  const items: CompensationProfileItem[] = [
    { label: '设备名称', value: archive?.name || '补偿器1' },
    { label: '序列号', value: archive?.sn || 'SN2323' },
    { label: '设备分类', value: input.categoryLabel || '无功功率补偿设备' },
    { label: '技术类型', value: input.subtypeLabel || '未定义' },
    { label: '能源类型', value: archive?.energy_type || '电' },
    { label: '安装位置', value: archive?.location || '未配置安装位置' },
    { label: '额定容量', value: (archive?.rated_capacity != null && archive.rated_capacity > 0) ? `${archive.rated_capacity} kVar` : '未配置' },
    { label: '描述', value: archive?.description || '用于无功补偿与功率因数优化的柜体设备。' },
  ]
  if (!prof) return items

  if (prof.model_number) items.push({ label: '产品型号', value: prof.model_number })
  if (prof.rated_voltage) items.push({ label: '额定电压', value: `${prof.rated_voltage} V` })
  if (prof.rated_frequency) items.push({ label: '额定频率', value: `${prof.rated_frequency} Hz` })
  if (prof.module_count) items.push({ label: '模块数量', value: `${prof.module_count} 组` })
  if (prof.software_version) items.push({ label: '软件版本', value: prof.software_version })
  if (prof.hardware_version) items.push({ label: '硬件版本', value: prof.hardware_version })
  if (prof.protocol_version) items.push({ label: '协议版本', value: prof.protocol_version })
  if (prof.distribution_room) items.push({ label: '配电房', value: prof.distribution_room })
  if (prof.building) items.push({ label: '所在楼栋', value: prof.building })
  if (prof.circuit) items.push({ label: '所在回路', value: prof.circuit })
  if (prof.asset_number) items.push({ label: '资产编号', value: prof.asset_number })
  if (prof.fixed_asset_code) items.push({ label: '固定资产编码', value: prof.fixed_asset_code })
  if (prof.qr_code_number) items.push({ label: '二维码编号', value: prof.qr_code_number })
  if (prof.asset_group) items.push({ label: '资产分组', value: prof.asset_group })
  if (prof.department) items.push({ label: '归属部门', value: prof.department })
  if (prof.management_unit) items.push({ label: '管理单位', value: prof.management_unit })
  if (prof.contact_phone) items.push({ label: '联系电话', value: prof.contact_phone })
  if (prof.om_responsible) items.push({ label: '运维负责人', value: prof.om_responsible })
  if (prof.inspection_responsible) items.push({ label: '巡检负责人', value: prof.inspection_responsible })
  if (prof.maintenance_cycle_days) items.push({ label: '维保周期', value: `${prof.maintenance_cycle_days} 天` })
  if (prof.commission_date) items.push({ label: '投运日期', value: prof.commission_date })
  if (prof.warranty_expiry) items.push({ label: '质保到期', value: prof.warranty_expiry })
  if (prof.device_group) items.push({ label: '设备分组', value: prof.device_group })
  if (prof.device_tree_level) items.push({ label: '设备树层级', value: prof.device_tree_level })
  if (prof.monitor_screen_position) items.push({ label: '监控画面位置', value: prof.monitor_screen_position })
  if (prof.alarm_policy) items.push({ label: '告警策略', value: prof.alarm_policy })
  if (prof.device_alias) items.push({ label: '设备别名', value: prof.device_alias })
  if (prof.display_name) items.push({ label: '展示名称', value: prof.display_name })

  return items
}

export function buildCapacitorBankControlSummaryView(
  input: CapacitorBankControlSummaryViewInput,
): CapacitorBankControlSummaryView {
  const profile = input.profile
  const summaryItems = capacitorBankControlParameterMeta
    .filter((item) => item.summary)
    .map((item) => ({
      label: item.label,
      value: profile ? formatCapacitorBankControlValue(profile, item) : '暂无参数',
    }))

  const capacityExpansionItems: CompensationProfileItem[] = profile
    ? [
      {
        label: 'A相分补',
        value: formatCapacitySlotList(profile.phase_a_capacity_steps_kvar ?? profile.split_capacity_expansion?.phase_a_groups),
      },
      {
        label: 'B相分补',
        value: formatCapacitySlotList(profile.phase_b_capacity_steps_kvar ?? profile.split_capacity_expansion?.phase_b_groups),
      },
      {
        label: 'C相分补',
        value: formatCapacitySlotList(profile.phase_c_capacity_steps_kvar ?? profile.split_capacity_expansion?.phase_c_groups),
      },
      {
        label: '公补 1-8',
        value: formatCapacitySlotList(profile.common_1_capacity_steps_kvar ?? profile.common_capacity_expansion?.common_1_groups),
      },
      {
        label: '公补 9-16',
        value: formatCapacitySlotList(profile.common_2_capacity_steps_kvar ?? profile.common_capacity_expansion?.common_2_groups),
      },
      {
        label: '公补 17-24',
        value: formatCapacitySlotList(profile.common_3_capacity_steps_kvar ?? profile.common_capacity_expansion?.common_3_groups),
      },
    ]
    : []

  return {
    summaryItems,
    capacityExpansionItems,
    hasSummaryData: summaryItems.some((item) => item.value !== '暂无参数'),
  }
}

export function buildCompensationTrendView(input: CompensationTrendViewInput): CompensationTrendModel {
  const labels = buildTrendLabels(input.trendPoints, input.timeRange)
  const [selectedStart, selectedEnd] = input.timeRange
  const xAxisMin = selectedStart.toISOString()
  const xAxisMax = selectedEnd.toISOString()

  if (input.activeTab === 'effect') {
    const useCapBankHistory = input.subtype === 'capacitor_bank_controller'
      && input.capacitorBankTelemetryHistory.length > 0
    const hasRealQ = useCapBankHistory
      ? (
          hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'reactive_power_a')
          || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'reactive_power_b')
          || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'reactive_power_c')
        )
      : input.trendPoints.some((p) => p.reactive_power != null)
    const hasRealPf = useCapBankHistory
      ? (
          hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'power_factor_a')
          || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'power_factor_b')
          || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'power_factor_c')
        )
      : input.trendPoints.some((p) => p.power_factor != null)
    const hasHistory = hasRealQ || hasRealPf
    const qSeries: Array<[string, number | null]> = useCapBankHistory
      ? buildTimedCapBankAggregateSeries(
          input.capacitorBankTelemetryHistory,
          ['reactive_power_a', 'reactive_power_b', 'reactive_power_c'],
          'sum',
        )
      : input.trendPoints.map((p) => [p.timestamp, p.reactive_power ?? null])
    const pfSeries: Array<[string, number | null]> = useCapBankHistory
      ? buildTimedCapBankAggregateSeries(
          input.capacitorBankTelemetryHistory,
          ['power_factor_a', 'power_factor_b', 'power_factor_c'],
          'average',
        )
      : input.trendPoints.map((p) => [p.timestamp, p.power_factor ?? null])
    return {
      labels: [],
      legend: ['无功功率 Q', '功率因数 PF'],
      axes: [
        { name: 'kVar' },
        { name: 'PF', min: 0.8, max: 1.1, position: 'right' },
      ],
      series: [
        { name: '无功功率 Q', data: qSeries, color: '#38bdf8', area: true },
        { name: '功率因数 PF', data: pfSeries, color: '#4ade80', yAxisIndex: 1 },
      ],
      xAxisType: 'time',
      xAxisMin,
      xAxisMax,
      summary: [
        { label: '当前 Q', value: displayValueWithUnit(input.realtime?.reactive_power, '-', 'kVar') },
        { label: '当前 PF', value: displayValue(input.realtime?.power_factor, '-', 2) },
        { label: '目标 PF', value: displayValue(input.fallbackCompensation.targetPowerFactor, '-', 2) },
      ],
      empty: !hasHistory,
      emptyText: '',
      hint: hasHistory
        ? (useCapBankHistory
            ? '展示电容控制器专属历史中的三相无功合计与功率因数均值走势。'
            : '展示历史采集的无功功率与功率因数走势。')
        : '当前时间范围内没有补偿效果历史数据。',
      isMock: false,
    }
  }

  if (input.subtype === 'capacitor_bank_controller' && input.activeTab === 'phase_power') {
    const hasHistory = hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'reactive_power_a')
      || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'active_power_a')
      || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'power_factor_a')
    return {
      labels: [],
      legend: ['A相有功', 'B相有功', 'C相有功', 'A相无功', 'B相无功', 'C相无功', 'A相PF', 'B相PF', 'C相PF'],
      axes: [
        { name: 'kW / kvar' },
        { name: 'PF', min: 0.8, max: 1.1, position: 'right' },
      ],
      series: [
        { name: 'A相有功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'active_power_a'), color: '#38bdf8' },
        { name: 'B相有功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'active_power_b'), color: '#60a5fa' },
        { name: 'C相有功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'active_power_c'), color: '#93c5fd' },
        { name: 'A相无功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'reactive_power_a'), color: '#22c55e' },
        { name: 'B相无功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'reactive_power_b'), color: '#4ade80' },
        { name: 'C相无功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'reactive_power_c'), color: '#86efac' },
        { name: 'A相PF', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'power_factor_a'), color: '#f59e0b', yAxisIndex: 1 },
        { name: 'B相PF', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'power_factor_b'), color: '#fbbf24', yAxisIndex: 1 },
        { name: 'C相PF', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'power_factor_c'), color: '#fcd34d', yAxisIndex: 1 },
      ],
      xAxisType: 'time',
      xAxisMin,
      xAxisMax,
      summary: [
        { label: 'A相有功', value: displayValueWithUnit(input.capacitorBankTelemetry?.active_power_a, '暂无数据', 'kW') },
        { label: 'B相无功', value: displayValueWithUnit(input.capacitorBankTelemetry?.reactive_power_b, '暂无数据', 'kvar') },
        { label: 'C相PF', value: displayValue(input.capacitorBankTelemetry?.power_factor_c, '暂无数据', 3) },
      ],
      empty: !hasHistory,
      emptyText: '暂无三相功率历史数据',
      hint: hasHistory ? '展示电容控制器三相有功、无功与功率因数历史走势。' : '当前时间范围内没有三相功率历史数据。',
      isMock: false,
    }
  }

  if (input.subtype === 'capacitor_bank_controller' && input.activeTab === 'phase_active_power') {
    const hasHistory = hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'active_power_a')
      || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'active_power_b')
      || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'active_power_c')
    return {
      labels: [],
      legend: ['A相有功', 'B相有功', 'C相有功'],
      axes: [{ name: 'kW' }],
      series: [
        { name: 'A相有功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'active_power_a'), color: '#38bdf8' },
        { name: 'B相有功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'active_power_b'), color: '#60a5fa' },
        { name: 'C相有功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'active_power_c'), color: '#93c5fd' },
      ],
      xAxisType: 'time',
      xAxisMin,
      xAxisMax,
      summary: [
        { label: 'A相有功', value: displayValueWithUnit(input.capacitorBankTelemetry?.active_power_a, '暂无数据', 'kW') },
        { label: 'B相有功', value: displayValueWithUnit(input.capacitorBankTelemetry?.active_power_b, '暂无数据', 'kW') },
        { label: 'C相有功', value: displayValueWithUnit(input.capacitorBankTelemetry?.active_power_c, '暂无数据', 'kW') },
      ],
      empty: !hasHistory,
      emptyText: '暂无三相有功历史数据',
      hint: hasHistory ? '展示电容控制器 A/B/C 三相有功功率历史走势。' : '当前时间范围内没有三相有功历史数据。',
      isMock: false,
    }
  }

  if (input.subtype === 'capacitor_bank_controller' && input.activeTab === 'phase_reactive_power') {
    const hasHistory = hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'reactive_power_a')
      || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'reactive_power_b')
      || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'reactive_power_c')
    return {
      labels: [],
      legend: ['A相无功', 'B相无功', 'C相无功'],
      axes: [{ name: 'kvar' }],
      series: [
        { name: 'A相无功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'reactive_power_a'), color: '#22c55e' },
        { name: 'B相无功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'reactive_power_b'), color: '#4ade80' },
        { name: 'C相无功', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'reactive_power_c'), color: '#86efac' },
      ],
      xAxisType: 'time',
      xAxisMin,
      xAxisMax,
      summary: [
        { label: 'A相无功', value: displayValueWithUnit(input.capacitorBankTelemetry?.reactive_power_a, '暂无数据', 'kvar') },
        { label: 'B相无功', value: displayValueWithUnit(input.capacitorBankTelemetry?.reactive_power_b, '暂无数据', 'kvar') },
        { label: 'C相无功', value: displayValueWithUnit(input.capacitorBankTelemetry?.reactive_power_c, '暂无数据', 'kvar') },
      ],
      empty: !hasHistory,
      emptyText: '暂无三相无功历史数据',
      hint: hasHistory ? '展示电容控制器 A/B/C 三相无功功率历史走势。' : '当前时间范围内没有三相无功历史数据。',
      isMock: false,
    }
  }

  if (input.subtype === 'capacitor_bank_controller' && input.activeTab === 'phase_power_factor') {
    const hasHistory = hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'power_factor_a')
      || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'power_factor_b')
      || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'power_factor_c')
    return {
      labels: [],
      legend: ['A相PF', 'B相PF', 'C相PF'],
      axes: [{ name: 'PF', min: 0.8, max: 1.1 }],
      series: [
        { name: 'A相PF', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'power_factor_a'), color: '#f59e0b' },
        { name: 'B相PF', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'power_factor_b'), color: '#fbbf24' },
        { name: 'C相PF', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'power_factor_c'), color: '#fcd34d' },
      ],
      xAxisType: 'time',
      xAxisMin,
      xAxisMax,
      summary: [
        { label: 'A相PF', value: displayValue(input.capacitorBankTelemetry?.power_factor_a, '暂无数据', 3) },
        { label: 'B相PF', value: displayValue(input.capacitorBankTelemetry?.power_factor_b, '暂无数据', 3) },
        { label: 'C相PF', value: displayValue(input.capacitorBankTelemetry?.power_factor_c, '暂无数据', 3) },
      ],
      empty: !hasHistory,
      emptyText: '暂无三相功率因数历史数据',
      hint: hasHistory ? '展示电容控制器 A/B/C 三相功率因数历史走势。' : '当前时间范围内没有三相功率因数历史数据。',
      isMock: false,
    }
  }

  if (input.subtype === 'capacitor_bank_controller' && input.activeTab === 'phase_voltage') {
    const hasHistory = hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'voltage_a')
    return {
      labels: [],
      legend: ['A相电压', 'B相电压', 'C相电压'],
      axes: [{ name: 'V', min: 200, max: 240 }],
      series: [
        { name: 'A相电压', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'voltage_a'), color: '#38bdf8' },
        { name: 'B相电压', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'voltage_b'), color: '#60a5fa' },
        { name: 'C相电压', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'voltage_c'), color: '#93c5fd' },
      ],
      xAxisType: 'time',
      xAxisMin,
      xAxisMax,
      summary: [
        { label: 'A相电压', value: displayValueWithUnit(input.capacitorBankTelemetry?.voltage_a, '暂无数据', 'V') },
        { label: 'B相电压', value: displayValueWithUnit(input.capacitorBankTelemetry?.voltage_b, '暂无数据', 'V') },
        { label: 'C相电压', value: displayValueWithUnit(input.capacitorBankTelemetry?.voltage_c, '暂无数据', 'V') },
      ],
      empty: !hasHistory,
      emptyText: '暂无三相电压历史数据',
      hint: hasHistory ? '展示三相母线电压的专属历史曲线。' : '当前时间范围内没有三相电压历史数据。',
      isMock: false,
    }
  }

  if (input.subtype === 'capacitor_bank_controller' && input.activeTab === 'phase_current') {
    const hasHistory = hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'current_a')
    return {
      labels: [],
      legend: ['A相电流', 'B相电流', 'C相电流'],
      axes: [{ name: 'A' }],
      series: [
        { name: 'A相电流', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'current_a'), color: '#f59e0b' },
        { name: 'B相电流', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'current_b'), color: '#fbbf24' },
        { name: 'C相电流', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'current_c'), color: '#fcd34d' },
      ],
      xAxisType: 'time',
      xAxisMin,
      xAxisMax,
      summary: [
        { label: 'A相电流', value: displayValueWithUnit(input.capacitorBankTelemetry?.current_a, '暂无数据', 'A') },
        { label: 'B相电流', value: displayValueWithUnit(input.capacitorBankTelemetry?.current_b, '暂无数据', 'A') },
        { label: 'C相电流', value: displayValueWithUnit(input.capacitorBankTelemetry?.current_c, '暂无数据', 'A') },
      ],
      empty: !hasHistory,
      emptyText: '暂无三相电流历史数据',
      hint: hasHistory ? '展示三相线电流的专属历史曲线。' : '当前时间范围内没有三相电流历史数据。',
      isMock: false,
    }
  }

  if (input.subtype === 'capacitor_bank_controller' && input.activeTab === 'harmonic') {
    const hasHistory = hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'voltage_thd_a')
      || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'current_harmonic_a')
    return {
      labels: [],
      legend: ['A相电压THD', 'B相电压THD', 'C相电压THD', 'A相谐波电流', 'B相谐波电流', 'C相谐波电流'],
      axes: [
        { name: '%' },
        { name: 'A', position: 'right' },
      ],
      series: [
        { name: 'A相电压THD', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'voltage_thd_a'), color: '#fb7185', area: true },
        { name: 'B相电压THD', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'voltage_thd_b'), color: '#f43f5e', area: true },
        { name: 'C相电压THD', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'voltage_thd_c'), color: '#e11d48', area: true },
        { name: 'A相谐波电流', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'current_harmonic_a'), color: '#22c55e', yAxisIndex: 1 },
        { name: 'B相谐波电流', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'current_harmonic_b'), color: '#4ade80', yAxisIndex: 1 },
        { name: 'C相谐波电流', data: buildTimedCapBankSeries(input.capacitorBankTelemetryHistory, 'current_harmonic_c'), color: '#86efac', yAxisIndex: 1 },
      ],
      xAxisType: 'time',
      xAxisMin,
      xAxisMax,
      summary: [
        { label: 'A相THD', value: displayValueWithUnit(input.capacitorBankTelemetry?.voltage_thd_a, '暂无数据', '%') },
        { label: 'B相谐波电流', value: displayValueWithUnit(input.capacitorBankTelemetry?.current_harmonic_b, '暂无数据', 'A') },
        { label: '温度告警', value: input.capacitorBankTelemetry?.temp_alarm ? '告警中' : '正常' },
      ],
      empty: !hasHistory,
      emptyText: '暂无谐波历史数据',
      hint: hasHistory ? '展示三相电压 THD 与谐波电流历史走势。' : '当前时间范围内没有谐波历史数据。',
      isMock: false,
    }
  }

  if (input.subtype === 'capacitor_bank_controller' && input.activeTab === 'switching') {
    const hasHistory = hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'circuit_state_phase_a')
      || hasCapBankHistoryValue(input.capacitorBankTelemetryHistory, 'circuit_state_common_1')
    return {
      labels: [],
      legend: ['A相投入路数', 'B相投入路数', 'C相投入路数', '公补投入路数'],
      axes: [{ name: '路数', min: 0, max: 20 }],
      series: [
        { name: 'A相投入路数', data: buildTimedCapBankSwitchingSeries(input.capacitorBankTelemetryHistory, 'circuit_state_phase_a'), color: '#38bdf8' },
        { name: 'B相投入路数', data: buildTimedCapBankSwitchingSeries(input.capacitorBankTelemetryHistory, 'circuit_state_phase_b'), color: '#60a5fa' },
        { name: 'C相投入路数', data: buildTimedCapBankSwitchingSeries(input.capacitorBankTelemetryHistory, 'circuit_state_phase_c'), color: '#93c5fd' },
        { name: '公补投入路数', data: buildTimedCapBankSwitchingSeries(input.capacitorBankTelemetryHistory, ['circuit_state_common_1', 'circuit_state_common_2', 'circuit_state_common_3']), color: '#f59e0b' },
      ],
      xAxisType: 'time',
      xAxisMin,
      xAxisMax,
      summary: [
        { label: 'A相分补', value: displayValue(decodeSwitchingCount(input.capacitorBankTelemetry?.circuit_state_phase_a), '暂无数据', 0) },
        { label: '公补 1-8', value: displayValue(decodeSwitchingCount(input.capacitorBankTelemetry?.circuit_state_common_1), '暂无数据', 0) },
        { label: '当前采样', value: displayValue(input.capacitorBankTelemetry?.timestamp, '暂无数据') },
      ],
      empty: !hasHistory,
      emptyText: '暂无投切历史数据',
      hint: hasHistory ? '按历史寄存器变化估算各组投入路数，用于回看投切节奏。' : '当前时间范围内没有投切回放历史数据。',
      isMock: false,
    }
  }

  if (input.activeTab === 'voltage') {
    const voltageSeries = buildTrendSeriesFromPoints(input.trendPoints, 'voltage')
    const timedValues = input.trendPoints.map((point) => [point.timestamp, point.voltage ?? null] as [string, number | null])
    return trendModelFromSingleSeries({
      labels: [],
      name: '母线电压',
      unit: 'V',
      color: '#60a5fa',
      values: timedValues,
      summaryItems: [
        { label: '当前电压', value: displayValueWithUnit(input.realtime?.voltage, '暂无数据', 'V') },
        { label: '峰值', value: displayValueWithUnit(voltageSeries.peak, '暂无数据', 'V') },
        { label: '谷值', value: displayValueWithUnit(voltageSeries.valley, '暂无数据', 'V') },
      ],
      isMock: voltageSeries.isMock,
      hint: voltageSeries.isMock ? '当前时间范围内没有母线电压历史数据。' : '展示最近时间范围内的母线电压走势。',
      emptyText: '暂无电压趋势数据',
      xAxisType: 'time',
      xAxisMin,
      xAxisMax,
    })
  }

  if (input.activeTab === 'current') {
    const currentSeries = buildTrendSeriesFromPoints(input.trendPoints, 'current')
    const timedValues = input.trendPoints.map((point) => [point.timestamp, point.current ?? null] as [string, number | null])
    return trendModelFromSingleSeries({
      labels: [],
      name: '线电流',
      unit: 'A',
      color: '#f59e0b',
      values: timedValues,
      summaryItems: [
        { label: '当前电流', value: displayValueWithUnit(input.realtime?.current, '暂无数据', 'A') },
        { label: '峰值', value: displayValueWithUnit(currentSeries.peak, '暂无数据', 'A') },
        { label: '谷值', value: displayValueWithUnit(currentSeries.valley, '暂无数据', 'A') },
      ],
      isMock: currentSeries.isMock,
      hint: currentSeries.isMock ? '当前时间范围内没有线电流历史数据。' : '展示最近时间范围内的线电流走势。',
      emptyText: '暂无电流趋势数据',
      xAxisType: 'time',
      xAxisMin,
      xAxisMax,
    })
  }

  const hasCabinetTemp = input.isSvgDevice
    ? input.svgTelemetryHistory.some((p) => p.cabinet_temp != null)
    : input.capacitorBankTelemetryHistory.some((p) => p.temperature != null)
  const hasFrequencyHistory = !input.isSvgDevice && input.capacitorBankTelemetryHistory.some((p) => p.frequency != null)
  const healthFrequency = hasFrequencyHistory
    ? input.capacitorBankTelemetryHistory.map((p) => p.frequency ?? null)
    : []
  // 即使历史中没有频率数据，只要最新遥测有频率值，也显示频率轴
  const showFrequencyAxis = !input.isSvgDevice && (hasFrequencyHistory || input.capacitorBankTelemetry?.frequency != null)
  const svgTempDetails = input.isSvgDevice
    ? [
      { label: '模块温度', value: displayValueWithUnit(input.svgTelemetry?.module_temp, '暂无数据', '°C') },
      { label: 'IGBT 温度', value: displayValueWithUnit(input.svgTelemetry?.igbt_temp, '暂无数据', '°C') },
      { label: '散热器温度', value: displayValueWithUnit(input.svgTelemetry?.heatsink_temp, '暂无数据', '°C') },
    ]
    : []
  const hasHealthData = hasCabinetTemp || healthFrequency.length > 0
  return {
    labels: [],
    legend: showFrequencyAxis ? ['柜内温度', '频率'] : ['柜内温度'],
    axes: showFrequencyAxis
      ? [
        { name: '°C', min: 0, max: 100 },
        { name: 'Hz', min: 45, max: 55, position: 'right' },
      ]
      : [
        { name: '°C', min: 0, max: 100 },
      ],
    series: [
      {
        name: '柜内温度',
        data: (input.isSvgDevice ? input.svgTelemetryHistory : input.capacitorBankTelemetryHistory).map((point) => [
          point.timestamp,
          input.isSvgDevice ? (point as CompensationSvgTelemetry).cabinet_temp ?? null : (point as CompensationCapacitorBankTelemetry).temperature ?? null,
        ]),
        color: '#fb7185',
        area: true,
      },
      ...(showFrequencyAxis
        ? [{
            name: '频率',
            data: input.capacitorBankTelemetryHistory.map((point) => [point.timestamp, point.frequency ?? null] as [string, number | null]),
            color: '#60a5fa',
            yAxisIndex: 1,
          }]
        : []),
    ],
    xAxisType: 'time',
    xAxisMin,
    xAxisMax,
    summary: [
      { label: '柜内温度', value: displayValueWithUnit(input.isSvgDevice ? input.svgTelemetry?.cabinet_temp : input.capacitorBankTelemetry?.temperature, '暂无数据', '°C') },
      { label: !input.isSvgDevice ? '电网频率' : '模块温度', value: !input.isSvgDevice ? displayValueWithUnit(input.capacitorBankTelemetry?.frequency, '暂无数据', 'Hz', 2) : displayValueWithUnit(input.svgTelemetry?.module_temp, '暂无数据', '°C') },
      ...(input.isSvgDevice ? svgTempDetails : []),
    ],
    empty: !hasHealthData,
    emptyText: '暂无温度与健康度趋势数据',
    hint: hasHealthData ? (input.isSvgDevice ? '展示采集的柜内及核心器件温度历史走势。' : '展示柜内温度与频率历史走势。') : '当前时间范围内没有温度或频率历史数据。',
    isMock: false,
  }
}
