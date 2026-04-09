<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { getAlarms, resolveAlarm, resolveAllAlarms, type Alarm } from '@/api/alarm'
import { getDevices, type Device } from '@/api/device'

type AlarmStatusFilter = 'all' | 'active' | 'resolved'
type AlarmSeverityFilter = 'all' | 'critical' | 'warning' | 'info'

interface TrendPoint {
  label: string
  total: number
  critical: number
  warning: number
}

const loading = ref(false)
const resolving = ref<number | null>(null)
const bulkResolving = ref(false)
const alarms = ref<Alarm[]>([])
const deviceList = ref<Device[]>([])
const refreshedAt = ref('')

const filters = reactive<{
  device_id?: number
  start_time?: string
  end_time?: string
  limit: number
}>({
  limit: 80,
})

const searchTerm = ref('')
const filterStatus = ref<AlarmStatusFilter>('all')
const filterSeverity = ref<AlarmSeverityFilter>('all')
const dateRange = ref<string[]>([])

const hasActiveAlarms = computed(() => alarms.value.some((item) => !item.is_resolved))

function resolveDeviceName(deviceId: number) {
  return deviceList.value.find((item) => item.id === deviceId)?.name || `设备 ${deviceId}`
}

function severityTagType(severity?: string) {
  if (severity === 'critical') return 'danger'
  if (severity === 'warning') return 'warning'
  return 'info'
}

function severityLabel(severity?: string) {
  if (severity === 'critical') return '严重'
  if (severity === 'warning') return '预警'
  return '提示'
}

function formatDateTime(value?: string | null) {
  if (!value) return '暂无时间'

  try {
    return new Date(value).toLocaleString('zh-CN', {
      hour12: false,
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return value
  }
}

function formatRelativeTime(value?: string | null) {
  if (!value) return '暂无更新'

  const diff = Math.max(0, Date.now() - new Date(value).getTime())
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days} 天前`
  return formatDateTime(value)
}

function applyDateRange() {
  filters.start_time = dateRange.value[0]
  filters.end_time = dateRange.value[1]
}

function matchesSearch(alarm: Alarm) {
  if (!searchTerm.value.trim()) return true
  const keyword = searchTerm.value.trim().toLowerCase()
  return [
    alarm.message,
    alarm.category,
    alarm.source,
    resolveDeviceName(alarm.device_id),
    String(alarm.device_id),
  ]
    .filter(Boolean)
    .some((item) => String(item).toLowerCase().includes(keyword))
}

const filteredAlarms = computed(() =>
  alarms.value.filter((alarm) => {
    const statusMatched =
      filterStatus.value === 'all' ||
      (filterStatus.value === 'active' && !alarm.is_resolved) ||
      (filterStatus.value === 'resolved' && alarm.is_resolved)

    const severityMatched = filterSeverity.value === 'all' || (alarm.severity || 'info') === filterSeverity.value

    return statusMatched && severityMatched && matchesSearch(alarm)
  }),
)

const metrics = computed(() => {
  const source = filteredAlarms.value
  const active = source.filter((item) => !item.is_resolved).length
  const critical = source.filter((item) => item.severity === 'critical').length
  const resolved = source.filter((item) => item.is_resolved).length
  const devices = new Set(source.map((item) => item.device_id)).size

  return [
    {
      label: '活跃告警',
      value: String(active),
      helper: active > 0 ? '需优先处理持续异常' : '当前没有持续异常',
      tone: active > 0 ? 'danger' : 'success',
    },
    {
      label: '严重告警',
      value: String(critical),
      helper: critical > 0 ? '建议优先检查影响范围' : '暂无严重级别',
      tone: critical > 0 ? 'danger' : 'info',
    },
    {
      label: '已恢复告警',
      value: String(resolved),
      helper: resolved > 0 ? '可继续复盘处理记录' : '暂无恢复记录',
      tone: 'success',
    },
    {
      label: '涉及设备',
      value: String(devices),
      helper: devices > 0 ? '当前结果集影响设备数' : '暂无设备影响',
      tone: devices > 0 ? 'warning' : 'info',
    },
  ]
})

const trendPoints = computed<TrendPoint[]>(() => {
  const formatter = new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit' })
  const buckets = new Map<string, TrendPoint>()

  for (let index = 6; index >= 0; index -= 1) {
    const date = new Date()
    date.setDate(date.getDate() - index)
    const key = date.toISOString().slice(0, 10)
    buckets.set(key, {
      label: formatter.format(date),
      total: 0,
      critical: 0,
      warning: 0,
    })
  }

  filteredAlarms.value.forEach((alarm) => {
    const key = alarm.timestamp?.slice(0, 10)
    if (!key || !buckets.has(key)) return
    const bucket = buckets.get(key)
    if (!bucket) return
    bucket.total += 1
    if (alarm.severity === 'critical') bucket.critical += 1
    if (alarm.severity === 'warning') bucket.warning += 1
  })

  return Array.from(buckets.values())
})

const maxTrendValue = computed(() => {
  const max = Math.max(...trendPoints.value.map((item) => item.total), 1)
  return max
})

const latestAlarm = computed(() => filteredAlarms.value[0] || null)

function handlingText(alarm: Alarm) {
  if (alarm.handling_note) return alarm.handling_note
  if (alarm.resolved_by) return `处理人：${alarm.resolved_by}`
  if (alarm.resolved_at) return `恢复时间：${formatDateTime(alarm.resolved_at)}`
  return '待处理'
}

async function loadDevices() {
  try {
    deviceList.value = await getDevices()
  } catch {
    // 由 axios 拦截器统一提示
  }
}

async function loadAlarms() {
  loading.value = true
  applyDateRange()

  try {
    alarms.value = await getAlarms({
      device_id: filters.device_id,
      start_time: filters.start_time,
      end_time: filters.end_time,
      limit: filters.limit,
    })
    refreshedAt.value = new Date().toISOString()
  } finally {
    loading.value = false
  }
}

async function handleResolve(alarm: Alarm) {
  resolving.value = alarm.id
  try {
    await resolveAlarm(alarm.id)
    ElMessage.success('告警已处理')
    await loadAlarms()
  } finally {
    resolving.value = null
  }
}

async function handleResolveAll() {
  bulkResolving.value = true
  try {
    const response = await resolveAllAlarms()
    ElMessage.success(response.message || '未恢复告警已批量处理')
    await loadAlarms()
  } finally {
    bulkResolving.value = false
  }
}

function resetControls() {
  searchTerm.value = ''
  filterStatus.value = 'all'
  filterSeverity.value = 'all'
  filters.device_id = undefined
  filters.limit = 80
  dateRange.value = []
  applyDateRange()
  void loadAlarms()
}

function tableRowClassName({ row }: { row: Alarm }) {
  if (row.is_resolved) return 'alarm-row is-resolved'
  if (row.severity === 'critical') return 'alarm-row is-critical'
  if (row.severity === 'warning') return 'alarm-row is-warning'
  return 'alarm-row'
}

onMounted(async () => {
  await Promise.all([loadDevices(), loadAlarms()])
})
</script>

<template>
  <div class="alarm-center-page">
    <div class="page-shell">
      <section class="page-header">
        <div>
          <h1>告警中心</h1>
          <p>实时监测园区能源系统异常，集中查看活跃、恢复与历史处理记录。</p>
        </div>
        <div class="header-meta">
          <div class="meta-chip">
            <el-icon><Bell /></el-icon>
            <span>最近更新：{{ formatRelativeTime(refreshedAt) }}</span>
          </div>
          <el-button
            plain
            :loading="loading"
            @click="loadAlarms"
          >
            刷新列表
          </el-button>
          <el-button
            type="danger"
            :disabled="!hasActiveAlarms"
            :loading="bulkResolving"
            @click="handleResolveAll"
          >
            一键处理未恢复告警
          </el-button>
        </div>
      </section>

      <section class="metrics-grid">
        <article
          v-for="item in metrics"
          :key="item.label"
          class="metric-card"
          :class="`tone-${item.tone}`"
        >
          <span class="metric-label">{{ item.label }}</span>
          <strong class="metric-value">{{ item.value }}</strong>
          <p>{{ item.helper }}</p>
        </article>
      </section>

      <section class="trend-panel">
        <div class="panel-title-row">
          <div>
            <h3>近 7 日告警趋势</h3>
            <p>按当前筛选结果统计每日告警数量，便于观察异常波动。</p>
          </div>
          <div
            v-if="latestAlarm"
            class="trend-highlight"
          >
            <span>最新告警</span>
            <strong>{{ formatRelativeTime(latestAlarm.timestamp) }}</strong>
            <small>{{ resolveDeviceName(latestAlarm.device_id) }}</small>
          </div>
        </div>

        <div class="trend-chart">
          <div
            v-for="point in trendPoints"
            :key="point.label"
            class="trend-column"
          >
            <div class="bar-track">
              <div
                class="bar-total"
                :style="{ height: `${(point.total / maxTrendValue) * 100}%` }"
              >
                <span>{{ point.total }}</span>
              </div>
            </div>
            <div class="bar-detail">
              <small>严 {{ point.critical }}</small>
              <small>预 {{ point.warning }}</small>
            </div>
            <strong>{{ point.label }}</strong>
          </div>
        </div>
      </section>

      <section class="controls-panel">
        <div class="panel-title-row">
          <div>
            <h3>筛选与检索</h3>
            <p>参考 Figma 版式收敛为“搜索 + 状态 + 严重级别 + 设备与时间窗口”。</p>
          </div>
          <el-button
            link
            @click="resetControls"
          >
            重置筛选
          </el-button>
        </div>

        <div class="controls-grid">
          <label class="field search-field">
            <span>搜索告警</span>
            <div class="search-box">
              <el-icon class="search-icon"><Search /></el-icon>
              <input
                v-model="searchTerm"
                type="text"
                placeholder="搜索告警内容、设备名称或来源"
              >
            </div>
          </label>

          <label class="field">
            <span>严重级别</span>
            <select v-model="filterSeverity">
              <option value="all">全部级别</option>
              <option value="critical">严重</option>
              <option value="warning">预警</option>
              <option value="info">提示</option>
            </select>
          </label>

          <label class="field">
            <span>处理状态</span>
            <select v-model="filterStatus">
              <option value="all">全部状态</option>
              <option value="active">未恢复</option>
              <option value="resolved">已恢复</option>
            </select>
          </label>

          <label class="field">
            <span>设备范围</span>
            <el-select
              v-model="filters.device_id"
              clearable
              filterable
              placeholder="全部设备"
              teleported
              popper-class="app-select-popper"
            >
              <el-option
                v-for="device in deviceList"
                :key="device.id"
                :label="device.name"
                :value="device.id"
              />
            </el-select>
          </label>

          <label class="field range-field">
            <span>时间窗口</span>
            <el-date-picker
              v-model="dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              value-format="YYYY-MM-DDTHH:mm:ss"
            />
          </label>

          <label class="field limit-field">
            <span>记录条数</span>
            <el-input-number
              v-model="filters.limit"
              :min="10"
              :max="100"
              :step="10"
            />
          </label>

          <div class="field action-field">
            <span>执行查询</span>
            <el-button
              type="primary"
              :loading="loading"
              @click="loadAlarms"
            >
              查询告警
            </el-button>
          </div>
        </div>
      </section>

      <section class="list-panel">
        <div class="panel-title-row">
          <div>
            <h3>告警列表</h3>
            <p>当前结果 {{ filteredAlarms.length }} 条，支持直接处理未恢复告警。</p>
          </div>
        </div>

        <el-table
          v-loading="loading"
          :data="filteredAlarms"
          class="alarm-table"
          :row-class-name="tableRowClassName"
        >
          <el-table-column
            label="告警内容"
            min-width="340"
          >
            <template #default="{ row }">
              <div class="alarm-main-cell">
                <div class="alarm-main-top">
                  <el-tag
                    size="small"
                    effect="dark"
                    :type="severityTagType(row.severity)"
                  >
                    {{ severityLabel(row.severity) }}
                  </el-tag>
                  <span class="alarm-time">{{ formatDateTime(row.timestamp) }}</span>
                </div>
                <strong>{{ row.message }}</strong>
                <p>
                  {{ row.category || '通用告警' }}
                  <span v-if="row.source">· {{ row.source }}</span>
                </p>
              </div>
            </template>
          </el-table-column>

          <el-table-column
            label="设备"
            min-width="220"
          >
            <template #default="{ row }">
              <div class="device-cell">
                <strong>{{ resolveDeviceName(row.device_id) }}</strong>
                <small>ID {{ row.device_id }}</small>
              </div>
            </template>
          </el-table-column>

          <el-table-column
            label="状态"
            width="120"
          >
            <template #default="{ row }">
              <el-tag
                size="small"
                :type="row.is_resolved ? 'success' : 'danger'"
              >
                {{ row.is_resolved ? '已恢复' : '未恢复' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column
            label="处理信息"
            min-width="250"
          >
            <template #default="{ row }">
              <div class="handling-cell">
                <strong>{{ handlingText(row) }}</strong>
                <small>{{ row.resolved_by || '等待人工处置' }}</small>
              </div>
            </template>
          </el-table-column>

          <el-table-column
            label="操作"
            width="150"
            fixed="right"
          >
            <template #default="{ row }">
              <el-button
                size="small"
                type="primary"
                :disabled="row.is_resolved"
                :loading="resolving === row.id"
                @click="handleResolve(row)"
              >
                标记已处理
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>
  </div>
</template>

<style scoped>
.alarm-center-page {
  min-height: 100%;
  background: transparent;
}

.page-shell {
  display: grid;
  gap: 20px;
}

.page-header,
.metric-card,
.trend-panel,
.controls-panel,
.list-panel {
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 0.76));
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.24);
}

.page-header,
.trend-panel,
.controls-panel,
.list-panel {
  border-radius: 24px;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.page-header h1,
.panel-title-row h3 {
  margin: 0;
  color: #f8fafc;
}

.page-header h1 {
  font-size: 30px;
  letter-spacing: -0.03em;
}

.page-header p,
.panel-title-row p,
.metric-card p,
.alarm-main-cell p,
.device-cell small,
.handling-cell small {
  margin: 0;
  color: #94a3b8;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.56);
  color: #cbd5e1;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  border-radius: 20px;
  padding: 18px 20px;
  display: grid;
  gap: 10px;
}

.metric-card.tone-danger {
  border-color: rgba(248, 113, 113, 0.28);
}

.metric-card.tone-warning {
  border-color: rgba(251, 191, 36, 0.24);
}

.metric-card.tone-success {
  border-color: rgba(74, 222, 128, 0.24);
}

.metric-card.tone-info {
  border-color: rgba(96, 165, 250, 0.24);
}

.metric-label {
  font-size: 13px;
  color: #94a3b8;
}

.metric-value {
  font-size: 34px;
  line-height: 1;
  color: #f8fafc;
}

.panel-title-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.trend-highlight {
  display: grid;
  justify-items: end;
  gap: 4px;
  padding: 10px 14px;
  border-radius: 18px;
  border: 1px solid rgba(248, 113, 113, 0.16);
  background: rgba(15, 23, 42, 0.55);
}

.trend-highlight span,
.trend-highlight small {
  color: #94a3b8;
}

.trend-highlight strong {
  color: #f8fafc;
}

.trend-chart {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 14px;
  align-items: end;
  min-height: 240px;
}

.trend-column {
  display: grid;
  gap: 10px;
  justify-items: center;
}

.bar-track {
  width: 100%;
  height: 180px;
  border-radius: 18px;
  padding: 12px;
  display: flex;
  align-items: end;
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.65));
}

.bar-total {
  width: 100%;
  min-height: 18px;
  border-radius: 14px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 8px;
  background: linear-gradient(180deg, rgba(248, 113, 113, 0.92), rgba(239, 68, 68, 0.36));
  color: #fff;
  transition: height 0.25s ease;
}

.bar-detail {
  display: flex;
  gap: 10px;
  color: #94a3b8;
}

.trend-column strong {
  color: #cbd5e1;
  font-size: 13px;
}

.controls-grid {
  display: grid;
  grid-template-columns: 1.4fr repeat(3, minmax(0, 1fr));
  gap: 14px;
  align-items: end;
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  font-size: 13px;
  color: #94a3b8;
}

.search-field {
  grid-column: span 2;
}

.range-field {
  grid-column: span 2;
}

.search-box,
.field select {
  min-height: 40px;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(15, 23, 42, 0.72);
  color: #e2e8f0;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
}

.search-box input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  color: inherit;
  font: inherit;
}

.search-box input::placeholder {
  color: #64748b;
}

.search-icon {
  color: #64748b;
}

.field select {
  padding: 0 14px;
  outline: none;
}

.action-field :deep(.el-button) {
  width: 100%;
  min-height: 40px;
}

.alarm-table {
  --el-table-border-color: rgba(148, 163, 184, 0.1);
  --el-table-tr-bg-color: transparent;
  --el-table-bg-color: transparent;
  --el-table-header-bg-color: rgba(15, 23, 42, 0.6);
  --el-table-row-hover-bg-color: rgba(30, 41, 59, 0.48);
  --el-table-text-color: #cbd5e1;
  --el-table-header-text-color: #94a3b8;
}

:deep(.alarm-table .el-table__inner-wrapper::before) {
  display: none;
}

:deep(.alarm-table .el-table__row td) {
  background: transparent;
}

:deep(.alarm-table .is-critical td) {
  background: linear-gradient(90deg, rgba(127, 29, 29, 0.16), rgba(15, 23, 42, 0));
}

:deep(.alarm-table .is-warning td) {
  background: linear-gradient(90deg, rgba(120, 53, 15, 0.18), rgba(15, 23, 42, 0));
}

:deep(.alarm-table .is-resolved td) {
  opacity: 0.82;
}

.alarm-main-cell,
.device-cell,
.handling-cell {
  display: grid;
  gap: 8px;
}

.alarm-main-top {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.alarm-main-cell strong,
.device-cell strong,
.handling-cell strong {
  color: #f8fafc;
}

.alarm-time {
  color: #94a3b8;
  font-size: 12px;
}

@media (max-width: 1280px) {
  .metrics-grid,
  .trend-chart {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .controls-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .search-field,
  .range-field {
    grid-column: span 2;
  }
}

@media (max-width: 900px) {
  .page-header,
  .panel-title-row,
  .metrics-grid,
  .trend-chart,
  .controls-grid {
    grid-template-columns: 1fr;
    display: grid;
  }

  .header-meta {
    justify-content: flex-start;
  }

  .search-field,
  .range-field {
    grid-column: span 1;
  }
}
</style>
