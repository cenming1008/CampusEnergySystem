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
  { label: '实时功率/流量', value: formatMetric(realtime.value?.flow_rate), unit: archive.value?.unit || '--' },
  { label: '累计读数', value: formatMetric(realtime.value?.consumption), unit: inferConsumptionUnit() },
  { label: '电压', value: formatMetric(realtime.value?.voltage), unit: 'V' },
  { label: '电流', value: formatMetric(realtime.value?.current), unit: 'A' },
])

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

async function loadPage(showLoading: boolean = true) {
  if (!deviceId.value) return
  if (showLoading) loading.value = true

  try {
    const overviewRes = await getDeviceMonitorOverview(deviceId.value)
    overview.value = overviewRes
    await loadTrendAndTables()
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
    await loadStatusHistory()
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
}
</style>
