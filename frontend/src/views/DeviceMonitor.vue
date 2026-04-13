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
  getSVGOperationsProfile,
  getSVGTelemetryHistory,
  getSVGTelemetryLatest,
  type SVGOperationsProfile,
  type SVGTelemetry,
} from '@/api/svg'
import CompensationHeader from '@/features/device-monitor/components/compensation/CompensationHeader.vue'
import CompensationRealtimeOverview from '@/features/device-monitor/components/compensation/CompensationRealtimeOverview.vue'
import CompensationTrendPanel from '@/features/device-monitor/components/compensation/CompensationTrendPanel.vue'
import CompensationEventTimeline from '@/features/device-monitor/components/compensation/CompensationEventTimeline.vue'
import CompensationStatusSummary from '@/features/device-monitor/components/compensation/CompensationStatusSummary.vue'
import CompensationDeviceProfile from '@/features/device-monitor/components/compensation/CompensationDeviceProfile.vue'
import CompensationAlarmTable from '@/features/device-monitor/components/compensation/CompensationAlarmTable.vue'
import CompensationThreePhasePanel from '@/features/device-monitor/components/compensation/CompensationThreePhasePanel.vue'
import type {
  CompensationEventItem,
  CompensationHeaderModel,
  CompensationLevelModel,
  CompensationMetric,
  CompensationProfileItem,
  CompensationStatusItem,
  CompensationTone,
  CompensationTrendModel,
  CompensationTrendOption,
  CompensationTrendTab,
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
const svgTelemetry = ref<SVGTelemetry | null>(null)
const svgProfile = ref<SVGOperationsProfile | null>(null)
const svgTelemetryHistory = ref<SVGTelemetry[]>([])
let refreshTimer: ReturnType<typeof setInterval> | null = null

const archive = computed(() => overview.value?.archive)
const runtimeStatus = computed(() => overview.value?.runtime_status)
const realtime = computed(() => overview.value?.realtime)

const isReactivePowerCompensator = computed(() => archive.value?.device_type === 'reactive_power_compensator')

const chartMetricOptions = [
  { label: '功率/流量', value: 'flow_rate' as const },
  { label: '电压', value: 'voltage' as const },
  { label: '电流', value: 'current' as const },
]

const compensationTrendTabs: CompensationTrendOption[] = [
  { label: '补偿效果', value: 'effect' },
  { label: '电压', value: 'voltage' },
  { label: '电流', value: 'current' },
  { label: '温度/健康度', value: 'health' },
]

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

const isDeviceActive = computed(() => runtimeStatus.value?.is_active ?? false)
const toggleActionLabel = computed(() => (isDeviceActive.value ? '停止设备' : '启动设备'))
const toggleButtonType = computed(() => (isDeviceActive.value ? 'danger' : 'success'))
const timelineHours = computed(() => {
  const [start, end] = timeRange.value || defaultTimeRange()
  return Math.max(1, Math.ceil((end.getTime() - start.getTime()) / (60 * 60 * 1000)))
})

const fallbackCompensation = computed(() => {
  const tel = svgTelemetry.value
  const prof = svgProfile.value

  // 控制模式：优先从 svg_telemetry.auto_mode/local_mode 读取
  const controlMode =
    tel?.auto_mode === true ? '自动' : tel?.auto_mode === false ? '手动' : isDeviceActive.value ? '自动' : '手动'

  // 模块总数：优先从 svg_asset_profile.module_count 读取
  const totalLevel = prof?.module_count ?? 8

  // 补偿容量利用率：优先从 svg_telemetry.capacity_utilization 读取
  const ratedCapacity = Number(archive.value?.rated_capacity || 0)
  const reactivePower = realtime.value?.reactive_power
  const usage =
    tel?.capacity_utilization != null
      ? tel.capacity_utilization
      : ratedCapacity > 0 && reactivePower !== null && reactivePower !== undefined
        ? Math.min(100, Math.max(0, (Math.abs(reactivePower) / ratedCapacity) * 100))
        : 0

  // 当前投入组数：由容量利用率和总模块数推算
  const currentLevel = Math.round((usage / 100) * totalLevel)

  // 柜内温度：优先从 svg_telemetry.cabinet_temp 读取
  const cabinetTemperature = tel?.cabinet_temp ?? realtime.value?.temperature ?? 36.8

  const controlSource = controlMode === '自动' ? 'EMS 自动策略' : '现场手动'

  return {
    controlMode,
    compensationLevelCurrent: currentLevel,
    compensationLevelTotal: totalLevel,
    compensationCapacityUsage: usage,
    controlSource,
    switchPermission: canControlDevices.value && runtimeStatus.value?.is_online !== false,
    cabinetTemperature,
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
      label: fallbackCompensation.value.controlMode,
      tone: fallbackCompensation.value.controlMode === '自动' ? 'info' : 'warning',
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
      hint: archive.value?.rated_capacity ? '按额定容量换算' : '演示占位，待真实容量策略接入',
      tone: fallbackCompensation.value.compensationCapacityUsage >= 90 ? 'warning' : 'success',
      state: archive.value?.rated_capacity ? 'live' : 'mock',
    },
    {
      key: 'controlMode',
      label: '控制模式',
      value: fallbackCompensation.value.controlMode,
      unit: '',
      hint: '支持自动 / 手动模式切换',
      tone: fallbackCompensation.value.controlMode === '自动' ? 'info' : 'warning',
      state: 'mock',
    },
    {
      key: 'cabinetTemperature',
      label: '柜内温度',
      value: displayValueWithState(temperature, '暂无数据'),
      unit: '°C',
      hint: temperature >= 45 ? '温度偏高，请关注通风散热' : temperature >= 40 ? '温度轻微预警' : '柜内温度正常',
      tone: temperature >= 45 ? 'danger' : temperature >= 40 ? 'warning' : 'success',
      state: realtime.value?.temperature == null ? 'mock' : 'live',
    },
  ]
})

const compensationLevelModel = computed<CompensationLevelModel>(() => ({
  current: fallbackCompensation.value.compensationLevelCurrent,
  total: fallbackCompensation.value.compensationLevelTotal,
  hint: `当前投入 ${fallbackCompensation.value.compensationLevelCurrent} 组，单小时投切 ${fallbackCompensation.value.hourlySwitchCount} 次`,
  state: runtimeStatus.value?.is_online ? 'live' : 'offline',
}))

const compensationExtendedHint = computed(() => {
  const messages: string[] = []
  if (!archive.value?.rated_capacity) messages.push('额定容量暂未接入，补偿容量利用率先按演示占位显示。')
  if (realtime.value?.temperature == null) messages.push('柜内温度当前使用演示占位，待真实采集点接入。')
  return messages.join(' ')
})

const compensationTrendModel = computed<CompensationTrendModel>(() => {
  const labels = buildTrendLabels()
  if (compensationTrendTab.value === 'effect') {
    const points = trend.value?.points || []
    const hasRealQ = points.some((p) => p.reactive_power != null)
    const hasRealPf = points.some((p) => p.power_factor != null)
    const qSeries = hasRealQ
      ? points.map((p) => p.reactive_power ?? null)
      : buildMockSeries(labels.length, 318, 22)
    const pfSeries = hasRealPf
      ? points.map((p) => p.power_factor ?? null)
      : buildMockSeries(labels.length, 0.95, 0.03, 2)
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
        { label: '目标 PF', value: fallbackCompensation.value.targetPowerFactor.toFixed(2) },
      ],
      empty: false,
      emptyText: '暂无补偿效果趋势数据',
      hint: hasRealQ || hasRealPf ? '展示历史采集的无功功率与功率因数走势。' : '当前采用演示曲线承载后续真实趋势接入。',
      isMock: !hasRealQ && !hasRealPf,
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
      hint: voltageSeries.isMock ? '当前电压趋势使用演示占位，待历史曲线更完整接入。' : '展示最近时间范围内的母线电压走势。',
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
      hint: currentSeries.isMock ? '当前电流趋势使用演示占位，待历史曲线更完整接入。' : '展示最近时间范围内的线电流走势。',
      emptyText: '暂无电流趋势数据',
    })
  }

  const histPoints = svgTelemetryHistory.value
  const hasCabinetTemp = histPoints.some((p) => p.cabinet_temp != null)
  const healthLabels = hasCabinetTemp ? histPoints.map((p) => toShortTime(p.timestamp)) : labels
  const healthTemp = hasCabinetTemp
    ? histPoints.map((p) => p.cabinet_temp ?? null)
    : buildMockSeries(labels.length, fallbackCompensation.value.cabinetTemperature, 4)
  const healthScore = buildMockSeries(healthLabels.length, 92, 6)
  return {
    labels: healthLabels,
    legend: ['柜内温度', '健康度'],
    axes: [
      { name: '°C' },
      { name: '分', min: 0, max: 100, position: 'right' },
    ],
    series: [
      { name: '柜内温度', data: healthTemp, color: '#fb7185', area: true },
      { name: '健康度', data: healthScore, color: '#22c55e', yAxisIndex: 1 },
    ],
    summary: [
      { label: '柜内温度', value: `${displayValueWithState(fallbackCompensation.value.cabinetTemperature, '暂无数据')} °C` },
      { label: 'THD', value: `${fallbackCompensation.value.thd.toFixed(1)} %` },
      { label: '累计运行', value: `${fallbackCompensation.value.runningHours} h` },
    ],
    empty: false,
    emptyText: '暂无温度与健康度趋势数据',
    hint: hasCabinetTemp ? '展示采集的柜内温度历史走势。' : '当前温度/健康度趋势使用演示占位，用于承接后续真实健康度算法接入。',
    isMock: !hasCabinetTemp,
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
    { time: '14:25', title: '自动投入第 1 组', detail: '检测到无功需求上升，系统自动投入补偿组。', tone: 'info', tag: '自动' },
    { time: '14:27', title: '自动投入第 2 组', detail: '功率因数仍低于目标值，继续追加补偿。', tone: 'info', tag: '自动' },
    { time: '14:35', title: '功率因数恢复正常', detail: '补偿效果稳定，功率因数回到目标区间。', tone: 'success', tag: '恢复' },
    { time: '14:42', title: '检测到轻微欠补偿', detail: '运行曲线显示轻微欠补偿，请关注负荷波动。', tone: 'warning', tag: '关注' },
    { time: '14:50', title: '通讯恢复', detail: '数据采集链路恢复，实时监控重新上线。', tone: 'success', tag: '通信' },
  ]
})

const compensationStatusItems = computed<CompensationStatusItem[]>(() => {
  const tel = svgTelemetry.value
  const items: CompensationStatusItem[] = [
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
      label: '当前模式',
      value: fallbackCompensation.value.controlMode,
      tone: fallbackCompensation.value.controlMode === '自动' ? 'info' : 'warning',
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
  }
  return items
})

const compensationProfileItems = computed<CompensationProfileItem[]>(() => {
  const prof = svgProfile.value
  const items: CompensationProfileItem[] = [
    { label: '设备名称', value: archive.value?.name || '补偿器1' },
    { label: '序列号', value: archive.value?.sn || 'SN2323' },
    { label: '设备类型', value: '无功功率补偿器' },
    { label: '能源类型', value: archive.value?.energy_type || '电' },
    { label: '安装位置', value: archive.value?.location || '未配置安装位置' },
    { label: '额定容量', value: archive.value?.rated_capacity ? `${archive.value.rated_capacity} kVar` : '未配置' },
    { label: '描述', value: archive.value?.description || '用于无功补偿与功率因数优化的柜体设备。' },
  ]
  if (prof) {
    if (prof.model_number) items.push({ label: '产品型号', value: prof.model_number })
    if (prof.rated_voltage) items.push({ label: '额定电压', value: `${prof.rated_voltage} V` })
    if (prof.module_count) items.push({ label: '模块数量', value: `${prof.module_count} 组` })
    if (prof.distribution_room) items.push({ label: '配电房', value: prof.distribution_room })
    if (prof.building) items.push({ label: '所在楼栋', value: prof.building })
    if (prof.circuit) items.push({ label: '所在回路', value: prof.circuit })
    if (prof.om_responsible) items.push({ label: '运维负责人', value: prof.om_responsible })
    if (prof.inspection_responsible) items.push({ label: '巡检负责人', value: prof.inspection_responsible })
    if (prof.maintenance_cycle_days) items.push({ label: '维保周期', value: `${prof.maintenance_cycle_days} 天` })
    if (prof.commission_date) items.push({ label: '投运日期', value: prof.commission_date })
    if (prof.warranty_expiry) items.push({ label: '质保到期', value: prof.warranty_expiry })
  }
  return items
})

const genericStatusItems = computed(() => [
  { label: '设备状态', value: runtimeStatus.value?.label || '状态未知' },
  { label: '在线状态', value: runtimeStatus.value?.is_online ? '在线' : '离线' },
  { label: '未处理告警', value: `${runtimeStatus.value?.unresolved_alarm_count ?? 0} 条` },
  { label: '最近消息', value: formatDateTime(runtimeStatus.value?.last_message_at) },
  { label: '最近成功入库', value: formatDateTime(runtimeStatus.value?.last_success_at) },
])

watch(
  () => chart.chartRef.value,
  async () => {
    if (!chart.chartRef.value || isReactivePowerCompensator.value) return
    await chart.initChart()
    await renderTrendChart()
  },
)

watch(
  () => chartMetric.value,
  async () => {
    if (isReactivePowerCompensator.value) return
    await renderTrendChart()
  },
)

async function renderTrendChart() {
  if (isReactivePowerCompensator.value || !trend.value) return

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

    trend.value = trendRes
    alarms.value = alarmsRes.items
    controlLogs.value = logsRes.items
    await renderTrendChart()
  } finally {
    chartLoading.value = false
  }
}

async function loadSVGTelemetry() {
  try {
    svgTelemetry.value = await getSVGTelemetryLatest(deviceId.value)
  } catch {
    svgTelemetry.value = null
  }
  try {
    const [start, end] = timeRange.value || defaultTimeRange()
    svgTelemetryHistory.value = await getSVGTelemetryHistory(deviceId.value, {
      start: toApiDate(start),
      end: toApiDate(end),
      limit: 200,
    })
  } catch {
    svgTelemetryHistory.value = []
  }
}

async function loadSVGProfile() {
  try {
    svgProfile.value = await getSVGOperationsProfile(deviceId.value)
  } catch {
    svgProfile.value = null
  }
}

async function loadPage(showLoading: boolean = true) {
  if (!deviceId.value) return
  if (showLoading) loading.value = true

  try {
    overview.value = await getDeviceMonitorOverview(deviceId.value)
    const extraTasks: Promise<unknown>[] = [loadTrendAndTables(), loadStatusHistory()]
    if (isReactivePowerCompensator.value) {
      extraTasks.push(loadSVGTelemetry(), loadSVGProfile())
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
    trend.value = trendRes
    await renderTrendChart()
    await loadStatusHistory()
    if (isReactivePowerCompensator.value) {
      await loadSVGTelemetry()
    }
  } catch {
    // axios 统一处理
  }
}

async function handleRangeChange() {
  if (!overview.value) return
  try {
    const tasks: Promise<unknown>[] = [loadTrendAndTables(), loadStatusHistory()]
    if (isReactivePowerCompensator.value) {
      tasks.push(loadSVGTelemetry())
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
  refreshTimer = setInterval(refreshRealtime, 10000)
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
  return value.toISOString()
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
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

function formatDateTime(value?: string | null) {
  if (!value) return '暂无数据'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
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
  if (status === 'active' || status === 'failed') return 'danger'
  if (eventType === 'control') return 'info'
  return 'warning'
}

function historyTag(status?: string) {
  if (status === 'resolved') return '已恢复'
  if (status === 'success') return '成功'
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

function buildMockSeries(length: number, base: number, variation: number, digits: number = 1) {
  return Array.from({ length }).map((_, index) => {
    const wave = Math.sin(index / 1.6) * variation
    return Number((base + wave).toFixed(digits))
  })
}

function buildTrendSeriesFromPoints(metric: 'voltage' | 'current') {
  const points = trend.value?.points || []
  const values = points
    .map((point) => (metric === 'voltage' ? point.voltage : point.current))
    .filter((value): value is number => value !== null && value !== undefined)

  if (!values.length) {
    const base = metric === 'voltage' ? 401 : 48
    return {
      values: buildMockSeries(buildTrendLabels().length, base, metric === 'voltage' ? 8 : 5),
      peak: null,
      valley: null,
      isMock: true,
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
    empty: false,
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
    <template v-if="isReactivePowerCompensator">
      <CompensationHeader
        :model="compensationHeaderModel"
        :toggle-action-label="toggleActionLabel"
        :toggle-button-type="toggleButtonType"
        :toggle-submitting="toggleSubmitting"
        :can-control-devices="canControlDevices"
        @back="router.push('/devices')"
        @refresh="loadPage(true)"
        @toggle="handleToggleDevice"
      />

      <div class="comp-page-grid">
        <section class="comp-main-column">
          <CompensationRealtimeOverview
            :core-metric="compensationCoreMetric"
            :pf-metric="compensationPfMetric"
            :metrics="compensationMetrics"
            :level="compensationLevelModel"
            :extended-hint="compensationExtendedHint"
          />

          <CompensationThreePhasePanel :telemetry="svgTelemetry" />

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
          <CompensationEventTimeline :events="compensationEvents" />
          <CompensationStatusSummary :items="compensationStatusItems" />
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
          <CompensationEventTimeline :events="compensationEvents" />
          <CompensationStatusSummary :items="genericStatusItems" />
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
