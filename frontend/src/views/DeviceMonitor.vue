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
  type CompensationMonitor,
  type DeviceAlarmRecord,
  type DeviceControlLog,
  type DeviceStatusEvent,
  type DeviceTrendResponse,
  type MonitorOverview,
  type TrendPoint,
} from '@/api/deviceMonitor'
import { useCompensationMonitor } from '@/features/device-monitor/composables/useCompensationMonitor'
import CompensationHeader from '@/features/device-monitor/components/compensation/CompensationHeader.vue'
import CompensationRealtimeOverview from '@/features/device-monitor/components/compensation/CompensationRealtimeOverview.vue'
import CompensationTrendPanel from '@/features/device-monitor/components/compensation/CompensationTrendPanel.vue'
import CompensationEventTimeline from '@/features/device-monitor/components/compensation/CompensationEventTimeline.vue'
import CompensationStatusSummary from '@/features/device-monitor/components/compensation/CompensationStatusSummary.vue'
import CompensationDeviceProfile from '@/features/device-monitor/components/compensation/CompensationDeviceProfile.vue'
import CompensationSvgProfileEditDialog from '@/features/device-monitor/components/compensation/CompensationSvgProfileEditDialog.vue'
import CompensationControlSummaryPanel from '@/features/device-monitor/components/compensation/CompensationControlSummaryPanel.vue'
import CompensationAlarmTable from '@/features/device-monitor/components/compensation/CompensationAlarmTable.vue'
import CompensationThreePhasePanel from '@/features/device-monitor/components/compensation/CompensationThreePhasePanel.vue'
import CompensationCircuitStatePanel from '@/features/device-monitor/components/compensation/CompensationCircuitStatePanel.vue'
import MonitorSectionPanel from '@/shared/components/MonitorSectionPanel.vue'
import MonitorPageHeader from '@/shared/components/MonitorPageHeader.vue'
import type { CompensationTrendTab } from '@/features/device-monitor/components/compensation/types'

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
const svgProfileEditVisible = ref(false)
let refreshTimer: ReturnType<typeof setInterval> | null = null
const REFRESH_INTERVAL_MS = 5000
const archive = computed(() => overview.value?.archive)
const runtimeStatus = computed(() => overview.value?.runtime_status)
const realtime = computed(() => overview.value?.realtime)

const {
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
} = useCompensationMonitor({
  deviceId,
  overview,
  trend,
  statusHistory,
  timeRange,
  compensationTrendTab,
  canControlDevices,
})

const chartMetricOptions = [
  { label: '功率/流量', value: 'flow_rate' as const },
  { label: '电压', value: 'voltage' as const },
  { label: '电流', value: 'current' as const },
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

watch(
  () => timeRange.value?.map((value) => value?.getTime()) ?? null,
  async (next, previous) => {
    if (!overview.value || !next || !previous) return
    if (next[0] === previous[0] && next[1] === previous[1]) return
    await handleRangeChange()
  },
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
    // NOTE: compensationSvgProfile / compensationCapacitorBankControlProfile are refs
    // returned from the composable; setting .value here directly mutates them.
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
    const shouldRefreshCompensationOverview = isCompensationDevice.value
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
    await refreshCompensationData()
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

function formatIngestionStatus(status?: string | null) {
  if (status === 'online') return '在线采集'
  if (status === 'degraded') return '采集波动'
  if (status === 'offline') return '离线'
  return '未知'
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
        @open-console="router.push(`/device-console/${deviceId}`)"
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
            :configured-split-circuit-count="compensationCapacitorBankControlProfile?.split_output_circuit_count ?? undefined"
            :configured-common-circuit-count="compensationCapacitorBankControlProfile?.common_output_circuit_count ?? undefined"
            :phase-a-circuit-total-count="compensationCapacitorBankControlProfile?.phase_a_circuit_total_count ?? undefined"
            :phase-b-circuit-total-count="compensationCapacitorBankControlProfile?.phase_b_circuit_total_count ?? undefined"
            :phase-c-circuit-total-count="compensationCapacitorBankControlProfile?.phase_c_circuit_total_count ?? undefined"
            :common1-circuit-total-count="compensationCapacitorBankControlProfile?.common_1_circuit_total_count ?? undefined"
            :common2-circuit-total-count="compensationCapacitorBankControlProfile?.common_2_circuit_total_count ?? undefined"
            :common3-circuit-total-count="compensationCapacitorBankControlProfile?.common_3_circuit_total_count ?? undefined"
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
          <CompensationControlSummaryPanel
            v-if="compensationSubtype === 'capacitor_bank_controller'"
            :summary-items="capacitorBankControlSummaryView.summaryItems"
            :capacity-expansion-items="capacitorBankControlSummaryView.capacityExpansionItems"
            :has-summary-data="capacitorBankControlSummaryView.hasSummaryData"
          />
          <CompensationDeviceProfile
            :items="compensationProfileItems"
            :editable="isSvgDevice && canControlDevices"
            @edit="svgProfileEditVisible = true"
          />
        </aside>
      </div>

      <CompensationSvgProfileEditDialog
        v-if="isSvgDevice"
        v-model="svgProfileEditVisible"
        :device-id="deviceId"
        :profile="compensationSvgProfile"
        @saved="loadSVGProfile"
      />
    </template>

    <template v-else>
      <MonitorPageHeader
        :title="archive?.name || '设备监控'"
        :subtitle="`${archive?.sn || '--'} · ${archive?.location || '未设置位置'}`"
      >
        <template #leading>
          <el-button
            :icon="ArrowLeft"
            text
            @click="router.push('/devices')"
          >
            返回设备台账
          </el-button>
        </template>
        <template #actions>
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
        </template>
      </MonitorPageHeader>

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

          <MonitorSectionPanel
            title="历史趋势"
            subtitle="按时间范围查看设备实时曲线"
          >
            <template #headerExtra>
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
            </template>
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
          </MonitorSectionPanel>

          <CompensationAlarmTable
            :rows="alarms"
            :action-id="alarmActionId"
            @resolve="handleResolveAlarm"
          />

          <MonitorSectionPanel
            title="启停记录"
            subtitle="设备启停与控制操作留痕"
          >
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
          </MonitorSectionPanel>
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
  width: min(100%, 1680px);
  margin: 0 auto;
  box-sizing: border-box;
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

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
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

/* ─── Large screens ──────────────────────────────────────────── */

@media (min-width: 1920px) {
  .monitor-page {
    width: min(100%, 2100px);
    gap: 20px;
  }

  .comp-page-grid,
  .monitor-grid {
    grid-template-columns: minmax(0, 1.95fr) 440px;
    gap: 20px;
  }

  .metric-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}

@media (min-width: 2400px) {
  .monitor-page {
    width: min(100%, 2560px);
    gap: 24px;
  }

  .comp-page-grid,
  .monitor-grid {
    grid-template-columns: minmax(0, 1.95fr) 520px;
    gap: 24px;
  }
}

/* ─── Responsive ─────────────────────────────────────────────── */

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
