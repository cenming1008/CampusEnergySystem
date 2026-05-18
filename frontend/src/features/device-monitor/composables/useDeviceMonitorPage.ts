import { computed, markRaw, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
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
  type MonitorMetricCard,
  type MonitorOverview,
  type MonitorTrendField,
  type TrendPoint,
} from '@/api/deviceMonitor'
import { useCapacitorBankControlConsole } from '@/features/device-control/useCapacitorBankControlConsole'
import { useECharts } from '@/shared/composables/useECharts'
import { usePermissions } from '@/shared/composables/usePermissions'
import { useCompensationMonitor } from './useCompensationMonitor'
import { useStorageMonitor } from './useStorageMonitor'
import type {
  CompensationTrendTab,
  CompensationWorkbenchTab,
  CompensationWorkbenchTabOption,
} from '@/features/device-monitor/components/compensation/types'

type SupportedTrendMetric = 'flow_rate' | 'voltage' | 'current' | 'reactive_power' | 'power_factor' | 'consumption'

const supportedTrendMetrics = new Set<SupportedTrendMetric>([
  'flow_rate',
  'voltage',
  'current',
  'reactive_power',
  'power_factor',
  'consumption',
])

const fallbackChartMetricOptions = [
  { label: '功率/流量', value: 'flow_rate' as const, unit: null as string | null },
  { label: '电压', value: 'voltage' as const, unit: 'V' },
  { label: '电流', value: 'current' as const, unit: 'A' },
]

const REFRESH_INTERVAL_MS = 5000
const LIVE_RANGE_TOLERANCE_MS = REFRESH_INTERVAL_MS * 2

const compensationWorkbenchTabs: CompensationWorkbenchTabOption[] = [
  { label: '运行监视', value: 'runtime' },
  { label: '曲线分析', value: 'curves' },
  { label: '远程控制', value: 'remote-control', tone: 'danger' },
  { label: '参数设置', value: 'parameter-settings', tone: 'warning' },
  { label: '事件记录', value: 'event-records' },
]

function normalizeWorkbenchTab(value: unknown): CompensationWorkbenchTab {
  const raw = Array.isArray(value) ? value[0] : value
  if (raw === 'curves') return 'curves'
  if (raw === 'remote-control') return 'remote-control'
  if (raw === 'parameter-settings') return 'parameter-settings'
  if (raw === 'event-records') return 'event-records'
  return 'runtime'
}

export function useDeviceMonitorPage() {
  const route = useRoute()
  const router = useRouter()
  const chart = useECharts()
  const {
    canManageDevices,
    canControlDevices,
    currentRole,
    isAdmin,
  } = usePermissions()

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
  const chartMetric = ref<SupportedTrendMetric>('flow_rate')
  const alarmFilter = ref<'all' | 'unresolved' | 'resolved'>('all')
  const timeRange = ref<[Date, Date] | null>(defaultTimeRange())
  const compensationTrendTab = ref<CompensationTrendTab>('effect')
  const compensationWorkbenchTab = ref<CompensationWorkbenchTab>(
    normalizeWorkbenchTab(route.query.tab),
  )
  const compensationDetailTab = ref<'three-phase' | 'circuit'>('circuit')
  const storageTrendTab = ref<'soc' | 'power' | 'temperature' | 'energy'>('soc')
  const svgProfileEditVisible = ref(false)
  let refreshTimer: ReturnType<typeof setInterval> | null = null
  let suppressTimeRangeWatcher = false

  const archive = computed(() => overview.value?.archive)
  const runtimeStatus = computed(() => overview.value?.runtime_status)
  const realtime = computed(() => overview.value?.realtime)
  const diagnosticsSummary = computed(() => overview.value?.diagnostics_summary)
  const templateDiagnostics = computed(() => overview.value?.template_diagnostics)
  const isPendingArchiveDevice = computed(() => archive.value?.archive_status === 'pending')

  const compensation = useCompensationMonitor({
    deviceId,
    overview,
    trend,
    statusHistory,
    timeRange,
    compensationTrendTab,
    canControlDevices,
  })

  const capacitorBankControlConsole = useCapacitorBankControlConsole({
    deviceId,
    canManageDevices,
    canControlDevices,
    currentRole,
    isAdmin,
    enableLifecycle: false,
  })

  const storage = useStorageMonitor({ deviceId, overview, timeRange })

  const timeShortcuts = [
    { text: '近 1 小时', value: () => buildRecentRange(1) },
    { text: '近 6 小时', value: () => buildRecentRange(6) },
    { text: '近 24 小时', value: () => buildRecentRange(24) },
    { text: '近 7 天', value: () => buildRecentRange(24 * 7) },
  ]

  const fallbackMetricCards = computed<MonitorMetricCard[]>(() => [
    { key: 'flow_rate', label: '实时功率/流量', value: realtime.value?.flow_rate, unit: archive.value?.unit || 'kW', precision: 1 },
    { key: 'consumption', label: '累计读数', value: realtime.value?.consumption, unit: inferConsumptionUnit(), precision: 1 },
    { key: 'voltage', label: '电压', value: realtime.value?.voltage, unit: 'V', precision: 1 },
    { key: 'current', label: '电流', value: realtime.value?.current, unit: 'A', precision: 1 },
  ])

  const metricCards = computed<MonitorMetricCard[]>(() => {
    const backendCards = overview.value?.metric_cards || []
    return backendCards.length ? backendCards : fallbackMetricCards.value
  })

  const trendFields = computed<MonitorTrendField[]>(() =>
    overview.value?.trend_fields?.length
      ? overview.value.trend_fields
      : fallbackChartMetricOptions.map((item) => ({
        key: item.value,
        label: item.label,
        unit: item.unit,
        precision: 1,
      })),
  )

  const chartMetricOptions = computed(() => {
    const options = trendFields.value
      .filter((item): item is MonitorTrendField & { key: SupportedTrendMetric } =>
        supportedTrendMetrics.has(item.key as SupportedTrendMetric),
      )
      .map((item) => ({
        label: item.label,
        value: item.key,
        unit: item.unit ?? null,
      }))

    return options.length ? options : fallbackChartMetricOptions
  })

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
  const toggleActionLabel = computed(() => (isDeviceActive.value ? '停用设备' : '启用设备'))
  const toggleButtonType = computed(() => (isDeviceActive.value ? 'danger' : 'success'))
  const realtimeStaleTime = computed(() =>
    runtimeStatus.value?.latest_timestamp
    || runtimeStatus.value?.last_success_at
    || runtimeStatus.value?.last_message_at
    || realtime.value?.timestamp
  )
  const isRealtimeStale = computed(() => runtimeStatus.value?.is_online === false && Boolean(realtimeStaleTime.value))

  // 聚合电容柜回路 profile 的 split/common 与各相回路总数，供 CompensationDetailPanel 使用
  const compensationCircuitProfile = computed(() => {
    const profile = compensation.compensationCapacitorBankControlProfile.value
    return {
      splitCircuitCount: profile?.split_output_circuit_count ?? undefined,
      commonCircuitCount: profile?.common_output_circuit_count ?? undefined,
      phaseACircuitTotalCount: profile?.phase_a_circuit_total_count ?? undefined,
      phaseBCircuitTotalCount: profile?.phase_b_circuit_total_count ?? undefined,
      phaseCCircuitTotalCount: profile?.phase_c_circuit_total_count ?? undefined,
      common1CircuitTotalCount: profile?.common_1_circuit_total_count ?? undefined,
      common2CircuitTotalCount: profile?.common_2_circuit_total_count ?? undefined,
      common3CircuitTotalCount: profile?.common_3_circuit_total_count ?? undefined,
    }
  })
  const timelineHours = computed(() => {
    const [start, end] = timeRange.value || defaultTimeRange()
    return Math.max(1, Math.ceil((end.getTime() - start.getTime()) / (60 * 60 * 1000)))
  })

  watch(
    () => chart.chartRef.value,
    async () => {
      if (!chart.chartRef.value || compensation.isCompensationDevice.value) return
      await chart.initChart()
      await renderTrendChart()
    },
  )

  watch(
    () => route.query.tab,
    (tab) => {
      compensationWorkbenchTab.value = normalizeWorkbenchTab(tab)
    },
  )

  watch(
    () => chartMetric.value,
    async () => {
      if (compensation.isCompensationDevice.value) return
      await renderTrendChart()
    },
  )

  watch(
    () => chartMetricOptions.value.map((item) => item.value),
    (options) => {
      if (!options.includes(chartMetric.value)) {
        chartMetric.value = options[0] || 'flow_rate'
      }
    },
    { immediate: true },
  )

  watch(
    () => compensation.compensationTrendTabs.value.map((item) => item.value),
    (tabs) => {
      if (!tabs.includes(compensationTrendTab.value)) {
        compensationTrendTab.value = tabs[0] || 'effect'
      }
    },
    { immediate: true },
  )

  watch(
    () => timeRange.value?.map((value) => value?.getTime()) ?? null,
    async (next, previous) => {
      if (suppressTimeRangeWatcher) return
      if (!overview.value || !next || !previous) return
      if (next[0] === previous[0] && next[1] === previous[1]) return
      await handleRangeChange()
    },
  )

  async function renderTrendChart() {
    if (compensation.isCompensationDevice.value || !trend.value) return

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

      const [trendRes, logsRes] = await Promise.all([
        getDeviceMonitorTrend(deviceId.value, params),
        getDeviceMonitorControlLogs(deviceId.value, params),
      ])

      trend.value = {
        ...trendRes,
        points: [...(trendRes.points || [])].sort(
          (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
        ),
      }
      controlLogs.value = logsRes.items
      await renderTrendChart()
    } finally {
      chartLoading.value = false
    }
  }

  // 告警记录独立加载：按设备维度取最新记录，不受历史趋势时间范围影响
  async function loadAlarms() {
    if (!deviceId.value) return
    const resolved =
      alarmFilter.value === 'all'
        ? undefined
        : alarmFilter.value === 'resolved'
          ? true
          : false
    const alarmsRes = await getDeviceMonitorAlarms(deviceId.value, { resolved })
    alarms.value = alarmsRes.items
  }

  async function loadPage(showLoading: boolean = true) {
    if (!deviceId.value) return
    if (showLoading) loading.value = true

    try {
      overview.value = await getDeviceMonitorOverview(deviceId.value)
      const currentOverview = overview.value
      const extraTasks: Promise<unknown>[] = [loadTrendAndTables(), loadStatusHistory(), loadAlarms()]
      if (compensation.isSvgDevice.value) {
        extraTasks.push(compensation.loadSVGTelemetry(), compensation.loadSVGProfile())
        compensation.compensationCapacitorBankControlProfile.value = null
      }
      if (compensation.compensationSubtype.value === 'capacitor_bank_controller') {
        extraTasks.push(
          compensation.loadCapBankTelemetry(),
          compensation.loadCapBankControlProfile(),
          capacitorBankControlConsole.loadPageWithOverview(currentOverview),
        )
        compensation.compensationSvgProfile.value = null
      }
      if (!compensation.isCompensationDevice.value) {
        compensation.compensationSvgProfile.value = null
        compensation.compensationCapacitorBankControlProfile.value = null
      }
      if (storage.isStorageDevice.value) {
        extraTasks.push(storage.loadLatestTelemetry(), storage.loadTelemetryHistory())
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
      syncLiveTimeRange()
      const shouldRefreshCompensationOverview = compensation.isCompensationDevice.value
      const [overviewRes, realtimeRes, trendRes] = await Promise.all([
        shouldRefreshCompensationOverview ? getDeviceMonitorOverview(deviceId.value) : Promise.resolve(null),
        getDeviceMonitorRealtime(deviceId.value),
        getDeviceMonitorTrend(deviceId.value, buildRangeParams()),
      ])

      overview.value = {
        ...(overviewRes || overview.value),
        realtime: realtimeRes,
        runtime_status: {
          ...(overviewRes?.runtime_status || overview.value.runtime_status),
          latest_timestamp:
            realtimeRes.timestamp
            || overviewRes?.runtime_status?.latest_timestamp
            || overview.value.runtime_status.latest_timestamp,
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
      await loadAlarms()
      await compensation.refreshCompensationData()
      if (compensation.compensationSubtype.value === 'capacitor_bank_controller' && overview.value) {
        await capacitorBankControlConsole.loadPageWithOverview(overview.value)
      }
      if (storage.isStorageDevice.value) await storage.refreshStorageData()
    } catch {
      // axios 统一处理
    }
  }

  async function handleRangeChange() {
    if (!overview.value) return
    const currentOverview = overview.value
    try {
      const tasks: Promise<unknown>[] = [loadTrendAndTables(), loadStatusHistory()]
      if (compensation.isSvgDevice.value) {
        tasks.push(compensation.loadSVGTelemetry())
      }
      if (compensation.compensationSubtype.value === 'capacitor_bank_controller') {
        tasks.push(
          compensation.loadCapBankTelemetry(),
          capacitorBankControlConsole.loadPageWithOverview(currentOverview),
        )
      }
      if (storage.isStorageDevice.value) {
        tasks.push(storage.loadTelemetryHistory())
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
        `${nextActive ? '将设备管理状态切换为启用' : '将设备管理状态切换为停用'}，可填写本次操作备注。`,
        nextActive ? '启用设备' : '停用设备',
        {
          confirmButtonText: nextActive ? '确认启用' : '确认停用',
          cancelButtonText: '取消',
          inputPlaceholder: '例如：例行巡检后恢复采集管理',
        },
      )
      toggleSubmitting.value = true
      await toggleDeviceStatus(deviceId.value, nextActive, value)
      ElMessage.success(nextActive ? '设备已启用' : '设备已停用')
      await loadPage(false)
    } catch (error) {
      if (error === 'cancel' || error === 'close') return
      ElMessage.error(nextActive ? '设备启用失败' : '设备停用失败')
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

  function inferConsumptionUnit() {
    const type = archive.value?.energy_type
    if (type === 'water' || type === 'gas') return 'm³'
    if (type === 'heat') return 'GJ'
    return 'kWh'
  }

  function buildRangeParams(limit: number = 300) {
    const [start, end] = timeRange.value || defaultTimeRange()
    return {
      start_time: toApiDate(start),
      end_time: toApiDate(end),
      limit,
    }
  }

  function syncLiveTimeRange() {
    if (!timeRange.value) return
    const [start, end] = timeRange.value
    const now = new Date()
    const distanceFromNow = Math.abs(now.getTime() - end.getTime())
    if (distanceFromNow > LIVE_RANGE_TOLERANCE_MS) return

    const durationMs = Math.max(1, end.getTime() - start.getTime())
    suppressTimeRangeWatcher = true
    timeRange.value = [new Date(now.getTime() - durationMs), now]
    void Promise.resolve().then(() => {
      suppressTimeRangeWatcher = false
    })
  }

  function getTrendMetricValue(point: TrendPoint, metric: SupportedTrendMetric) {
    if (metric === 'voltage') return point.voltage ?? null
    if (metric === 'current') return point.current ?? null
    if (metric === 'reactive_power') return point.reactive_power ?? null
    if (metric === 'power_factor') return point.power_factor ?? null
    if (metric === 'consumption') return point.consumption ?? null
    return point.flow_rate ?? point.value ?? null
  }

  function metricLabel(metric: SupportedTrendMetric) {
    return chartMetricOptions.value.find((item) => item.value === metric)?.label || '功率/流量'
  }

  function chartUnit(metric: SupportedTrendMetric) {
    const unit = chartMetricOptions.value.find((item) => item.value === metric)?.unit
    if (unit) return unit
    if (metric === 'voltage') return 'V'
    if (metric === 'current') return 'A'
    if (metric === 'reactive_power') return 'kvar'
    if (metric === 'power_factor') return ''
    if (metric === 'consumption') return inferConsumptionUnit()
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

  function statusTagType(code?: string) {
    if (code === 'running') return 'success'
    if (code === 'alarm' || code === 'offline') return 'danger'
    if (code === 'degraded') return 'warning'
    return 'info'
  }

  return reactive({
    router: markRaw(router),
    chart: markRaw(chart),
    canControlDevices,
    deviceId,
    loading,
    chartLoading,
    toggleSubmitting,
    alarmActionId,
    overview,
    trend,
    alarms,
    controlLogs,
    statusHistory,
    chartMetric,
    alarmFilter,
    timeRange,
    compensationTrendTab,
    compensationWorkbenchTabs,
    compensationWorkbenchTab,
    compensationDetailTab,
    compensationCircuitProfile,
    storageTrendTab,
    svgProfileEditVisible,
    archive,
    runtimeStatus,
    realtime,
    diagnosticsSummary,
    templateDiagnostics,
    isPendingArchiveDevice,
    ...compensation,
    capacitorBankControlConsole,
    controlConsoleLoadError: capacitorBankControlConsole.loadError,
    controlConsoleProfileWarning: capacitorBankControlConsole.profileWarning,
    controlConsoleWriteDialogVisible: capacitorBankControlConsole.writeDialogVisible,
    controlConsoleControlProfile: capacitorBankControlConsole.controlProfile,
    controlConsoleWriteForm: capacitorBankControlConsole.writeForm,
    controlConsoleManualSwitchForm: capacitorBankControlConsole.manualSwitchForm,
    controlConsoleWriteSubmitting: capacitorBankControlConsole.writeSubmitting,
    controlConsoleToggleSubmitting: capacitorBankControlConsole.toggleSubmitting,
    controlConsoleCurrentControlModeLabel: capacitorBankControlConsole.currentControlModeLabel,
    controlConsoleCanRunManualSwitch: capacitorBankControlConsole.canRunManualSwitch,
    controlConsoleManualSwitchDisabledReason: capacitorBankControlConsole.manualSwitchDisabledReason,
    controlConsoleCanWriteParameters: capacitorBankControlConsole.canWriteParameters,
    controlConsoleSelectedWriteMeta: capacitorBankControlConsole.selectedWriteMeta,
    controlConsoleEditableParameterCards: capacitorBankControlConsole.editableParameterCards,
    controlConsoleManualPhaseOptions: capacitorBankControlConsole.manualPhaseOptions,
    controlConsoleManualSwitchActionOptions: capacitorBankControlConsole.manualSwitchActionOptions,
    controlConsoleManualCommonGroupOptions: capacitorBankControlConsole.manualCommonGroupOptions,
    controlConsoleActionCards: capacitorBankControlConsole.actionCards,
    controlConsoleReadonlySectionView: capacitorBankControlConsole.readonlySectionView,
    controlConsoleReadonlySummaryView: capacitorBankControlConsole.readonlySummaryView,
    controlConsoleWriteSectionView: capacitorBankControlConsole.writeSectionView,
    controlConsoleLogView: capacitorBankControlConsole.logView,
    handleControlConsoleManualSwitchCommand: capacitorBankControlConsole.handleManualSwitchCommand,
    openControlConsoleWriteDialog: capacitorBankControlConsole.openWriteDialog,
    submitControlConsoleParameterWrite: capacitorBankControlConsole.submitParameterWrite,
    handleControlConsoleActionCard: capacitorBankControlConsole.handleActionCard,
    storageTelemetry: storage.latestTelemetry,
    storageTelemetryHistory: storage.telemetryHistory,
    isStorageDevice: storage.isStorageDevice,
    storageMonitor: storage.storageMonitor,
    storageRuntimeStatus: storage.runtimeStatus,
    runStateRaw: storage.runStateRaw,
    runStateLabel: storage.runStateLabel,
    socValue: storage.socValue,
    socState: storage.socState,
    powerValue: storage.powerValue,
    powerState: storage.powerState,
    powerDirection: storage.powerDirection,
    storageOverviewMetrics: storage.overviewMetrics,
    storageControlModeLabel: storage.controlModeLabel,
    storageIngestionTone: storage.ingestionTone,
    storageIngestionStatusLabel: storage.ingestionStatusLabel,
    storageLatestSampleText: storage.latestSampleText,
    timeShortcuts,
    metricCards,
    trendFields,
    chartMetricOptions,
    trendSummary,
    isDeviceActive,
    toggleActionLabel,
    toggleButtonType,
    realtimeStaleTime,
    isRealtimeStale,
    loadPage,
    loadStatusHistory,
    refreshRealtime,
    handleRangeChange,
    handleResolveAlarm,
    handleToggleDevice,
    chartUnit,
    formatDateTime,
    statusTagType,
  })
}

function buildRecentRange(hours: number): [Date, Date] {
  const end = new Date()
  const start = new Date(end.getTime() - hours * 60 * 60 * 1000)
  return [start, end]
}

function defaultTimeRange(): [Date, Date] {
  return buildRecentRange(1)
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

export type DeviceMonitorPageModel = ReturnType<typeof useDeviceMonitorPage>
