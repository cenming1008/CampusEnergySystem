<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Refresh, SwitchButton, Warning } from '@element-plus/icons-vue'
import { useECharts } from '@/shared/composables/useECharts'
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
  type MonitorOverview,
  type DeviceTrendResponse,
} from '@/api/deviceMonitor'

import { usePermissions } from '@/shared/composables/usePermissions'
import {
  getSVGTelemetryLatest,
  getSVGOperationsProfile,
  type SVGTelemetry,
  type SVGOperationsProfile,
} from '@/api/svg'

const route = useRoute()
const router = useRouter()
const chart = useECharts()
const { canControlDevices } = usePermissions()

const deviceId = computed(() => Number(route.params.id))
const loading = ref(false)
const overview = ref<MonitorOverview | null>(null)
const alarms = ref<DeviceAlarmRecord[]>([])
const controlLogs = ref<DeviceControlLog[]>([])
const statusHistory = ref<DeviceStatusEvent[]>([])
const trend = ref<DeviceTrendResponse | null>(null)
const chartMetric = ref<'flow_rate' | 'voltage' | 'current'>('flow_rate')
const timeRange = ref<[Date, Date] | null>(defaultTimeRange())
const chartLoading = ref(false)
const alarmActionId = ref<number | null>(null)
const toggleSubmitting = ref(false)
const alarmFilter = ref<'all' | 'unresolved' | 'resolved'>('all')
let refreshTimer: ReturnType<typeof setInterval> | null = null

const archive = computed(() => overview.value?.archive)
const runtimeStatus = computed(() => overview.value?.runtime_status)
const realtime = computed(() => overview.value?.realtime)

const isSVG = computed(() => archive.value?.device_type === 'svg')
const svgTelemetry = ref<SVGTelemetry | null>(null)
const svgOperationsProfile = ref<SVGOperationsProfile | null>(null)

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

const metricCards = computed(() => {
  if (isSVG.value) {
    return [
      { label: '实时有功功率', value: formatMetric(realtime.value?.flow_rate), unit: 'kW' },
      { label: '无功功率', value: formatMetric(realtime.value?.reactive_power), unit: 'kVAR' },
      { label: '功率因数', value: formatMetric(realtime.value?.power_factor), unit: '' },
      { label: '综合电压', value: formatMetric(realtime.value?.voltage), unit: 'V' },
    ]
  }
  return [
    { label: '实时功率/流量', value: formatMetric(realtime.value?.flow_rate), unit: archive.value?.unit || '--' },
    { label: '累计读数', value: formatMetric(realtime.value?.consumption), unit: inferConsumptionUnit() },
    { label: '电压', value: formatMetric(realtime.value?.voltage), unit: 'V' },
    { label: '电流', value: formatMetric(realtime.value?.current), unit: 'A' },
  ]
})

const chartUnit = computed(() => {
  if (chartMetric.value === 'voltage') return 'V'
  if (chartMetric.value === 'current') return 'A'
  return archive.value?.unit || '--'
})

const trendSummary = computed(() => {
  const values = (trend.value?.points || [])
    .map(point => getTrendMetricValue(point, chartMetric.value))
    .filter((value): value is number => value !== null && value !== undefined)

  if (!values.length) {
    return { latest: null, peak: null, valley: null, average: null }
  }

  const latest = values[values.length - 1]
  const peak = Math.max(...values)
  const valley = Math.min(...values)
  const average = values.reduce((sum, value) => sum + value, 0) / values.length

  return {
    latest,
    peak,
    valley,
    average,
  }
})

const isDeviceActive = computed(() => runtimeStatus.value?.is_active ?? false)
const toggleActionLabel = computed(() => isDeviceActive.value ? '停止设备' : '启动设备')
const toggleButtonType = computed(() => isDeviceActive.value ? 'danger' : 'success')
const timelineHours = computed(() => {
  const [start, end] = timeRange.value || defaultTimeRange()
  return Math.max(1, Math.ceil((end.getTime() - start.getTime()) / (60 * 60 * 1000)))
})

function formatMetric(value?: number | null) {
  if (value === null || value === undefined) return '--'
  return Number(value).toFixed(1)
}

function inferConsumptionUnit() {
  const type = archive.value?.energy_type
  if (type === 'water' || type === 'gas') return 'm³'
  if (type === 'heat') return 'GJ'
  return 'kWh'
}

function formatTime(value?: string | null) {
  if (!value) return '--'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
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

function historyTagType(status?: string) {
  if (status === 'success' || status === 'resolved') return 'success'
  if (status === 'active' || status === 'failed') return 'danger'
  return 'info'
}

function historyNodeType(eventType?: string) {
  if (eventType === 'alarm') return 'danger'
  if (eventType === 'alarm_resolution') return 'success'
  if (eventType === 'control') return 'warning'
  return 'primary'
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

function getTrendMetricValue(point: DeviceTrendResponse['points'][number], metric: typeof chartMetric.value) {
  if (metric === 'voltage') return point.voltage ?? null
  if (metric === 'current') return point.current ?? null
  return point.value ?? null
}

function metricLabel(metric: typeof chartMetric.value) {
  if (metric === 'voltage') return '电压'
  if (metric === 'current') return '电流'
  return '功率/流量'
}

async function renderTrendChart() {
  if (!trend.value) return

  const points = trend.value.points || []
  const seriesData = points.map(point => getTrendMetricValue(point, chartMetric.value) ?? 0)
  const threshold = archive.value?.rated_capacity && chartMetric.value === 'flow_rate'
    ? Number(archive.value.rated_capacity)
    : null

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
      data: points.map(point => new Date(point.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })),
      axisLine: { lineStyle: { color: '#314055' } },
      axisLabel: { color: '#8ea0bc', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: chartUnit.value,
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
        markPoint: {
          symbolSize: 40,
          data: [{ type: 'max', name: '峰值' }, { type: 'min', name: '谷值' }],
          itemStyle: { color: '#1d2938', borderColor: '#38bdf8', borderWidth: 1 },
          label: { color: '#e5edf7', fontSize: 10 },
        },
        markLine: threshold ? {
          symbol: 'none',
          label: { color: '#f59e0b', formatter: '额定阈值' },
          lineStyle: { color: '#f59e0b', type: 'dashed' },
          data: [{ yAxis: threshold }],
        } : undefined,
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

async function loadSVGData() {
  if (!isSVG.value) return
  const id = deviceId.value
  const results = await Promise.allSettled([
    getSVGTelemetryLatest(id),
    getSVGOperationsProfile(id),
  ])
  if (results[0].status === 'fulfilled') svgTelemetry.value = results[0].value
  if (results[1].status === 'fulfilled') svgOperationsProfile.value = results[1].value
}

async function loadPage(showLoading: boolean = true) {
  if (!deviceId.value) return
  if (showLoading) loading.value = true

  try {
    const overviewRes = await getDeviceMonitorOverview(deviceId.value)
    overview.value = overviewRes
    await Promise.all([loadTrendAndTables(), loadSVGData()])
  } catch (error) {
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
    // 由 axios 拦截器统一提示
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
    await Promise.all([loadStatusHistory(), loadSVGData()])
  } catch {
    // 由各子函数处理
  }
}

async function handleRangeChange() {
  if (!overview.value) return
  try {
    await loadTrendAndTables()
    await loadStatusHistory()
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
      }
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
  await loadStatusHistory()
  refreshTimer = setInterval(refreshRealtime, 10000)
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<template>
  <div
    v-loading="loading"
    class="monitor-page"
  >
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
                @change="renderTrendChart"
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
            <span>当前 {{ formatMetric(trendSummary.latest) }} {{ chartUnit }}</span>
            <span>峰值 {{ formatMetric(trendSummary.peak) }} {{ chartUnit }}</span>
            <span>均值 {{ formatMetric(trendSummary.average) }} {{ chartUnit }}</span>
            <span>谷值 {{ formatMetric(trendSummary.valley) }} {{ chartUnit }}</span>
          </div>
          <div
            :ref="chart.chartRef"
            v-loading="chartLoading"
            class="trend-chart"
          />
        </div>

        <!-- SVG 遥测扩展面板 -->
        <div
          v-if="isSVG && svgTelemetry"
          class="panel svg-telemetry-panel"
        >
          <div class="panel-head">
            <div>
              <h3>SVG 实时遥测</h3>
              <span>三相数据 · 状态位 · 温度 · 故障</span>
            </div>
            <span class="muted-text">{{ svgTelemetry.timestamp ? formatTime(svgTelemetry.timestamp) : '--' }}</span>
          </div>

          <!-- 三相电量 -->
          <div class="svg-section-title">三相电量</div>
          <div class="svg-metric-grid">
            <div class="svg-metric-card"><span>Ua</span><strong>{{ svgTelemetry.voltage_a?.toFixed(1) ?? '--' }}</strong><small>V</small></div>
            <div class="svg-metric-card"><span>Ub</span><strong>{{ svgTelemetry.voltage_b?.toFixed(1) ?? '--' }}</strong><small>V</small></div>
            <div class="svg-metric-card"><span>Uc</span><strong>{{ svgTelemetry.voltage_c?.toFixed(1) ?? '--' }}</strong><small>V</small></div>
            <div class="svg-metric-card"><span>Ia</span><strong>{{ svgTelemetry.current_a?.toFixed(1) ?? '--' }}</strong><small>A</small></div>
            <div class="svg-metric-card"><span>Ib</span><strong>{{ svgTelemetry.current_b?.toFixed(1) ?? '--' }}</strong><small>A</small></div>
            <div class="svg-metric-card"><span>Ic</span><strong>{{ svgTelemetry.current_c?.toFixed(1) ?? '--' }}</strong><small>A</small></div>
            <div class="svg-metric-card"><span>频率</span><strong>{{ svgTelemetry.frequency?.toFixed(2) ?? '--' }}</strong><small>Hz</small></div>
            <div class="svg-metric-card"><span>无功输出</span><strong>{{ svgTelemetry.svg_reactive_output?.toFixed(1) ?? '--' }}</strong><small>kVAR</small></div>
            <div class="svg-metric-card"><span>容量利用率</span><strong>{{ svgTelemetry.capacity_utilization?.toFixed(1) ?? '--' }}</strong><small>%</small></div>
            <div class="svg-metric-card"><span>输出方向</span><strong>{{ svgTelemetry.output_direction === 'inductive' ? '感性' : svgTelemetry.output_direction === 'capacitive' ? '容性' : '--' }}</strong><small></small></div>
          </div>

          <!-- 温度和内部量 -->
          <div class="svg-section-title">温度 / 内部量</div>
          <div class="svg-metric-grid">
            <div class="svg-metric-card"><span>柜内温度</span><strong>{{ svgTelemetry.cabinet_temp?.toFixed(1) ?? '--' }}</strong><small>°C</small></div>
            <div class="svg-metric-card"><span>模块温度</span><strong>{{ svgTelemetry.module_temp?.toFixed(1) ?? '--' }}</strong><small>°C</small></div>
            <div class="svg-metric-card"><span>IGBT温度</span><strong>{{ svgTelemetry.igbt_temp?.toFixed(1) ?? '--' }}</strong><small>°C</small></div>
            <div class="svg-metric-card"><span>散热器温度</span><strong>{{ svgTelemetry.heatsink_temp?.toFixed(1) ?? '--' }}</strong><small>°C</small></div>
            <div class="svg-metric-card"><span>直流母线电压</span><strong>{{ svgTelemetry.dc_bus_voltage?.toFixed(1) ?? '--' }}</strong><small>V</small></div>
          </div>

          <!-- 运行状态位 -->
          <div class="svg-section-title">运行状态</div>
          <div class="svg-status-grid">
            <el-tag :type="svgTelemetry.run_status ? 'success' : 'info'" size="small">{{ svgTelemetry.run_status ? '运行中' : '未运行' }}</el-tag>
            <el-tag :type="svgTelemetry.stop_status ? 'danger' : 'info'" size="small">{{ svgTelemetry.stop_status ? '已停机' : '未停机' }}</el-tag>
            <el-tag :type="svgTelemetry.auto_mode ? 'success' : 'warning'" size="small">{{ svgTelemetry.auto_mode === null ? '--' : svgTelemetry.auto_mode ? '自动' : '手动' }}</el-tag>
            <el-tag :type="svgTelemetry.local_mode ? 'info' : 'primary'" size="small">{{ svgTelemetry.local_mode === null ? '--' : svgTelemetry.local_mode ? '本地' : '远方' }}</el-tag>
            <el-tag :type="svgTelemetry.breaker_status ? 'success' : 'danger'" size="small">断路器 {{ svgTelemetry.breaker_status === null ? '--' : svgTelemetry.breaker_status ? '合' : '分' }}</el-tag>
            <el-tag :type="svgTelemetry.module_status ? 'success' : 'warning'" size="small">模块 {{ svgTelemetry.module_status === null ? '--' : svgTelemetry.module_status ? '正常' : '异常' }}</el-tag>
            <el-tag :type="svgTelemetry.fan_status ? 'success' : 'warning'" size="small">风机 {{ svgTelemetry.fan_status === null ? '--' : svgTelemetry.fan_status ? '正常' : '异常' }}</el-tag>
            <el-tag :type="svgTelemetry.comm_status ? 'success' : 'danger'" size="small">通信 {{ svgTelemetry.comm_status === null ? '--' : svgTelemetry.comm_status ? '正常' : '中断' }}</el-tag>
          </div>

          <!-- 故障位 -->
          <div class="svg-section-title">故障告警</div>
          <div class="svg-status-grid">
            <el-tag :type="svgTelemetry.overvoltage_fault ? 'danger' : 'success'" size="small">{{ svgTelemetry.overvoltage_fault ? '⚠ 过压' : '过压正常' }}</el-tag>
            <el-tag :type="svgTelemetry.undervoltage_fault ? 'danger' : 'success'" size="small">{{ svgTelemetry.undervoltage_fault ? '⚠ 欠压' : '欠压正常' }}</el-tag>
            <el-tag :type="svgTelemetry.overcurrent_fault ? 'danger' : 'success'" size="small">{{ svgTelemetry.overcurrent_fault ? '⚠ 过流' : '过流正常' }}</el-tag>
            <el-tag :type="svgTelemetry.overtemp_fault ? 'warning' : 'success'" size="small">{{ svgTelemetry.overtemp_fault ? '⚠ 过温' : '温度正常' }}</el-tag>
            <el-tag :type="svgTelemetry.module_fault ? 'danger' : 'success'" size="small">{{ svgTelemetry.module_fault ? '⚠ 模块故障' : '模块正常' }}</el-tag>
            <el-tag :type="svgTelemetry.fan_fault ? 'warning' : 'success'" size="small">{{ svgTelemetry.fan_fault ? '⚠ 风机故障' : '风机正常' }}</el-tag>
            <el-tag :type="svgTelemetry.comm_fault ? 'warning' : 'success'" size="small">{{ svgTelemetry.comm_fault ? '⚠ 通信故障' : '通信正常' }}</el-tag>
          </div>
          <div
            v-if="svgTelemetry.current_fault_code || svgTelemetry.current_alarm_code"
            class="svg-code-row"
          >
            <span v-if="svgTelemetry.current_fault_code">故障代码：<strong>{{ svgTelemetry.current_fault_code }}</strong></span>
            <span v-if="svgTelemetry.current_alarm_code">告警代码：<strong>{{ svgTelemetry.current_alarm_code }}</strong></span>
          </div>
        </div>

        <div class="panel">
          <div class="panel-head">
            <div>
              <h3>告警记录</h3>
              <span>支持直接处理未关闭告警</span>
            </div>
            <el-segmented
              v-model="alarmFilter"
              :options="[
                { label: '全部', value: 'all' },
                { label: '未处理', value: 'unresolved' },
                { label: '已处理', value: 'resolved' },
              ]"
              size="small"
              @change="handleRangeChange"
            />
          </div>
          <el-table
            :data="alarms"
            class="dark-table"
            empty-text="暂无告警记录"
          >
            <el-table-column
              prop="timestamp"
              label="时间"
              min-width="170"
            >
              <template #default="{ row }">
                {{ formatTime(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column
              prop="message"
              label="内容"
              min-width="260"
            />
            <el-table-column
              prop="severity"
              label="级别"
              width="100"
            >
              <template #default="{ row }">
                <el-tag :type="severityTagType(row.severity)">
                  {{ row.severity || 'info' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="is_resolved"
              label="状态"
              width="100"
            >
              <template #default="{ row }">
                <el-tag :type="row.is_resolved ? 'success' : 'danger'">
                  {{ row.is_resolved ? '已处理' : '未处理' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="120"
              fixed="right"
            >
              <template #default="{ row }">
                <el-button
                  v-if="!row.is_resolved"
                  type="warning"
                  link
                  :icon="Warning"
                  :loading="alarmActionId === row.id"
                  @click="handleResolveAlarm(row)"
                >
                  处理
                </el-button>
                <span
                  v-else
                  class="muted-text"
                >已关闭</span>
              </template>
            </el-table-column>
          </el-table>
        </div>

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
                {{ formatTime(row.created_at) }}
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
        <div class="panel">
          <div class="panel-head">
            <div>
              <h3>状态时间轴</h3>
              <span>汇总设备告警与启停事件</span>
            </div>
          </div>
          <div
            v-if="statusHistory.length"
            class="timeline-wrap"
          >
            <el-timeline>
              <el-timeline-item
                v-for="item in statusHistory"
                :key="`${item.event_type}-${item.timestamp}-${item.title}`"
                :timestamp="formatTime(item.timestamp)"
                :type="historyNodeType(item.event_type)"
                hollow
              >
                <div class="timeline-card">
                  <div class="timeline-head">
                    <strong>{{ item.title }}</strong>
                    <el-tag
                      size="small"
                      :type="historyTagType(item.status)"
                    >
                      {{ item.status }}
                    </el-tag>
                  </div>
                  <p>{{ item.detail || '无附加说明' }}</p>
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>
          <el-empty
            v-else
            description="当前时间范围内暂无状态事件"
          />
        </div>

        <div class="panel">
          <div class="panel-head">
            <div>
              <h3>运行状态</h3>
              <span>当前接入与设备状态</span>
            </div>
          </div>
          <div class="status-list">
            <div class="status-row">
              <span>设备状态</span><strong>{{ runtimeStatus?.label || '--' }}</strong>
            </div>
            <div class="status-row">
              <span>在线状态</span><strong>{{ runtimeStatus?.is_online ? '在线' : '离线' }}</strong>
            </div>
            <div class="status-row">
              <span>未处理告警</span><strong>{{ runtimeStatus?.unresolved_alarm_count ?? 0 }}</strong>
            </div>
            <div class="status-row">
              <span>最近消息</span><strong>{{ formatTime(runtimeStatus?.last_message_at) }}</strong>
            </div>
            <div class="status-row">
              <span>最近成功入库</span><strong>{{ formatTime(runtimeStatus?.last_success_at) }}</strong>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-head">
            <div>
              <h3>设备档案</h3>
              <span>基础信息与安装信息</span>
            </div>
          </div>
          <div class="archive-list">
            <div class="archive-row">
              <span>设备名称</span><strong>{{ archive?.name || '--' }}</strong>
            </div>
            <div class="archive-row">
              <span>序列号</span><strong>{{ archive?.sn || '--' }}</strong>
            </div>
            <div class="archive-row">
              <span>设备类型</span><strong>{{ archive?.device_type || '--' }}</strong>
            </div>
            <div class="archive-row">
              <span>能源类型</span><strong>{{ archive?.energy_type || '--' }}</strong>
            </div>
            <div class="archive-row">
              <span>安装位置</span><strong>{{ archive?.location || '--' }}</strong>
            </div>
            <div class="archive-row">
              <span>额定容量</span><strong>{{ archive?.rated_capacity ?? '--' }}</strong>
            </div>
            <div class="archive-row">
              <span>描述</span><strong>{{ archive?.description || '--' }}</strong>
            </div>
          </div>
        </div>

        <div
          v-if="isSVG && svgOperationsProfile"
          class="panel"
        >
          <div class="panel-head">
            <div>
              <h3>SVG 运维档案</h3>
              <span>基础参数与运维维护信息</span>
            </div>
          </div>
          <div class="archive-list">
            <div
              v-for="[label, val] in [
                ['设备型号', svgOperationsProfile.model_number],
                ['额定电压', svgOperationsProfile.rated_voltage != null ? svgOperationsProfile.rated_voltage + ' V' : null],
                ['额定频率', svgOperationsProfile.rated_frequency != null ? svgOperationsProfile.rated_frequency + ' Hz' : null],
                ['通信地址', svgOperationsProfile.comm_address],
                ['软件版本', svgOperationsProfile.software_version],
                ['硬件版本', svgOperationsProfile.hardware_version],
                ['协议版本', svgOperationsProfile.protocol_version],
                ['模块数量', svgOperationsProfile.module_count != null ? svgOperationsProfile.module_count + ' 个' : null],
                ['单模块容量', svgOperationsProfile.single_module_capacity != null ? svgOperationsProfile.single_module_capacity + ' kVAR' : null],
                ['设备标签', svgOperationsProfile.device_label_zh],
                ['资产编号', svgOperationsProfile.asset_number],
                ['固定资产编码', svgOperationsProfile.fixed_asset_code],
                ['所属配电室', svgOperationsProfile.distribution_room],
                ['所属配电柜', svgOperationsProfile.distribution_cabinet],
                ['所属回路', svgOperationsProfile.circuit],
                ['所属楼栋', svgOperationsProfile.building],
                ['所属区域', svgOperationsProfile.area],
                ['现场编号', svgOperationsProfile.field_number],
                ['安装日期', svgOperationsProfile.install_date],
                ['投运日期', svgOperationsProfile.commission_date],
                ['运维负责人', svgOperationsProfile.om_responsible],
                ['巡检负责人', svgOperationsProfile.inspection_responsible],
                ['所属部门', svgOperationsProfile.department],
                ['联系电话', svgOperationsProfile.contact_phone],
                ['保修到期', svgOperationsProfile.warranty_expiry],
                ['维护周期', svgOperationsProfile.maintenance_cycle_days != null ? svgOperationsProfile.maintenance_cycle_days + ' 天' : null],
                ['设备别名', svgOperationsProfile.device_alias],
                ['上位机名称', svgOperationsProfile.display_name],
              ].filter(([, v]) => v != null)"
              :key="label as string"
              class="archive-row"
            >
              <span>{{ label }}</span><strong>{{ val }}</strong>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.monitor-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
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

.monitor-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) 360px;
  gap: 16px;
}

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

.timeline-wrap {
  max-height: 360px;
  overflow: auto;
  padding-right: 6px;
}

.timeline-card {
  padding: 10px 12px;
  background: #162130;
  border: 1px solid #243244;
  border-radius: 10px;
}

.timeline-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 6px;
}

.timeline-head strong {
  color: #f8fafc;
  font-size: 13px;
}

.timeline-card p {
  margin: 0;
  color: #8ea0bc;
  font-size: 12px;
  line-height: 1.5;
}

.muted-text {
  color: #8ea0bc;
  font-size: 12px;
}

.status-list,
.archive-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-row,
.archive-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  background: #162130;
  border: 1px solid #243244;
  border-radius: 10px;
}

.status-row span,
.archive-row span {
  color: #8ea0bc;
  font-size: 12px;
}

.status-row strong,
.archive-row strong {
  color: #f8fafc;
  font-size: 12px;
  text-align: right;
}

:deep(.dark-table) {
  --el-table-bg-color: #131d2b;
  --el-table-tr-bg-color: #131d2b;
  --el-table-header-bg-color: #162130;
  --el-table-border-color: #243244;
  --el-table-row-hover-bg-color: #162130;
  --el-table-text-color: #dbe6f5;
  --el-table-header-text-color: #8ea0bc;
}

:deep(.el-segmented) {
  --el-segmented-bg-color: #162130;
  --el-segmented-item-selected-bg-color: #243244;
  --el-border-radius-base: 10px;
}

@media (max-width: 1280px) {
  .monitor-grid {
    grid-template-columns: 1fr;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

/* SVG 遥测面板 */
.svg-section-title {
  font-size: 11px;
  color: #8ea0bc;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 14px 0 8px;
}

.svg-metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.svg-metric-card {
  background: #162130;
  border: 1px solid #243244;
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.svg-metric-card span {
  font-size: 11px;
  color: #8ea0bc;
}

.svg-metric-card strong {
  font-size: 18px;
  color: #f8fafc;
  font-family: 'DIN', 'Monaco', monospace;
}

.svg-metric-card small {
  font-size: 11px;
  color: #8ea0bc;
}

.svg-status-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.svg-code-row {
  margin-top: 10px;
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #8ea0bc;
}

.svg-code-row strong {
  color: #f59e0b;
}

@media (max-width: 1280px) {
  .svg-metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .head-right,
  .trend-toolbar {
    width: 100%;
    justify-content: flex-start;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .svg-metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
