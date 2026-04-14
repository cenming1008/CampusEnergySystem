<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Refresh, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useECharts } from '@/shared/composables/useECharts'
import { usePermissions } from '@/shared/composables/usePermissions'
import { resolveAlarm } from '@/api/alarm'
import { toggleDeviceStatus } from '@/api/device'
import {
  getDeviceMonitorAlarms,
  getDeviceMonitorControlLogs,
  getDeviceMonitorOverview,
  getDeviceMonitorRealtime,
  getDeviceMonitorStatusHistory,
  getDeviceMonitorTrend,
  type DeviceAlarmRecord,
  type DeviceControlLog,
  type DeviceStatusEvent,
  type DeviceTrendResponse,
  type MonitorOverview,
  type TrendPoint,
} from '@/api/deviceMonitor'
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
import { resolveCompensationSubtype } from '@/shared/compensationDevices'
import { getDeviceCategoryLabel, getDeviceSubtypeLabel } from '@/shared/deviceTypeLabels'
import {
  capacitorBankControlParameterMeta,
  formatCapacitorBankControlValue,
} from '@/features/device-control/capacitorBankControlProfile'
import CompensationHeader from '@/features/device-monitor/components/compensation/CompensationHeader.vue'
import CompensationRealtimeOverview from '@/features/device-monitor/components/compensation/CompensationRealtimeOverview.vue'
import CompensationTrendPanel from '@/features/device-monitor/components/compensation/CompensationTrendPanel.vue'
import CompensationEventTimeline from '@/features/device-monitor/components/compensation/CompensationEventTimeline.vue'
import CompensationStatusSummary from '@/features/device-monitor/components/compensation/CompensationStatusSummary.vue'
import CompensationDeviceProfile from '@/features/device-monitor/components/compensation/CompensationDeviceProfile.vue'
import CompensationAlarmTable from '@/features/device-monitor/components/compensation/CompensationAlarmTable.vue'
import CompensationThreePhasePanel from '@/features/device-monitor/components/compensation/CompensationThreePhasePanel.vue'
import CompensationCircuitStatePanel from '@/features/device-monitor/components/compensation/CompensationCircuitStatePanel.vue'
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
  ModuleStateTone,
} from '@/features/device-monitor/components/compensation/types'

const route = useRoute()
const router = useRouter()
const chart = useECharts()
const { canControlDevices } = usePermissions()

const deviceId = computed(() => Number(route.params.id))
const loading = ref(false)
const chartLoading = ref(false)
const toggleSubmitting = ref(false)
const alarmActionId = ref<number | null>(null)
const overview = ref<MonitorOverview | null>(null)
const trend = ref<DeviceTrendResponse | null>(null)
const alarms = ref<DeviceAlarmRecord[]>([])
const controlLogs = ref<DeviceControlLog[]>([])
const statusHistory = ref<DeviceStatusEvent[]>([])
const chartMetric = ref<'flow_rate' | 'voltage' | 'current'>('flow_rate')
const alarmFilter = ref<'all' | 'unresolved' | 'resolved'>('all')
const timeRange = ref<[Date, Date] | null>(defaultTimeRange())
const compensationTrendTab = ref<CompensationTrendTab>('effect')
const compensationSvgTelemetry = ref<CompensationSvgTelemetry | null>(null)
const compensationSvgProfile = ref<CompensationSvgOperationsProfile | null>(null)
const compensationSvgTelemetryHistory = ref<CompensationSvgTelemetry[]>([])
const compensationCapacitorBankTelemetry = ref<CompensationCapacitorBankTelemetry | null>(null)
const compensationCapacitorBankTelemetryHistory = ref<CompensationCapacitorBankTelemetry[]>([])
const compensationCapacitorBankControlProfile = ref<CompensationCapacitorBankControlProfile | null>(null)
let refreshTimer: ReturnType<typeof setInterval> | null = null
const REFRESH_INTERVAL_MS = 5000

const archive = computed(() => overview.value?.archive)
const runtimeStatus = computed(() => overview.value?.runtime_status)
const realtime = computed(() => overview.value?.realtime)
const compensationSubtype = computed(() => resolveCompensationSubtype(
  archive.value?.device_type,
  archive.value?.device_subtype,
) || '')

const isCompensationDevice = computed(() =>
  Boolean(compensationSubtype.value),
)
const isSvgDevice = computed(() => compensationSubtype.value === 'svg')
const compensationCategoryLabel = computed(() => getDeviceCategoryLabel('compensation'))
const compensationSubtypeLabel = computed(() => getDeviceSubtypeLabel(compensationSubtype.value))
const compensationUnitLabel = computed(() => (isSvgDevice.value ? '模块' : '回路'))

const chartMetricOptions = [
  { label: '功率/流量', value: 'flow_rate' as const },
  { label: '电压', value: 'voltage' as const },
  { label: '电流', value: 'current' as const },
]

const compensationTrendTabs = computed<CompensationTrendOption[]>(() => {
  if (compensationSubtype.value === 'capacitor_bank_controller') {
    return [
      { label: '补偿效果', value: 'effect' },
      { label: '三相功率', value: 'phase_power' },
      { label: '三相电压', value: 'phase_voltage' },
      { label: '三相电流', value: 'phase_current' },
      { label: '谐波', value: 'harmonic' },
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

const timeShortcuts = [
  { text: '近 1 小时', value: () => buildRecentRange(1) },
  { text: '近 6 小时', value: () => buildRecentRange(6) },
  { text: '近 24 小时', value: () => buildRecentRange(24) },
  { text: '近 7 天', value: () => buildRecentRange(24 * 7) },
]

const metricCards = computed(() => [
  { label: '实时功率/流量', value: displayNumber(realtime.value?.flow_rate), unit: archive.value?.unit || 'kW' },
  { label: '累计读数', value: displayNumber(realtime.value?.consumption), unit: inferConsumptionUnit() },
  { label: '电压', value: displayNumber(realtime.value?.voltage), unit: 'V' },
  { label: '电流', value: displayNumber(realtime.value?.current), unit: 'A' },
])

const trendSummary = computed(() => {
  const values = (trend.value?.points || [])
    .map((point) => getTrendMetricValue(point, chartMetric.value))
    .filter((value): value is number => value !== null && value !== undefined)

  if (!values.length) {
    return { latest: null, peak: null, valley: null, average: null }
  }

  return {
    latest: values[values.length - 1],
    peak: Math.max(...values),
    valley: Math.min(...values),
    average: values.reduce((sum, value) => sum + value, 0) / values.length,
  }
})

function countActiveBits(value?: number | null) {
  if (typeof value !== 'number' || Number.isNaN(value)) return 0
  let count = 0
  for (let bit = 0; bit < 16; bit += 1) {
    if (value & (1 << bit)) count += 1
  }
  return count
}

function resolveCapBankControlMode() {
  const scheme = compensationCapacitorBankControlProfile.value?.terminal_assignment_scheme?.trim()
  if (scheme) {
    if (scheme.includes('手动')) return { value: '手动', source: '参数回读' as const, state: 'live' as const }
    if (scheme.includes('自动')) return { value: '自动', source: '参数回读' as const, state: 'live' as const }
    return { value: scheme, source: '参数回读' as const, state: 'live' as const }
  }
  return { value: isDeviceActive.value ? '自动' : '待确认', source: '估算/占位' as const, state: 'mock' as const }
}

const capacitorBankCircuitSummary = computed(() => {
  if (compensationSubtype.value !== 'capacitor_bank_controller') return null
  const latest = compensationCapacitorBankTelemetry.value
  const configuredTotal = (
    (compensationCapacitorBankControlProfile.value?.common_output_circuit_count || 0)
    + (compensationCapacitorBankControlProfile.value?.split_output_circuit_count || 0)
  )
  const runningCount = countActiveBits(latest?.circuit_state_phase_a)
    + countActiveBits(latest?.circuit_state_phase_b)
    + countActiveBits(latest?.circuit_state_phase_c)
    + countActiveBits(latest?.circuit_state_common_1)
    + countActiveBits(latest?.circuit_state_common_2)
    + countActiveBits(latest?.circuit_state_common_3)
  const totalCount = configuredTotal > 0 ? configuredTotal : 24
  const hasRealtimeState = [
    latest?.circuit_state_phase_a,
    latest?.circuit_state_phase_b,
    latest?.circuit_state_phase_c,
    latest?.circuit_state_common_1,
    latest?.circuit_state_common_2,
    latest?.circuit_state_common_3,
  ].some((item) => item != null)
  return {
    runningCount,
    totalCount,
    hasRealtimeState,
    source: hasRealtimeState ? '投切回路回读' : '估算/占位',
  }
})

const isDeviceActive = computed(() => runtimeStatus.value?.is_active ?? false)
const toggleActionLabel = computed(() => (isDeviceActive.value ? '停止设备' : '启动设备'))
const toggleButtonType = computed(() => (isDeviceActive.value ? 'danger' : 'success'))
const timelineHours = computed(() => {
  const [start, end] = timeRange.value || defaultTimeRange()
  return Math.max(1, Math.ceil((end.getTime() - start.getTime()) / (60 * 60 * 1000)))
})

const fallbackCompensation = computed(() => {
  const tel = compensationSvgTelemetry.value
  const prof = compensationSvgProfile.value
  const capTel = compensationCapacitorBankTelemetry.value
  const capMode = resolveCapBankControlMode()
  const totalModuleCount = isSvgDevice.value
    ? (prof?.module_count ?? 8)
    : (capacitorBankCircuitSummary.value?.totalCount ?? 24)
  const ratedCapacity = Number(archive.value?.rated_capacity || 0)
  const reactivePower = realtime.value?.reactive_power
  let usage = 0
  let usageSource = '演示占位'
  let usageState: 'live' | 'mock' | 'missing' = 'mock'
  if (isSvgDevice.value && tel?.capacity_utilization != null) {
    usage = tel.capacity_utilization
    usageSource = '遥测回读'
    usageState = 'live'
  } else if (!isSvgDevice.value && capacitorBankCircuitSummary.value?.hasRealtimeState) {
    usage = Math.min(
      100,
      Math.max(
        0,
        (capacitorBankCircuitSummary.value.runningCount / Math.max(1, capacitorBankCircuitSummary.value.totalCount)) * 100,
      ),
    )
    usageSource = '按投切回路回读换算'
    usageState = 'live'
  } else if (ratedCapacity > 0 && reactivePower !== null && reactivePower !== undefined) {
    usage = Math.min(100, Math.max(0, (Math.abs(reactivePower) / ratedCapacity) * 100))
    usageSource = '按额定容量估算'
    usageState = 'mock'
  }

  const runningModuleCount = isSvgDevice.value
    ? Math.round((usage / 100) * totalModuleCount)
    : (capacitorBankCircuitSummary.value?.runningCount ?? 0)

  const cabinetTemperature = isSvgDevice.value
    ? (tel?.cabinet_temp ?? realtime.value?.temperature ?? null)
    : (capTel?.temperature ?? realtime.value?.temperature ?? null)
  const cabinetTemperatureSource = cabinetTemperature == null ? '当前缺测' : '实时采集'
  const controlMode = isSvgDevice.value
    ? (tel?.auto_mode === true ? '自动' : tel?.auto_mode === false ? '手动' : '待确认')
    : capMode.value
  const controlModeSource = isSvgDevice.value
    ? (tel?.auto_mode != null ? '遥测回读' : '估算/占位')
    : capMode.source
  const controlModeState = isSvgDevice.value
    ? (tel?.auto_mode != null ? 'live' : 'mock')
    : capMode.state
  const controlSource = controlMode === '自动' ? 'EMS 自动策略' : controlMode === '手动' ? '现场手动' : '待确认'

  return {
    controlMode,
    controlModeSource,
    controlModeState,
    runningModuleCount,
    totalModuleCount,
    compensationCapacityUsage: usage,
    capacityUsageSource: usageSource,
    capacityUsageState: usageState,
    controlSource,
    switchPermission: canControlDevices.value && runtimeStatus.value?.is_online !== false,
    cabinetTemperature,
    cabinetTemperatureSource,
    targetPowerFactor: 0.98,
    dailySwitchCount: 12,
    hourlySwitchCount: 2,
    thd: 3.2,
    runningHours: 3280,
  }
})

const compensationStatusText = computed(() => {
  const pf = realtime.value?.power_factor
  if (!runtimeStatus.value?.is_online) return '离线'
  if (pf === null || pf === undefined) return '待判断'
  if (pf < 0.9) return '欠补偿'
  if (pf > 0.99) return '过补偿'
  return '正常补偿'
})

const compensationStatusTone = computed<CompensationTone>(() => {
  if (!runtimeStatus.value?.is_online) return 'neutral'
  if (compensationStatusText.value === '欠补偿') return 'warning'
  if (compensationStatusText.value === '过补偿') return 'danger'
  if (compensationStatusText.value === '正常补偿') return 'success'
  return 'info'
})

const compensationHeaderModel = computed<CompensationHeaderModel>(() => ({
  title: archive.value?.name || '补偿器1',
  serial: archive.value?.sn || 'SN2323',
  location: archive.value?.location || '未配置安装位置',
  deviceStatus: runtimeStatus.value?.label || statusText(runtimeStatus.value?.is_online, '运行状态未知'),
  deviceStatusTone: runtimeStatus.value?.is_online ? 'info' : 'neutral',
  tags: [
    {
      label: `${fallbackCompensation.value.controlMode} · ${fallbackCompensation.value.controlModeSource}`,
      tone: fallbackCompensation.value.controlModeState === 'live'
        ? (fallbackCompensation.value.controlMode === '自动' ? 'info' : 'warning')
        : 'warning',
    },
    {
      label: compensationStatusText.value,
      tone: compensationStatusTone.value,
    },
  ],
}))

const hasReactivePowerField = computed(() =>
  Object.prototype.hasOwnProperty.call(realtime.value || {}, 'reactive_power'),
)

const compensationReactiveHint = computed(() => {
  if (!hasReactivePowerField.value) return '当前接口未返回无功功率字段'
  if (realtime.value?.reactive_power === null) return '当前无实时无功功率数据'
  return '实时采集值'
})

const compensationCoreMetric = computed<CompensationMetric>(() => ({
  key: 'reactivePower',
  label: '当前无功功率',
  value: displayValueWithState(realtime.value?.reactive_power, '暂无数据'),
  unit: 'kVar',
  hint: compensationReactiveHint.value,
  state: realtime.value?.reactive_power === null || realtime.value?.reactive_power === undefined ? 'missing' : 'live',
  emphasized: true,
}))

const compensationPfMetric = computed<CompensationMetric>(() => ({
  key: 'powerFactor',
  label: '功率因数',
  value: displayValueWithState(realtime.value?.power_factor, '暂无数据', 2),
  unit: '',
  hint: realtime.value?.power_factor == null ? '实时值缺失' : `目标 PF ${fallbackCompensation.value.targetPowerFactor.toFixed(2)}`,
  tone: compensationStatusTone.value,
  state: realtime.value?.power_factor == null ? 'missing' : 'live',
  emphasized: true,
}))

const compensationMetrics = computed<CompensationMetric[]>(() => {
  const temperature = fallbackCompensation.value.cabinetTemperature
  return [
    {
      key: 'busVoltage',
      label: '母线电压',
      value: displayValueWithState(realtime.value?.voltage, '通讯中断'),
      unit: 'V',
      hint: realtime.value?.voltage == null ? '实时电压未采集' : '当前母线测量值',
      state: realtime.value?.voltage == null ? 'missing' : 'live',
    },
    {
      key: 'lineCurrent',
      label: '线电流',
      value: displayValueWithState(realtime.value?.current, '通讯中断'),
      unit: 'A',
      hint: realtime.value?.current == null ? '实时电流未采集' : '当前线电流测量值',
      state: realtime.value?.current == null ? 'missing' : 'live',
    },
    {
      key: 'activePower',
      label: '有功功率',
      value: displayValueWithState(realtime.value?.flow_rate, '暂无数据'),
      unit: 'kW',
      hint: realtime.value?.flow_rate == null ? '实时有功功率未采集' : '当前柜体有功功率',
      state: realtime.value?.flow_rate == null ? 'missing' : 'live',
    },
    {
      key: 'capacityUsage',
      label: '补偿容量利用率',
      value: `${fallbackCompensation.value.compensationCapacityUsage.toFixed(1)}`,
      unit: '%',
      hint: fallbackCompensation.value.capacityUsageSource,
      tone: fallbackCompensation.value.compensationCapacityUsage >= 90 ? 'warning' : 'success',
      state: fallbackCompensation.value.capacityUsageState,
    },
    {
      key: 'controlMode',
      label: '控制模式',
      value: fallbackCompensation.value.controlMode,
      unit: '',
      hint: fallbackCompensation.value.controlModeSource,
      tone: fallbackCompensation.value.controlMode === '自动' ? 'info' : 'warning',
      state: fallbackCompensation.value.controlModeState,
    },
    {
      key: 'cabinetTemperature',
      label: '柜内温度',
      value: displayValueWithState(temperature, '暂无数据'),
      unit: '°C',
      hint: temperature == null
        ? fallbackCompensation.value.cabinetTemperatureSource
        : temperature >= 45
          ? `温度偏高，请关注通风散热 · ${fallbackCompensation.value.cabinetTemperatureSource}`
          : temperature >= 40
            ? `温度轻微预警 · ${fallbackCompensation.value.cabinetTemperatureSource}`
            : `柜内温度正常 · ${fallbackCompensation.value.cabinetTemperatureSource}`,
      tone: temperature == null ? 'neutral' : temperature >= 45 ? 'danger' : temperature >= 40 ? 'warning' : 'success',
      state: temperature == null ? 'missing' : 'live',
    },
  ]
})

const moduleStatusModel = computed<ModuleStatusModel>(() => {
  if (compensationSubtype.value === 'capacitor_bank_controller' && capacitorBankCircuitSummary.value) {
    const totalCount = Math.max(1, capacitorBankCircuitSummary.value.totalCount)
    const runningCount = Math.max(0, Math.min(totalCount, capacitorBankCircuitSummary.value.runningCount))
    const moduleStates: ModuleStateTone[] = Array.from({ length: totalCount }, (_, index) =>
      index < runningCount ? 'running' : 'standby',
    )
    return {
      title: '回路投切状态',
      unitLabel: compensationUnitLabel.value,
      runningModuleCount: runningCount,
      totalModuleCount: totalCount,
      moduleStates,
      hint: capacitorBankCircuitSummary.value.hasRealtimeState
        ? '根据最新回路投切寄存器回读统计当前投入回路数。'
        : '当前未获取到回路投切寄存器，暂按默认回路数展示待机态。',
    }
  }
  const runningCount = Math.max(
    0,
    Math.min(fallbackCompensation.value.totalModuleCount, fallbackCompensation.value.runningModuleCount),
  )
  const totalCount = Math.max(runningCount, fallbackCompensation.value.totalModuleCount)
  const moduleStates: ModuleStateTone[] = Array.from({ length: totalCount }, (_, index) =>
    index < runningCount ? 'running' : 'standby',
  )

  const alarmIndex = totalCount - 2
  const faultIndex = totalCount - 1

  if (compensationSvgTelemetry.value?.overtemp_fault || compensationSvgTelemetry.value?.overcurrent_fault) {
    moduleStates[Math.max(runningCount, alarmIndex)] = 'alarm'
  }
  if (compensationSvgTelemetry.value?.module_fault) {
    moduleStates[Math.max(runningCount, faultIndex)] = 'fault'
  }

  return {
    title: isSvgDevice.value ? '模块运行状态' : '回路投切状态',
    unitLabel: compensationUnitLabel.value,
    runningModuleCount: moduleStates.filter((state) => state === 'running').length,
    totalModuleCount: totalCount,
    moduleStates,
    hint: compensationSvgTelemetry.value?.module_fault
      ? '红色表示模块故障，黄色表示模块告警，绿色表示运行，灰色表示待机。'
      : '绿色表示运行，灰色表示待机，黄色表示告警，红色表示故障。',
  }
})

const compensationExtendedHint = computed(() => {
  const messages: string[] = []
  if (fallbackCompensation.value.capacityUsageState !== 'live') {
    messages.push(`补偿容量利用率当前来源：${fallbackCompensation.value.capacityUsageSource}。`)
  }
  if (fallbackCompensation.value.controlModeState !== 'live') {
    messages.push(`控制模式当前来源：${fallbackCompensation.value.controlModeSource}。`)
  }
  if (fallbackCompensation.value.cabinetTemperature == null) {
    messages.push('柜内温度当前缺测，暂不展示默认温度。')
  }
  if (!isSvgDevice.value) messages.push('当前已接入 JKWF-LCD 专属快照与历史曲线，可查看三相功率、谐波与投切回放。')
  return messages.join(' ')
})

const capacitorBankHistoryLabels = computed(() => {
  const points = compensationCapacitorBankTelemetryHistory.value || []
  return points.map((point) => toShortTime(point.timestamp))
})

function hasCapBankHistoryValue(key: keyof CompensationCapacitorBankTelemetry) {
  return compensationCapacitorBankTelemetryHistory.value.some((point) => point[key] != null)
}

function buildCapBankSeries(
  keys: Array<keyof CompensationCapacitorBankTelemetry>,
): Array<Array<number | null>> {
  return keys.map((key) =>
    compensationCapacitorBankTelemetryHistory.value.map((point) => {
      const value = point[key]
      return typeof value === 'number' ? value : null
    }),
  )
}

function buildCapBankSwitchingSeries(key: keyof CompensationCapacitorBankTelemetry): Array<number | null> {
  return compensationCapacitorBankTelemetryHistory.value.map((point) => {
    const value = point[key]
    if (typeof value !== 'number') return null
    let count = 0
    for (let i = 0; i < 8; i += 1) {
      if (value & (1 << i)) count += 1
    }
    return count
  })
}

function summaryNumber(value: number | null | undefined, unit = '', digits = 1) {
  const displayed = displayValueWithState(value, '暂无数据', digits)
  return unit ? `${displayed} ${unit}` : displayed
}

const compensationTrendModel = computed<CompensationTrendModel>(() => {
  const labels = buildTrendLabels()
  if (compensationTrendTab.value === 'effect') {
    const points = trend.value?.points || []
    const hasRealQ = points.some((p) => p.reactive_power != null)
    const hasRealPf = points.some((p) => p.power_factor != null)
    const hasHistory = hasRealQ || hasRealPf
    const qSeries = points.map((p) => p.reactive_power ?? null)
    const pfSeries = points.map((p) => p.power_factor ?? null)
    return {
      labels,
      legend: ['无功功率 Q', '功率因数 PF'],
      axes: [
        { name: 'kVar' },
        { name: 'PF', min: 0.8, max: 1, position: 'right' },
      ],
      series: [
        { name: '无功功率 Q', data: qSeries, color: '#38bdf8', area: true },
        { name: '功率因数 PF', data: pfSeries, color: '#4ade80', yAxisIndex: 1 },
      ],
      summary: [
        { label: '当前 Q', value: `${displayValueWithState(realtime.value?.reactive_power, '暂无数据')} kVar` },
        { label: '当前 PF', value: compensationPfMetric.value.value },
        { label: '目标 PF', value: archive.value?.rated_capacity ? fallbackCompensation.value.targetPowerFactor.toFixed(2) : '暂无数据' },
      ],
      empty: !hasHistory,
      emptyText: '暂无补偿效果趋势数据',
      hint: hasHistory ? '展示历史采集的无功功率与功率因数走势。' : '当前时间范围内没有补偿效果历史数据。',
      isMock: false,
    }
  }

  if (compensationSubtype.value === 'capacitor_bank_controller' && compensationTrendTab.value === 'phase_power') {
    const histLabels = capacitorBankHistoryLabels.value
    const hasHistory = hasCapBankHistoryValue('reactive_power_a')
      || hasCapBankHistoryValue('active_power_a')
      || hasCapBankHistoryValue('power_factor_a')
    const [activeA, activeB, activeC] = buildCapBankSeries(['active_power_a', 'active_power_b', 'active_power_c'])
    const [reactiveA, reactiveB, reactiveC] = buildCapBankSeries(['reactive_power_a', 'reactive_power_b', 'reactive_power_c'])
    const [pfA, pfB, pfC] = buildCapBankSeries(['power_factor_a', 'power_factor_b', 'power_factor_c'])
    return {
      labels: histLabels,
      legend: ['A相有功', 'B相有功', 'C相有功', 'A相无功', 'B相无功', 'C相无功', 'A相PF', 'B相PF', 'C相PF'],
      axes: [
        { name: 'kW / kvar' },
        { name: 'PF', min: 0.8, max: 1, position: 'right' },
      ],
      series: [
        { name: 'A相有功', data: activeA, color: '#38bdf8' },
        { name: 'B相有功', data: activeB, color: '#60a5fa' },
        { name: 'C相有功', data: activeC, color: '#93c5fd' },
        { name: 'A相无功', data: reactiveA, color: '#22c55e' },
        { name: 'B相无功', data: reactiveB, color: '#4ade80' },
        { name: 'C相无功', data: reactiveC, color: '#86efac' },
        { name: 'A相PF', data: pfA, color: '#f59e0b', yAxisIndex: 1 },
        { name: 'B相PF', data: pfB, color: '#fbbf24', yAxisIndex: 1 },
        { name: 'C相PF', data: pfC, color: '#fcd34d', yAxisIndex: 1 },
      ],
      summary: [
        { label: 'A相有功', value: summaryNumber(compensationCapacitorBankTelemetry.value?.active_power_a, 'kW') },
        { label: 'B相无功', value: summaryNumber(compensationCapacitorBankTelemetry.value?.reactive_power_b, 'kvar') },
        { label: 'C相PF', value: summaryNumber(compensationCapacitorBankTelemetry.value?.power_factor_c, '', 3) },
      ],
      empty: !hasHistory,
      emptyText: '暂无三相功率历史数据',
      hint: hasHistory ? '展示电容控制器三相有功、无功与功率因数历史走势。' : '当前时间范围内没有三相功率历史数据。',
      isMock: false,
    }
  }

  if (compensationSubtype.value === 'capacitor_bank_controller' && compensationTrendTab.value === 'phase_voltage') {
    const hasHistory = hasCapBankHistoryValue('voltage_a')
    const [a, b, c] = buildCapBankSeries(['voltage_a', 'voltage_b', 'voltage_c'])
    return {
      labels: capacitorBankHistoryLabels.value,
      legend: ['A相电压', 'B相电压', 'C相电压'],
      axes: [{ name: 'V' }],
      series: [
        { name: 'A相电压', data: a, color: '#38bdf8' },
        { name: 'B相电压', data: b, color: '#60a5fa' },
        { name: 'C相电压', data: c, color: '#93c5fd' },
      ],
      summary: [
        { label: 'A相电压', value: summaryNumber(compensationCapacitorBankTelemetry.value?.voltage_a, 'V') },
        { label: 'B相电压', value: summaryNumber(compensationCapacitorBankTelemetry.value?.voltage_b, 'V') },
        { label: 'C相电压', value: summaryNumber(compensationCapacitorBankTelemetry.value?.voltage_c, 'V') },
      ],
      empty: !hasHistory,
      emptyText: '暂无三相电压历史数据',
      hint: hasHistory ? '展示三相母线电压的专属历史曲线。' : '当前时间范围内没有三相电压历史数据。',
      isMock: false,
    }
  }

  if (compensationSubtype.value === 'capacitor_bank_controller' && compensationTrendTab.value === 'phase_current') {
    const hasHistory = hasCapBankHistoryValue('current_a')
    const [a, b, c] = buildCapBankSeries(['current_a', 'current_b', 'current_c'])
    return {
      labels: capacitorBankHistoryLabels.value,
      legend: ['A相电流', 'B相电流', 'C相电流'],
      axes: [{ name: 'A' }],
      series: [
        { name: 'A相电流', data: a, color: '#f59e0b' },
        { name: 'B相电流', data: b, color: '#fbbf24' },
        { name: 'C相电流', data: c, color: '#fcd34d' },
      ],
      summary: [
        { label: 'A相电流', value: summaryNumber(compensationCapacitorBankTelemetry.value?.current_a, 'A') },
        { label: 'B相电流', value: summaryNumber(compensationCapacitorBankTelemetry.value?.current_b, 'A') },
        { label: 'C相电流', value: summaryNumber(compensationCapacitorBankTelemetry.value?.current_c, 'A') },
      ],
      empty: !hasHistory,
      emptyText: '暂无三相电流历史数据',
      hint: hasHistory ? '展示三相线电流的专属历史曲线。' : '当前时间范围内没有三相电流历史数据。',
      isMock: false,
    }
  }

  if (compensationSubtype.value === 'capacitor_bank_controller' && compensationTrendTab.value === 'harmonic') {
    const hasHistory = hasCapBankHistoryValue('voltage_thd_a') || hasCapBankHistoryValue('current_harmonic_a')
    const [vA, vB, vC] = buildCapBankSeries(['voltage_thd_a', 'voltage_thd_b', 'voltage_thd_c'])
    const [iA, iB, iC] = buildCapBankSeries(['current_harmonic_a', 'current_harmonic_b', 'current_harmonic_c'])
    return {
      labels: capacitorBankHistoryLabels.value,
      legend: ['A相电压THD', 'B相电压THD', 'C相电压THD', 'A相谐波电流', 'B相谐波电流', 'C相谐波电流'],
      axes: [
        { name: '%' },
        { name: 'A', position: 'right' },
      ],
      series: [
        { name: 'A相电压THD', data: vA, color: '#fb7185', area: true },
        { name: 'B相电压THD', data: vB, color: '#f43f5e', area: true },
        { name: 'C相电压THD', data: vC, color: '#e11d48', area: true },
        { name: 'A相谐波电流', data: iA, color: '#22c55e', yAxisIndex: 1 },
        { name: 'B相谐波电流', data: iB, color: '#4ade80', yAxisIndex: 1 },
        { name: 'C相谐波电流', data: iC, color: '#86efac', yAxisIndex: 1 },
      ],
      summary: [
        { label: 'A相THD', value: summaryNumber(compensationCapacitorBankTelemetry.value?.voltage_thd_a, '%') },
        { label: 'B相谐波电流', value: summaryNumber(compensationCapacitorBankTelemetry.value?.current_harmonic_b, 'A') },
        { label: '温度告警', value: compensationCapacitorBankTelemetry.value?.temp_alarm ? '告警中' : '正常' },
      ],
      empty: !hasHistory,
      emptyText: '暂无谐波历史数据',
      hint: hasHistory ? '展示三相电压 THD 与谐波电流历史走势。' : '当前时间范围内没有谐波历史数据。',
      isMock: false,
    }
  }

  if (compensationSubtype.value === 'capacitor_bank_controller' && compensationTrendTab.value === 'switching') {
    const hasHistory = hasCapBankHistoryValue('circuit_state_phase_a') || hasCapBankHistoryValue('circuit_state_common_1')
    const phaseA = buildCapBankSwitchingSeries('circuit_state_phase_a')
    const phaseB = buildCapBankSwitchingSeries('circuit_state_phase_b')
    const phaseC = buildCapBankSwitchingSeries('circuit_state_phase_c')
    const common = buildCapBankSwitchingSeries('circuit_state_common_1')
    return {
      labels: capacitorBankHistoryLabels.value,
      legend: ['A相投入路数', 'B相投入路数', 'C相投入路数', '公补投入路数'],
      axes: [{ name: '路数', min: 0 }],
      series: [
        { name: 'A相投入路数', data: phaseA, color: '#38bdf8' },
        { name: 'B相投入路数', data: phaseB, color: '#60a5fa' },
        { name: 'C相投入路数', data: phaseC, color: '#93c5fd' },
        { name: '公补投入路数', data: common, color: '#f59e0b' },
      ],
      summary: [
        { label: 'A相分补', value: summaryNumber(compensationCapacitorBankTelemetry.value?.circuit_state_phase_a, '', 0) },
        { label: '公补 1-8', value: summaryNumber(compensationCapacitorBankTelemetry.value?.circuit_state_common_1, '', 0) },
        { label: '当前采样', value: formatDateTime(compensationCapacitorBankTelemetry.value?.timestamp) },
      ],
      empty: !hasHistory,
      emptyText: '暂无投切历史数据',
      hint: hasHistory ? '按历史寄存器变化估算各组投入路数，用于回看投切节奏。' : '当前时间范围内没有投切回放历史数据。',
      isMock: false,
    }
  }

  if (compensationTrendTab.value === 'voltage') {
    const voltageSeries = buildTrendSeriesFromPoints('voltage')
    return trendModelFromSingleSeries({
      labels,
      name: '母线电压',
      unit: 'V',
      color: '#60a5fa',
      values: voltageSeries.values,
      summaryItems: [
        { label: '当前电压', value: `${displayValueWithState(realtime.value?.voltage, '暂无数据')} V` },
        { label: '峰值', value: `${displayValueWithState(voltageSeries.peak, '暂无数据')} V` },
        { label: '谷值', value: `${displayValueWithState(voltageSeries.valley, '暂无数据')} V` },
      ],
      isMock: voltageSeries.isMock,
      hint: voltageSeries.isMock ? '当前时间范围内没有母线电压历史数据。' : '展示最近时间范围内的母线电压走势。',
      emptyText: '暂无电压趋势数据',
    })
  }

  if (compensationTrendTab.value === 'current') {
    const currentSeries = buildTrendSeriesFromPoints('current')
    return trendModelFromSingleSeries({
      labels,
      name: '线电流',
      unit: 'A',
      color: '#f59e0b',
      values: currentSeries.values,
      summaryItems: [
        { label: '当前电流', value: `${displayValueWithState(realtime.value?.current, '暂无数据')} A` },
        { label: '峰值', value: `${displayValueWithState(currentSeries.peak, '暂无数据')} A` },
        { label: '谷值', value: `${displayValueWithState(currentSeries.valley, '暂无数据')} A` },
      ],
      isMock: currentSeries.isMock,
      hint: currentSeries.isMock ? '当前时间范围内没有线电流历史数据。' : '展示最近时间范围内的线电流走势。',
      emptyText: '暂无电流趋势数据',
    })
  }

  const svgHistPoints = compensationSvgTelemetryHistory.value
  const capHistPoints = compensationCapacitorBankTelemetryHistory.value
  const hasCabinetTemp = isSvgDevice.value
    ? svgHistPoints.some((p) => p.cabinet_temp != null)
    : capHistPoints.some((p) => p.temperature != null)
  const healthLabels = hasCabinetTemp
    ? (isSvgDevice.value
      ? svgHistPoints.map((p) => toShortTime(p.timestamp))
      : capHistPoints.map((p) => toShortTime(p.timestamp)))
    : labels
  const healthTemp = hasCabinetTemp
    ? (isSvgDevice.value
      ? svgHistPoints.map((p) => p.cabinet_temp ?? null)
      : capHistPoints.map((p) => p.temperature ?? null))
    : []
  const healthFrequency = !isSvgDevice.value && capHistPoints.some((p) => p.frequency != null)
    ? capHistPoints.map((p) => p.frequency ?? null)
    : []
  const healthScore: Array<number | null> = []
  const svgTempDetails = isSvgDevice.value
    ? [
        { label: '模块温度', value: summaryNumber(compensationSvgTelemetry.value?.module_temp, '°C') },
        { label: 'IGBT 温度', value: summaryNumber(compensationSvgTelemetry.value?.igbt_temp, '°C') },
        { label: '散热器温度', value: summaryNumber(compensationSvgTelemetry.value?.heatsink_temp, '°C') },
      ]
    : []
  const hasHealthData = hasCabinetTemp || healthFrequency.length > 0
  return {
    labels: healthLabels,
    legend: !isSvgDevice.value && healthFrequency.length ? ['柜内温度', '频率'] : ['柜内温度'],
    axes: [
      { name: '°C' },
      { name: !isSvgDevice.value && healthFrequency.length ? 'Hz' : '', min: !isSvgDevice.value && healthFrequency.length ? 49 : 0, max: !isSvgDevice.value && healthFrequency.length ? 100 : 100, position: 'right' },
    ],
    series: [
      { name: '柜内温度', data: healthTemp, color: '#fb7185', area: true },
      ...(!isSvgDevice.value && healthFrequency.length
        ? [{ name: '频率', data: healthFrequency, color: '#60a5fa', yAxisIndex: 1 } as const]
        : []),
    ],
    summary: [
      { label: '柜内温度', value: `${displayValueWithState(isSvgDevice.value ? compensationSvgTelemetry.value?.cabinet_temp : compensationCapacitorBankTelemetry.value?.temperature, '暂无数据')} °C` },
      { label: !isSvgDevice.value ? '电网频率' : '模块温度', value: !isSvgDevice.value ? summaryNumber(compensationCapacitorBankTelemetry.value?.frequency, 'Hz', 2) : summaryNumber(compensationSvgTelemetry.value?.module_temp, '°C') },
      ...(isSvgDevice.value ? svgTempDetails : []),
    ],
    empty: !hasHealthData,
    emptyText: '暂无温度与健康度趋势数据',
    hint: hasHealthData ? (isSvgDevice.value ? '展示采集的柜内及核心器件温度历史走势。' : '展示柜内温度与频率历史走势。') : '当前时间范围内没有温度或频率历史数据。',
    isMock: false,
  }
})

const compensationEvents = computed<CompensationEventItem[]>(() => {
  if (statusHistory.value.length) {
    return statusHistory.value.slice(0, 6).map((item) => ({
      time: formatTimeOnly(item.timestamp),
      title: item.title,
      detail: item.detail || '无附加说明',
      tone: historyTone(item.status, item.event_type),
      tag: historyTag(item.status),
    }))
  }

  return [
    {
      time: '--:--',
      title: '当前时间范围内暂无真实运行事件',
      detail: '尚未采集到补偿器控制/告警事件，页面不再用示例事件替代真实记录。',
      tone: 'info',
      tag: '待采集',
      isMock: true,
    },
  ]
})

const compensationStatusItems = computed<CompensationStatusItem[]>(() => {
  const tel = compensationSvgTelemetry.value
  const capTel = compensationCapacitorBankTelemetry.value
  const items: CompensationStatusItem[] = [
    {
      label: '技术类型',
      value: compensationSubtypeLabel.value || '未定义',
      tone: 'info',
    },
    {
      label: '设备状态',
      value: runtimeStatus.value?.label || '状态未知',
      tone: runtimeStatus.value?.is_active ? 'success' : 'warning',
    },
    {
      label: '在线状态',
      value: runtimeStatus.value?.is_online ? '在线' : '离线',
      tone: runtimeStatus.value?.is_online ? 'info' : 'neutral',
    },
    {
      label: '采集状态',
      value: formatIngestionStatus(runtimeStatus.value?.ingestion_status),
      tone: ingestionTone(runtimeStatus.value?.ingestion_status),
      hint: '来自 monitor/runtime-status 的接入健康判定',
    },
    {
      label: '当前模式',
      value: fallbackCompensation.value.controlMode,
      tone: fallbackCompensation.value.controlMode === '自动' ? 'info' : 'warning',
      hint: fallbackCompensation.value.controlModeSource,
    },
    {
      label: '未处理告警',
      value: `${runtimeStatus.value?.unresolved_alarm_count ?? 0} 条`,
      tone: (runtimeStatus.value?.unresolved_alarm_count || 0) > 0 ? 'warning' : 'success',
    },
    {
      label: '控制来源',
      value: fallbackCompensation.value.controlSource,
      tone: 'info',
    },
    {
      label: '容量利用率来源',
      value: fallbackCompensation.value.capacityUsageSource,
      tone: fallbackCompensation.value.capacityUsageState === 'live' ? 'success' : 'warning',
    },
    {
      label: '温度来源',
      value: fallbackCompensation.value.cabinetTemperatureSource,
      tone: fallbackCompensation.value.cabinetTemperature != null ? 'success' : 'warning',
    },
    {
      label: '最近采样',
      value: formatDateTime(isSvgDevice.value ? tel?.timestamp : capTel?.timestamp),
      tone: 'info',
      hint: '来自补偿设备专属 latest 快照',
    },
      {
        label: '是否允许投切',
        value: fallbackCompensation.value.switchPermission ? '允许投切' : '禁止投切',
        tone: fallbackCompensation.value.switchPermission ? 'success' : 'danger',
        hint: canControlDevices.value ? '基于当前权限与在线状态判定' : '当前账号无设备控制权限',
    },
  ]
  if (tel) {
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
        value: formatBooleanStatus(tel.run_status, '运行', '未运行'),
        tone: tel.run_status === true ? 'success' : tel.run_status === false ? 'neutral' : 'info',
      },
      {
        label: '停机反馈',
        value: formatBooleanStatus(tel.stop_status, '已停机', '未停机'),
        tone: tel.stop_status === true ? 'warning' : tel.stop_status === false ? 'success' : 'neutral',
      },
      {
        label: '就地模式',
        value: formatBooleanStatus(tel.local_mode, '就地', '远程'),
        tone: tel.local_mode === true ? 'warning' : tel.local_mode === false ? 'info' : 'neutral',
      },
      {
        label: '通讯状态',
        value: formatBooleanStatus(tel.comm_status, '通讯正常', '通讯异常'),
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
    items.push({
      label: '当前故障',
      value: faults.length > 0 ? faults.join(' / ') : '无故障',
      tone: faults.length > 0 ? 'danger' : 'success',
    })
    items.push(
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
        value: `${displayValueWithState(tel.cabinet_temp, '暂无数据')} °C / ${displayValueWithState(tel.module_temp, '暂无数据')} °C`,
        tone: temperatureTone(tel.cabinet_temp, tel.module_temp),
      },
      {
        label: 'IGBT / 散热器温度',
        value: `${displayValueWithState(tel.igbt_temp, '暂无数据')} °C / ${displayValueWithState(tel.heatsink_temp, '暂无数据')} °C`,
        tone: temperatureTone(tel.igbt_temp, tel.heatsink_temp),
      },
    )
  } else if (capTel) {
    const capFlags = [
      capTel.leading_a && 'A超前',
      capTel.leading_b && 'B超前',
      capTel.leading_c && 'C超前',
      capTel.temp_alarm && '温度告警',
      capTel.overvoltage_alarm_a && 'A相过压',
      capTel.overvoltage_alarm_b && 'B相过压',
      capTel.overvoltage_alarm_c && 'C相过压',
    ].filter(Boolean) as string[]
    items.push(
      {
        label: '参数快照',
        value: compensationCapacitorBankControlProfile.value?.source_status === 'fresh'
          ? '最新参数'
          : compensationCapacitorBankControlProfile.value?.source_status === 'stale'
            ? '参数可能过期'
            : compensationCapacitorBankControlProfile.value?.source_status === 'empty'
              ? '暂无参数'
              : '状态未知',
        tone: compensationCapacitorBankControlProfile.value?.source_status === 'fresh'
          ? 'success'
          : compensationCapacitorBankControlProfile.value?.source_status === 'stale'
            ? 'warning'
            : 'neutral',
        hint: '来自控制器参数回读档案',
      },
      {
        label: '控制策略',
        value: '按功率因数自动投切',
        tone: 'info',
        hint: '适用于 JKWF 等传统电容补偿控制器的常见控制方式',
      },
      {
        label: '回路状态',
        value: `${moduleStatusModel.value.runningModuleCount} / ${moduleStatusModel.value.totalModuleCount} 回路投入`,
        tone: moduleStatusModel.value.runningModuleCount > 0 ? 'success' : 'warning',
      },
      {
        label: '频率 / 温度',
        value: `${displayValueWithState(capTel.frequency, '暂无数据', 2)} Hz / ${displayValueWithState(capTel.temperature, '暂无数据')} °C`,
        tone: capTel.temp_alarm ? 'warning' : 'info',
      },
      {
        label: '当前标志',
        value: capFlags.length ? capFlags.join(' / ') : '无异常标志',
        tone: capFlags.length ? 'warning' : 'success',
      },
    )
  } else if (!isSvgDevice.value) {
    items.push(
      {
        label: '控制策略',
        value: '按功率因数自动投切',
        tone: 'info',
        hint: '适用于 JKWF 等传统电容补偿控制器的常见控制方式',
      },
      {
        label: '回路状态',
        value: `${moduleStatusModel.value.runningModuleCount} / ${moduleStatusModel.value.totalModuleCount} 回路投入`,
        tone: moduleStatusModel.value.runningModuleCount > 0 ? 'success' : 'warning',
      },
    )
  }
  return items
})

const compensationProfileItems = computed<CompensationProfileItem[]>(() => {
  const prof = compensationSvgProfile.value
  const items: CompensationProfileItem[] = [
    { label: '设备名称', value: archive.value?.name || '补偿器1' },
    { label: '序列号', value: archive.value?.sn || 'SN2323' },
    { label: '设备分类', value: compensationCategoryLabel.value || '无功功率补偿设备' },
    { label: '技术类型', value: compensationSubtypeLabel.value || '未定义' },
    { label: '能源类型', value: archive.value?.energy_type || '电' },
    { label: '安装位置', value: archive.value?.location || '未配置安装位置' },
    { label: '额定容量', value: archive.value?.rated_capacity ? `${archive.value.rated_capacity} kVar` : '未配置' },
    { label: '描述', value: archive.value?.description || '用于无功补偿与功率因数优化的柜体设备。' },
  ]
  if (prof) {
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
  }
  return items
})

const capacitorBankControlSummaryItems = computed(() =>
  capacitorBankControlParameterMeta
    .filter((item) => item.summary)
    .map((item) => ({
      label: item.label,
      value: formatCapacitorBankControlValue(compensationCapacitorBankControlProfile.value, item),
    })),
)

const genericStatusItems = computed(() => [
  { label: '设备状态', value: runtimeStatus.value?.label || '状态未知' },
  { label: '在线状态', value: runtimeStatus.value?.is_online ? '在线' : '离线' },
  {
    label: '采集状态',
    value: formatIngestionStatus(runtimeStatus.value?.ingestion_status),
    hint: '聚合接入健康状态',
  },
  { label: '未处理告警', value: `${runtimeStatus.value?.unresolved_alarm_count ?? 0} 条` },
  { label: '最近消息', value: formatDateTime(runtimeStatus.value?.last_message_at) },
  { label: '最近成功入库', value: formatDateTime(runtimeStatus.value?.last_success_at) },
])

watch(
  () => chart.chartRef.value,
  async () => {
    if (!chart.chartRef.value || isCompensationDevice.value) return
    await chart.initChart()
    await renderTrendChart()
  },
)

watch(
  () => chartMetric.value,
  async () => {
    if (isCompensationDevice.value) return
    await renderTrendChart()
  },
)

watch(
  () => compensationTrendTabs.value.map((item) => item.value),
  (tabs) => {
    if (!tabs.includes(compensationTrendTab.value)) {
      compensationTrendTab.value = tabs[0] || 'effect'
    }
  },
  { immediate: true },
)

async function renderTrendChart() {
  if (isCompensationDevice.value || !trend.value) return

  const points = trend.value.points || []
  const seriesData = points.map((point) => getTrendMetricValue(point, chartMetric.value) ?? 0)

  await chart.setOptions({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 36, 0.95)',
      borderColor: '#314055',
      textStyle: { color: '#e5edf7' },
    },
    grid: { left: 48, right: 16, top: 24, bottom: 28 },
    xAxis: {
      type: 'category',
      data: points.map((point) => toShortTime(point.timestamp)),
      axisLine: { lineStyle: { color: '#314055' } },
      axisLabel: { color: '#8ea0bc', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: chartUnit(chartMetric.value),
      nameTextStyle: { color: '#8ea0bc', padding: [0, 0, 0, 8] },
      axisLabel: { color: '#8ea0bc', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
    },
    series: [
      {
        name: metricLabel(chartMetric.value),
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: seriesData,
        lineStyle: { color: '#38bdf8', width: 2.5 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(56, 189, 248, 0.24)' },
              { offset: 1, color: 'rgba(56, 189, 248, 0)' },
            ],
          },
        },
      },
    ],
  }, { notMerge: true })
}

async function loadTrendAndTables() {
  if (!deviceId.value) return
  chartLoading.value = true
  try {
    const params = buildRangeParams()
    const resolved =
      alarmFilter.value === 'all'
        ? undefined
        : alarmFilter.value === 'resolved'
          ? true
          : false

    const [trendRes, alarmsRes, logsRes] = await Promise.all([
      getDeviceMonitorTrend(deviceId.value, params),
      getDeviceMonitorAlarms(deviceId.value, { ...params, resolved }),
      getDeviceMonitorControlLogs(deviceId.value, params),
    ])

    trend.value = {
      ...trendRes,
      points: [...(trendRes.points || [])].sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      ),
    }
    alarms.value = alarmsRes.items
    controlLogs.value = logsRes.items
    await renderTrendChart()
  } finally {
    chartLoading.value = false
  }
}

async function loadSVGTelemetry() {
  try {
    compensationSvgTelemetry.value = await getCompensationSvgTelemetryLatest(deviceId.value)
  } catch {
    compensationSvgTelemetry.value = null
  }
  try {
    const [start, end] = timeRange.value || defaultTimeRange()
    const records = await getCompensationSvgTelemetryHistory(deviceId.value, {
      start: toApiDate(start),
      end: toApiDate(end),
      limit: 200,
    })
    compensationSvgTelemetryHistory.value = [...records].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    )
  } catch {
    compensationSvgTelemetryHistory.value = []
  }
}

async function loadSVGProfile() {
  try {
    compensationSvgProfile.value = await getCompensationSvgOperationsProfile(deviceId.value)
  } catch {
    compensationSvgProfile.value = null
  }
}

async function loadCapBankTelemetry() {
  try {
    compensationCapacitorBankTelemetry.value = await getCompensationCapacitorBankTelemetryLatest(deviceId.value)
  } catch {
    compensationCapacitorBankTelemetry.value = null
  }
  try {
    const [start, end] = timeRange.value || defaultTimeRange()
    const records = await getCompensationCapacitorBankTelemetryHistory(deviceId.value, {
      start: toApiDate(start),
      end: toApiDate(end),
      limit: 500,
    })
    compensationCapacitorBankTelemetryHistory.value = [...records].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    )
  } catch {
    compensationCapacitorBankTelemetryHistory.value = []
  }
}

async function loadCapBankControlProfile() {
  try {
    compensationCapacitorBankControlProfile.value = await getCompensationCapacitorBankControlProfile(deviceId.value)
  } catch {
    compensationCapacitorBankControlProfile.value = null
  }
}

async function loadPage(showLoading: boolean = true) {
  if (!deviceId.value) return
  if (showLoading) loading.value = true

  try {
    overview.value = await getDeviceMonitorOverview(deviceId.value)
    const extraTasks: Promise<unknown>[] = [loadTrendAndTables(), loadStatusHistory()]
    if (isSvgDevice.value) {
      extraTasks.push(loadSVGTelemetry(), loadSVGProfile())
      compensationCapacitorBankControlProfile.value = null
    }
    if (compensationSubtype.value === 'capacitor_bank_controller') {
      extraTasks.push(loadCapBankTelemetry(), loadCapBankControlProfile())
      compensationSvgProfile.value = null
    }
    if (!isCompensationDevice.value) {
      compensationSvgProfile.value = null
      compensationCapacitorBankControlProfile.value = null
    }
    await Promise.all(extraTasks)
  } catch {
    ElMessage.error('设备监控数据加载失败')
  } finally {
    loading.value = false
  }
}

async function loadStatusHistory() {
  if (!deviceId.value) return
  try {
    const response = await getDeviceMonitorStatusHistory(deviceId.value, {
      hours: Math.min(timelineHours.value, 720),
      limit: 30,
    })
    statusHistory.value = response.items
  } catch {
    // axios 统一处理
  }
}

async function refreshRealtime() {
  if (!deviceId.value || !overview.value) return
  try {
    const [realtimeRes, trendRes] = await Promise.all([
      getDeviceMonitorRealtime(deviceId.value),
      getDeviceMonitorTrend(deviceId.value, buildRangeParams()),
    ])

    overview.value = {
      ...overview.value,
      realtime: realtimeRes,
      runtime_status: {
        ...overview.value.runtime_status,
        latest_timestamp: realtimeRes.timestamp || overview.value.runtime_status.latest_timestamp,
      },
    }
    trend.value = {
      ...trendRes,
      points: [...(trendRes.points || [])].sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      ),
    }
    await renderTrendChart()
    await loadStatusHistory()
    if (isSvgDevice.value) {
      await loadSVGTelemetry()
    }
    if (compensationSubtype.value === 'capacitor_bank_controller') {
      await Promise.all([
        loadCapBankTelemetry(),
        loadCapBankControlProfile(),
      ])
    }
  } catch {
    // axios 统一处理
  }
}

async function handleRangeChange() {
  if (!overview.value) return
  try {
    const tasks: Promise<unknown>[] = [loadTrendAndTables(), loadStatusHistory()]
    if (isSvgDevice.value) {
      tasks.push(loadSVGTelemetry())
    }
    if (compensationSubtype.value === 'capacitor_bank_controller') {
      tasks.push(loadCapBankTelemetry())
    }
    await Promise.all(tasks)
  } catch {
    ElMessage.error('筛选数据加载失败')
  }
}

async function handleResolveAlarm(row: DeviceAlarmRecord) {
  try {
    const { value } = await ElMessageBox.prompt('可填写处理备注，留空则直接标记为已处理。', '处理告警', {
      confirmButtonText: '确认处理',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：已远程复位，待现场复检',
    })
    alarmActionId.value = row.id
    await resolveAlarm(row.id, value)
    ElMessage.success('告警已处理')
    await loadPage(false)
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error('告警处理失败')
  } finally {
    alarmActionId.value = null
  }
}

async function handleToggleDevice() {
  if (!deviceId.value) return
  const nextActive = !isDeviceActive.value
  try {
    const { value } = await ElMessageBox.prompt(
      `${nextActive ? '将设备切换为运行状态' : '将设备切换为停机状态'}，可填写本次操作备注。`,
      nextActive ? '启动设备' : '停止设备',
      {
        confirmButtonText: nextActive ? '确认启动' : '确认停止',
        cancelButtonText: '取消',
        inputPlaceholder: '例如：例行巡检后恢复运行',
      },
    )
    toggleSubmitting.value = true
    await toggleDeviceStatus(deviceId.value, nextActive, value)
    ElMessage.success(nextActive ? '设备已启动' : '设备已停止')
    await loadPage(false)
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(nextActive ? '设备启动失败' : '设备停止失败')
  } finally {
    toggleSubmitting.value = false
  }
}

onMounted(async () => {
  await chart.initChart()
  await loadPage(true)
  refreshTimer = setInterval(refreshRealtime, REFRESH_INTERVAL_MS)
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})

function displayNumber(value?: number | null, digits: number = 1) {
  if (value === null || value === undefined) return '--'
  return Number(value).toFixed(digits)
}

function displayValueWithState(value: number | string | null | undefined, emptyText: string, digits: number = 1) {
  if (value === null || value === undefined || value === '') return emptyText
  if (typeof value === 'number') return Number(value).toFixed(digits)
  return String(value)
}

function formatBooleanStatus(
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

function temperatureTone(...values: Array<number | null | undefined>): CompensationTone {
  const maxTemp = maxTemperature(...values)
  if (maxTemp === null) return 'neutral'
  if (maxTemp >= 75) return 'danger'
  if (maxTemp >= 60) return 'warning'
  return 'success'
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

function inferConsumptionUnit() {
  const type = archive.value?.energy_type
  if (type === 'water' || type === 'gas') return 'm³'
  if (type === 'heat') return 'GJ'
  return 'kWh'
}

function buildRecentRange(hours: number): [Date, Date] {
  const end = new Date()
  const start = new Date(end.getTime() - hours * 60 * 60 * 1000)
  return [start, end]
}

function defaultTimeRange(): [Date, Date] {
  return buildRecentRange(24)
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

function buildRangeParams(limit: number = 300) {
  const [start, end] = timeRange.value || defaultTimeRange()
  return {
    start_time: toApiDate(start),
    end_time: toApiDate(end),
    limit,
  }
}

function getTrendMetricValue(point: TrendPoint, metric: 'flow_rate' | 'voltage' | 'current') {
  if (metric === 'voltage') return point.voltage ?? null
  if (metric === 'current') return point.current ?? null
  return point.value ?? null
}

function metricLabel(metric: 'flow_rate' | 'voltage' | 'current') {
  if (metric === 'voltage') return '电压'
  if (metric === 'current') return '电流'
  return '功率/流量'
}

function chartUnit(metric: 'flow_rate' | 'voltage' | 'current') {
  if (metric === 'voltage') return 'V'
  if (metric === 'current') return 'A'
  return archive.value?.unit || 'kW'
}

function toShortTime(timestamp?: string | null) {
  if (!timestamp) return '--'
  const date = new Date(timestamp)
  const [start, end] = timeRange.value || defaultTimeRange()
  const crossesDay =
    start.getFullYear() !== end.getFullYear()
    || start.getMonth() !== end.getMonth()
    || start.getDate() !== end.getDate()

  return crossesDay
    ? `${`${date.getMonth() + 1}`.padStart(2, '0')}/${`${date.getDate()}`.padStart(2, '0')} ${`${date.getHours()}`.padStart(2, '0')}:${`${date.getMinutes()}`.padStart(2, '0')}`
    : `${`${date.getHours()}`.padStart(2, '0')}:${`${date.getMinutes()}`.padStart(2, '0')}`
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

function historyTag(status?: string) {
  if (status === 'resolved') return '已恢复'
  if (status === 'success') return '成功'
  if (status === 'running') return '执行中'
  if (status === 'accepted') return '已入队'
  if (status === 'timeout') return '超时'
  if (status === 'rejected') return '拒绝'
  if (status === 'active') return '告警'
  return '事件'
}

function buildTrendLabels() {
  const points = trend.value?.points || []
  if (points.length) {
    return points.map((point) => toShortTime(point.timestamp))
  }

  const [start, end] = timeRange.value || defaultTimeRange()
  const step = Math.max(1, Math.floor((end.getTime() - start.getTime()) / (8 * 60 * 1000)))
  return Array.from({ length: 8 }).map((_, index) =>
    new Date(start.getTime() + index * step * 60 * 1000).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }),
  )
}

function buildTrendSeriesFromPoints(metric: 'voltage' | 'current') {
  const points = trend.value?.points || []
  const values = points
    .map((point) => (metric === 'voltage' ? point.voltage : point.current))
    .filter((value): value is number => value !== null && value !== undefined)

  if (!values.length) {
    return {
      values: points.map((point) => (metric === 'voltage' ? point.voltage : point.current) ?? null),
      peak: null,
      valley: null,
      isMock: false,
    }
  }

  return {
    values: points.map((point) => (metric === 'voltage' ? point.voltage : point.current) ?? null),
    peak: Math.max(...values),
    valley: Math.min(...values),
    isMock: false,
  }
}

function trendModelFromSingleSeries(options: {
  labels: string[]
  name: string
  unit: string
  color: string
  values: Array<number | null>
  summaryItems: Array<{ label: string; value: string }>
  isMock: boolean
  hint: string
  emptyText: string
}): CompensationTrendModel {
  return {
    labels: options.labels,
    legend: [options.name],
    axes: [{ name: options.unit }],
    series: [{ name: options.name, data: options.values, color: options.color, area: true }],
    summary: options.summaryItems,
    empty: !options.values.some((value) => value !== null && value !== undefined),
    emptyText: options.emptyText,
    hint: options.hint,
    isMock: options.isMock,
  }
}

function severityTagType(severity?: string) {
  if (severity === 'critical') return 'danger'
  if (severity === 'warning') return 'warning'
  return 'info'
}

function statusTagType(code?: string) {
  if (code === 'running') return 'success'
  if (code === 'alarm' || code === 'offline') return 'danger'
  if (code === 'degraded') return 'warning'
  return 'info'
}
</script>

<template>
  <div
    v-loading="loading"
    class="monitor-page"
  >
    <template v-if="isCompensationDevice">
      <CompensationHeader
        :model="compensationHeaderModel"
        :toggle-action-label="toggleActionLabel"
        :toggle-button-type="toggleButtonType"
        :toggle-submitting="toggleSubmitting"
        :can-control-devices="canControlDevices"
        :show-console-entry="compensationSubtype === 'capacitor_bank_controller'"
        @back="router.push('/devices')"
        @open-console="router.push(`/devices/${deviceId}/console`)"
        @refresh="loadPage(true)"
        @toggle="handleToggleDevice"
      />

      <div class="comp-page-grid">
        <section class="comp-main-column">
          <CompensationRealtimeOverview
            :core-metric="compensationCoreMetric"
            :pf-metric="compensationPfMetric"
            :metrics="compensationMetrics"
            :module-status="moduleStatusModel"
            :extended-hint="compensationExtendedHint"
          />

          <CompensationThreePhasePanel
            v-if="isSvgDevice || compensationSubtype === 'capacitor_bank_controller'"
            :svg-telemetry="compensationSvgTelemetry"
            :capacitor-bank-telemetry="compensationCapacitorBankTelemetry"
          />

          <CompensationCircuitStatePanel
            v-if="compensationSubtype === 'capacitor_bank_controller'"
            :capacitor-bank-telemetry="compensationCapacitorBankTelemetry"
          />

          <CompensationTrendPanel
            v-model:active-tab="compensationTrendTab"
            v-model:time-range="timeRange"
            :tabs="compensationTrendTabs"
            :model="compensationTrendModel"
            :shortcuts="timeShortcuts"
            :loading="chartLoading"
            @range-change="handleRangeChange"
          />

          <CompensationAlarmTable
            :rows="alarms"
            :action-id="alarmActionId"
            @resolve="handleResolveAlarm"
          />
        </section>

        <aside class="comp-side-column">
          <CompensationStatusSummary :items="compensationStatusItems" />
          <CompensationEventTimeline :events="compensationEvents" />
          <section
            v-if="compensationSubtype === 'capacitor_bank_controller'"
            class="side-panel side-panel--muted control-summary-panel"
          >
            <div class="side-panel__head">
              <h3>控制参数摘要</h3>
              <span>监控页仅展示只读摘要，完整参数与控制能力可通过顶部“进入控制台”查看。</span>
            </div>

            <div
              v-if="capacitorBankControlSummaryItems.some((item) => item.value !== '暂无参数')"
              class="profile-list"
            >
              <div
                v-for="item in capacitorBankControlSummaryItems"
                :key="item.label"
                class="profile-row"
              >
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <div
              v-else
              class="control-summary-empty"
            >
              <strong>暂无参数</strong>
              <span>当前设备还没有可回读的 JKWF 参数快照。</span>
            </div>
          </section>
          <CompensationDeviceProfile :items="compensationProfileItems" />
        </aside>
      </div>
    </template>

    <template v-else>
      <div class="page-head">
        <div class="head-left">
          <el-button
            :icon="ArrowLeft"
            text
            @click="router.push('/devices')"
          >
            返回设备台账
          </el-button>
          <div>
            <h2>{{ archive?.name || '设备监控' }}</h2>
            <p>{{ archive?.sn || '--' }} · {{ archive?.location || '未设置位置' }}</p>
          </div>
        </div>
        <div class="head-right">
          <el-tag
            :type="statusTagType(runtimeStatus?.code)"
            size="large"
          >
            {{ runtimeStatus?.label || '状态未知' }}
          </el-tag>
          <el-button
            :type="toggleButtonType"
            plain
            :icon="SwitchButton"
            :loading="toggleSubmitting"
            :disabled="!canControlDevices"
            @click="handleToggleDevice"
          >
            {{ toggleActionLabel }}
          </el-button>
          <el-button
            :icon="Refresh"
            @click="loadPage(true)"
          >
            刷新
          </el-button>
        </div>
      </div>

      <div class="monitor-grid">
        <section class="main-column">
          <div class="metric-grid">
            <div
              v-for="item in metricCards"
              :key="item.label"
              class="metric-card"
            >
              <span class="metric-label">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.unit }}</small>
            </div>
          </div>

          <div class="panel trend-panel">
            <div class="panel-head">
              <div>
                <h3>历史趋势</h3>
                <span>按时间范围查看设备实时曲线</span>
              </div>
              <div class="trend-toolbar">
                <el-radio-group
                  v-model="chartMetric"
                  size="small"
                >
                  <el-radio-button
                    v-for="item in chartMetricOptions"
                    :key="item.value"
                    :value="item.value"
                  >
                    {{ item.label }}
                  </el-radio-button>
                </el-radio-group>
                <el-date-picker
                  v-model="timeRange"
                  type="datetimerange"
                  unlink-panels
                  start-placeholder="开始时间"
                  end-placeholder="结束时间"
                  range-separator="至"
                  :shortcuts="timeShortcuts"
                  @change="handleRangeChange"
                />
              </div>
            </div>
            <div class="summary-inline">
              <span>当前 {{ displayNumber(trendSummary.latest) }} {{ chartUnit(chartMetric) }}</span>
              <span>峰值 {{ displayNumber(trendSummary.peak) }} {{ chartUnit(chartMetric) }}</span>
              <span>均值 {{ displayNumber(trendSummary.average) }} {{ chartUnit(chartMetric) }}</span>
              <span>谷值 {{ displayNumber(trendSummary.valley) }} {{ chartUnit(chartMetric) }}</span>
            </div>
            <div
              :ref="chart.chartRef"
              v-loading="chartLoading"
              class="trend-chart"
            />
          </div>

          <CompensationAlarmTable
            :rows="alarms"
            :action-id="alarmActionId"
            @resolve="handleResolveAlarm"
          />

          <div class="panel">
            <div class="panel-head">
              <div>
                <h3>启停记录</h3>
                <span>设备启停与控制操作留痕</span>
              </div>
            </div>
            <el-table
              :data="controlLogs"
              class="dark-table"
              empty-text="暂无启停记录"
            >
              <el-table-column
                prop="created_at"
                label="时间"
                min-width="170"
              >
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column
                prop="action"
                label="动作"
                width="100"
              />
              <el-table-column
                prop="result"
                label="结果"
                width="100"
              >
                <template #default="{ row }">
                  <el-tag :type="row.result === 'success' ? 'success' : 'danger'">
                    {{ row.result || '--' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                prop="operator"
                label="操作人"
                width="120"
              />
              <el-table-column
                prop="reason"
                label="备注"
                min-width="220"
              />
            </el-table>
          </div>
        </section>

        <aside class="side-column">
          <CompensationStatusSummary :items="genericStatusItems" />
          <CompensationEventTimeline :events="compensationEvents" />
          <CompensationDeviceProfile :items="compensationProfileItems" />
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped>
.monitor-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comp-page-grid,
.monitor-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.95fr) 360px;
  gap: 16px;
}

.comp-main-column,
.comp-side-column,
.main-column,
.side-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  background: #131d2b;
  border: 1px solid #243244;
  border-radius: 14px;
}

.head-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.head-left h2 {
  margin: 0;
  font-size: 22px;
  color: #f8fafc;
}

.head-left p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #8ea0bc;
}

.head-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-card,
.panel {
  background: #131d2b;
  border: 1px solid #243244;
  border-radius: 14px;
}

.metric-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-label {
  font-size: 12px;
  color: #8ea0bc;
}

.metric-card strong {
  font-size: 24px;
  color: #f8fafc;
  font-family: 'DIN', 'Monaco', monospace;
}

.metric-card small {
  color: #8ea0bc;
}

.panel {
  padding: 16px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-head h3 {
  margin: 0;
  font-size: 16px;
  color: #f8fafc;
}

.panel-head span {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #8ea0bc;
}

.summary-inline {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  color: #cdd9ec;
  font-size: 12px;
  margin-bottom: 14px;
}

.trend-toolbar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.trend-chart {
  height: 360px;
  width: 100%;
}

.control-summary-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-summary-empty {
  min-height: 92px;
  border: 1px dashed rgba(63, 82, 107, 0.72);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 6px;
  color: #8ea0bc;
  text-align: center;
  padding: 12px;
}

.control-summary-empty strong {
  color: #eef4ff;
}

.control-summary-button {
  width: 100%;
}

:deep(.dark-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(14, 24, 37, 0.92);
  --el-table-border-color: #243244;
  --el-table-row-hover-bg-color: rgba(22, 33, 48, 0.92);
  --el-table-text-color: #dbe6f5;
  --el-table-header-text-color: #8ea0bc;
}

@media (max-width: 1360px) {
  .comp-page-grid,
  .monitor-grid {
    grid-template-columns: 1fr;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
