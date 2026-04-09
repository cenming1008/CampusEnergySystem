<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bell, CircleCloseFilled, InfoFilled, RefreshRight, WarningFilled } from '@element-plus/icons-vue'

import { getAlarms, resolveAlarm, resolveAllAlarms, type Alarm } from '@/api/alarm'
import { getDevices, type Device } from '@/api/device'
import { echarts } from '@/shared/lib/echarts'

// ─── State ────────────────────────────────────────────────────────────────────

const loading = ref(false)
const resolving = ref<number | null>(null)
const bulkResolving = ref(false)
const alarms = ref<Alarm[]>([])
const deviceList = ref<Device[]>([])
const autoRefresh = ref(true)
const detailDrawer = ref(false)
const selectedAlarm = ref<Alarm | null>(null)
const resolveDialogVisible = ref(false)
const resolveTarget = ref<Alarm | null>(null)
const handlingNote = ref('')
const bulkNoteDialogVisible = ref(false)
const bulkHandlingNote = ref('')
let refreshTimer: ReturnType<typeof setInterval> | null = null

// Chart ref
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: ReturnType<typeof echarts.init> | null = null

const filters = reactive<{
  device_id?: number
  severity?: string
  resolved?: boolean
  start_time?: string
  end_time?: string
  limit: number
}>({
  resolved: false,
  limit: 100,
})

// ─── Computed ──────────────────────────────────────────────────────────────────

const stats = computed(() => {
  const list = alarms.value
  const active = list.filter(a => !a.is_resolved)
  return {
    active: active.length,
    critical: active.filter(a => a.severity === 'critical').length,
    warning: active.filter(a => a.severity === 'warning').length,
    info: active.filter(a => a.severity === 'info' || !a.severity).length,
    resolved: list.filter(a => a.is_resolved).length,
  }
})

const hasActiveAlarms = computed(() => alarms.value.some(item => !item.is_resolved))

const categories = computed(() => {
  const cats = new Set(alarms.value.map(a => a.category).filter(Boolean) as string[])
  return Array.from(cats)
})

// ─── Helpers ──────────────────────────────────────────────────────────────────

function resolveDeviceName(deviceId: number) {
  return deviceList.value.find(item => item.id === deviceId)?.name ?? `设备 ${deviceId}`
}

function severityTagType(severity?: string): 'danger' | 'warning' | 'info' | 'success' {
  if (severity === 'critical') return 'danger'
  if (severity === 'warning') return 'warning'
  return 'info'
}

function severityLabel(severity?: string) {
  if (severity === 'critical') return '严重'
  if (severity === 'warning') return '警告'
  return '提示'
}

function categoryLabel(category?: string) {
  const map: Record<string, string> = {
    current_overload: '电流过载',
    voltage_out_of_range: '电压异常',
    threshold: '阈值告警',
  }
  return category ? (map[category] ?? category) : '-'
}

function formatDateTime(ts?: string | null) {
  if (!ts) return '-'
  try {
    return new Date(ts).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return ts
  }
}

function rowClassName({ row }: { row: Alarm }) {
  if (row.is_resolved) return 'row-resolved'
  if (row.severity === 'critical') return 'row-critical'
  if (row.severity === 'warning') return 'row-warning'
  return ''
}

// ─── Chart ────────────────────────────────────────────────────────────────────

function buildChartOption() {
  const hourMap: Record<string, { critical: number; warning: number; info: number }> = {}
  const labels: string[] = []
  const now = new Date()

  for (let i = 23; i >= 0; i--) {
    const h = new Date(now.getTime() - i * 3_600_000)
    const key = `${String(h.getMonth() + 1).padStart(2, '0')}/${String(h.getDate()).padStart(2, '0')} ${String(h.getHours()).padStart(2, '0')}:00`
    hourMap[key] = { critical: 0, warning: 0, info: 0 }
    labels.push(key)
  }

  alarms.value.forEach(alarm => {
    const d = new Date(alarm.timestamp)
    const key = `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:00`
    if (hourMap[key]) {
      const sev = alarm.severity ?? 'info'
      if (sev === 'critical') hourMap[key].critical++
      else if (sev === 'warning') hourMap[key].warning++
      else hourMap[key].info++
    }
  })

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#1e293b',
      borderColor: '#334155',
      textStyle: { color: '#cbd5e1' },
    },
    legend: {
      data: ['严重', '警告', '提示'],
      textStyle: { color: '#94a3b8', fontSize: 12 },
      right: 0,
    },
    grid: { left: 8, right: 8, bottom: 0, top: 32, containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        color: '#64748b',
        fontSize: 11,
        interval: Math.floor(labels.length / 6),
        rotate: 0,
      },
      axisLine: { lineStyle: { color: '#334155' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#64748b', fontSize: 11 },
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
    },
    series: [
      {
        name: '严重',
        type: 'bar',
        stack: 'alarms',
        barMaxWidth: 24,
        data: labels.map(k => hourMap[k].critical),
        itemStyle: { color: '#ef4444' },
        emphasis: { itemStyle: { color: '#dc2626' } },
      },
      {
        name: '警告',
        type: 'bar',
        stack: 'alarms',
        barMaxWidth: 24,
        data: labels.map(k => hourMap[k].warning),
        itemStyle: { color: '#f59e0b' },
        emphasis: { itemStyle: { color: '#d97706' } },
      },
      {
        name: '提示',
        type: 'bar',
        stack: 'alarms',
        barMaxWidth: 24,
        data: labels.map(k => hourMap[k].info),
        itemStyle: { color: '#3b82f6' },
        emphasis: { itemStyle: { color: '#2563eb' } },
      },
    ],
  }
}

async function renderChart() {
  await nextTick()
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  chartInstance.setOption(buildChartOption(), { notMerge: true })
}

function handleChartResize() {
  chartInstance?.resize()
}

// ─── Data Loading ─────────────────────────────────────────────────────────────

async function loadDevices() {
  try {
    deviceList.value = await getDevices()
  } catch { /* axios interceptor handles errors */ }
}

async function loadAlarms() {
  loading.value = true
  try {
    alarms.value = await getAlarms({
      device_id: filters.device_id,
      severity: filters.severity || undefined,
      resolved: filters.resolved,
      start_time: filters.start_time,
      end_time: filters.end_time,
      limit: filters.limit,
    })
    await renderChart()
  } finally {
    loading.value = false
  }
}

// ─── Actions ──────────────────────────────────────────────────────────────────

function openResolveDialog(alarm: Alarm, event: Event) {
  event.stopPropagation()
  resolveTarget.value = alarm
  handlingNote.value = ''
  resolveDialogVisible.value = true
}

async function confirmResolve() {
  if (!resolveTarget.value) return
  resolving.value = resolveTarget.value.id
  resolveDialogVisible.value = false
  try {
    await resolveAlarm(resolveTarget.value.id, handlingNote.value || undefined)
    ElMessage.success('报警已处理')
    await loadAlarms()
  } finally {
    resolving.value = null
    resolveTarget.value = null
  }
}

function openBulkResolveDialog() {
  bulkHandlingNote.value = ''
  bulkNoteDialogVisible.value = true
}

async function confirmBulkResolve() {
  bulkNoteDialogVisible.value = false
  bulkResolving.value = true
  try {
    const response = await resolveAllAlarms(bulkHandlingNote.value || undefined)
    ElMessage.success(response.message || '报警已批量处理')
    await loadAlarms()
  } finally {
    bulkResolving.value = false
  }
}

function openDetail(alarm: Alarm) {
  selectedAlarm.value = alarm
  detailDrawer.value = true
}

// ─── Auto Refresh ─────────────────────────────────────────────────────────────

function startAutoRefresh() {
  if (refreshTimer) return
  refreshTimer = setInterval(loadAlarms, 30_000)
}

function stopAutoRefresh() {
  if (!refreshTimer) return
  clearInterval(refreshTimer)
  refreshTimer = null
}

watch(autoRefresh, val => {
  if (val) startAutoRefresh()
  else stopAutoRefresh()
})

// ─── Lifecycle ────────────────────────────────────────────────────────────────

onMounted(async () => {
  await Promise.all([loadDevices(), loadAlarms()])
  startAutoRefresh()
  window.addEventListener('resize', handleChartResize)
})

onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('resize', handleChartResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<template>
  <div class="alarm-center">

    <!-- ─── Header ─────────────────────────────────────────────────────────── -->
    <div class="page-header">
      <div class="header-left">
        <h2>告警中心</h2>
        <p>集中查看未处理、已恢复和历史告警，支持多维筛选。</p>
      </div>
      <div class="header-actions">
        <el-tooltip
          :content="autoRefresh ? '点击关闭自动刷新 (30s)' : '点击开启自动刷新 (30s)'"
          placement="bottom"
        >
          <el-button
            :type="autoRefresh ? 'success' : 'default'"
            :icon="RefreshRight"
            circle
            @click="autoRefresh = !autoRefresh"
          />
        </el-tooltip>
        <el-button
          type="danger"
          :disabled="!hasActiveAlarms"
          :loading="bulkResolving"
          @click="openBulkResolveDialog"
        >
          一键处理全部
        </el-button>
      </div>
    </div>

    <!-- ─── Stats Cards ────────────────────────────────────────────────────── -->
    <div class="stats-row">
      <div class="stat-card stat-active">
        <div class="stat-icon">
          <el-icon size="22"><Bell /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.active }}</div>
          <div class="stat-label">活跃告警</div>
        </div>
      </div>
      <div class="stat-card stat-critical">
        <div class="stat-icon">
          <el-icon size="22"><CircleCloseFilled /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.critical }}</div>
          <div class="stat-label">严重</div>
        </div>
      </div>
      <div class="stat-card stat-warning">
        <div class="stat-icon">
          <el-icon size="22"><WarningFilled /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.warning }}</div>
          <div class="stat-label">警告</div>
        </div>
      </div>
      <div class="stat-card stat-info">
        <div class="stat-icon">
          <el-icon size="22"><InfoFilled /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.info }}</div>
          <div class="stat-label">提示</div>
        </div>
      </div>
      <div class="stat-card stat-resolved">
        <div class="stat-icon stat-check">✓</div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.resolved }}</div>
          <div class="stat-label">已处理</div>
        </div>
      </div>
    </div>

    <!-- ─── Trend Chart ────────────────────────────────────────────────────── -->
    <el-card shadow="never" class="chart-card">
      <template #header>
        <span class="card-title">近 24 小时告警趋势</span>
      </template>
      <div
        ref="chartRef"
        class="chart-container"
      />
    </el-card>

    <!-- ─── Filter + Table ────────────────────────────────────────────────── -->
    <el-card shadow="never">
      <div class="filters">
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

        <el-select
          v-model="filters.severity"
          clearable
          placeholder="严重级别"
          teleported
          popper-class="app-select-popper"
        >
          <el-option
            label="严重"
            value="critical"
          />
          <el-option
            label="警告"
            value="warning"
          />
          <el-option
            label="提示"
            value="info"
          />
        </el-select>

        <el-select
          v-model="filters.resolved"
          clearable
          placeholder="报警状态"
          teleported
          popper-class="app-select-popper"
        >
          <el-option
            label="仅活跃"
            :value="false"
          />
          <el-option
            label="仅已处理"
            :value="true"
          />
        </el-select>

        <el-date-picker
          v-model="filters.start_time"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          placeholder="开始时间"
        />
        <el-date-picker
          v-model="filters.end_time"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          placeholder="结束时间"
        />

        <el-input-number
          v-model="filters.limit"
          :min="10"
          :max="500"
          :step="50"
        />

        <el-button
          type="primary"
          :loading="loading"
          @click="loadAlarms"
        >
          查询
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="alarms"
        :row-class-name="rowClassName"
        row-key="id"
        class="alarm-table"
        @row-click="openDetail"
      >
        <!-- Severity indicator bar -->
        <el-table-column
          width="6"
          class-name="severity-bar-col"
        >
          <template #default="{ row }">
            <div :class="['severity-bar', `severity-bar--${row.severity ?? 'info'}`]" />
          </template>
        </el-table-column>

        <el-table-column
          label="严重级别"
          width="100"
        >
          <template #default="{ row }">
            <el-tag
              :type="severityTagType(row.severity)"
              size="small"
              effect="dark"
            >
              {{ severityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          label="告警时间"
          min-width="170"
        >
          <template #default="{ row }">
            <span class="mono">{{ formatDateTime(row.timestamp) }}</span>
          </template>
        </el-table-column>

        <el-table-column
          label="设备"
          min-width="150"
        >
          <template #default="{ row }">
            {{ resolveDeviceName(row.device_id) }}
          </template>
        </el-table-column>

        <el-table-column
          label="类别"
          width="130"
        >
          <template #default="{ row }">
            <span class="category-text">{{ categoryLabel(row.category) }}</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="message"
          label="告警内容"
          min-width="240"
          show-overflow-tooltip
        />

        <el-table-column
          label="最后触发"
          min-width="170"
        >
          <template #default="{ row }">
            <span class="mono dim">{{ formatDateTime(row.last_seen_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column
          label="状态"
          width="110"
        >
          <template #default="{ row }">
            <el-tag
              :type="row.is_resolved ? 'success' : (row.recovered_at ? 'warning' : 'danger')"
              size="small"
            >
              {{
                row.is_resolved
                  ? '已处理'
                  : row.recovered_at
                    ? '已恢复'
                    : '活跃'
              }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          label="处理人"
          width="110"
        >
          <template #default="{ row }">
            <span>{{ row.resolved_by ?? '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column
          label="操作"
          width="100"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              :disabled="row.is_resolved"
              :loading="resolving === row.id"
              @click="openResolveDialog(row, $event)"
            >
              处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div
        v-if="!loading && alarms.length === 0"
        class="empty-state"
      >
        <el-icon
          size="48"
          color="#22c55e"
        >
          <Bell />
        </el-icon>
        <p>当前无告警记录</p>
      </div>
    </el-card>

    <!-- ─── Detail Drawer ──────────────────────────────────────────────────── -->
    <el-drawer
      v-model="detailDrawer"
      title="告警详情"
      direction="rtl"
      size="420px"
    >
      <template v-if="selectedAlarm">
        <el-descriptions
          :column="1"
          border
          label-class-name="detail-label"
        >
          <el-descriptions-item label="告警 ID">
            {{ selectedAlarm.id }}
          </el-descriptions-item>
          <el-descriptions-item label="严重级别">
            <el-tag
              :type="severityTagType(selectedAlarm.severity)"
              effect="dark"
              size="small"
            >
              {{ severityLabel(selectedAlarm.severity) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="设备">
            {{ resolveDeviceName(selectedAlarm.device_id) }}
          </el-descriptions-item>
          <el-descriptions-item label="类别">
            {{ categoryLabel(selectedAlarm.category) }}
          </el-descriptions-item>
          <el-descriptions-item label="来源">
            {{ selectedAlarm.source ?? '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="告警内容">
            {{ selectedAlarm.message }}
          </el-descriptions-item>
          <el-descriptions-item label="首次触发">
            {{ formatDateTime(selectedAlarm.timestamp) }}
          </el-descriptions-item>
          <el-descriptions-item label="最后触发">
            {{ formatDateTime(selectedAlarm.last_seen_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="系统恢复">
            {{ formatDateTime(selectedAlarm.recovered_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag
              :type="selectedAlarm.is_resolved ? 'success' : (selectedAlarm.recovered_at ? 'warning' : 'danger')"
              size="small"
            >
              {{
                selectedAlarm.is_resolved
                  ? '已处理'
                  : selectedAlarm.recovered_at
                    ? '已恢复'
                    : '活跃'
              }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item
            v-if="selectedAlarm.is_resolved"
            label="处理时间"
          >
            {{ formatDateTime(selectedAlarm.resolved_at) }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="selectedAlarm.is_resolved"
            label="处理人"
          >
            {{ selectedAlarm.resolved_by ?? '-' }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="selectedAlarm.handling_note"
            label="处理备注"
          >
            {{ selectedAlarm.handling_note }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="selectedAlarm.instance_key"
            label="实例键"
          >
            <span class="mono dim">{{ selectedAlarm.instance_key }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <div
          v-if="!selectedAlarm.is_resolved"
          class="drawer-footer"
        >
          <el-button
            type="primary"
            :loading="resolving === selectedAlarm.id"
            @click="openResolveDialog(selectedAlarm, $event); detailDrawer = false"
          >
            处理此告警
          </el-button>
        </div>
      </template>
    </el-drawer>

    <!-- ─── Single Resolve Dialog ──────────────────────────────────────────── -->
    <el-dialog
      v-model="resolveDialogVisible"
      title="处理告警"
      width="440px"
      :close-on-click-modal="false"
    >
      <template v-if="resolveTarget">
        <p class="dialog-alarm-msg">
          <el-tag
            :type="severityTagType(resolveTarget.severity)"
            effect="dark"
            size="small"
          >
            {{ severityLabel(resolveTarget.severity) }}
          </el-tag>
          &nbsp;{{ resolveTarget.message }}
        </p>
        <el-form label-position="top">
          <el-form-item label="处理备注（可选）">
            <el-input
              v-model="handlingNote"
              type="textarea"
              :rows="3"
              placeholder="填写处理说明或措施..."
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="resolveDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmResolve"
        >
          确认处理
        </el-button>
      </template>
    </el-dialog>

    <!-- ─── Bulk Resolve Dialog ────────────────────────────────────────────── -->
    <el-dialog
      v-model="bulkNoteDialogVisible"
      title="一键处理全部活跃告警"
      width="440px"
      :close-on-click-modal="false"
    >
      <p class="dialog-warn-text">
        将批量处理当前 <strong>{{ stats.active }}</strong> 条活跃告警，该操作不可撤销。
      </p>
      <el-form label-position="top">
        <el-form-item label="处理备注（可选）">
          <el-input
            v-model="bulkHandlingNote"
            type="textarea"
            :rows="3"
            placeholder="填写统一处理说明..."
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bulkNoteDialogVisible = false">取消</el-button>
        <el-button
          type="danger"
          :loading="bulkResolving"
          @click="confirmBulkResolve"
        >
          确认批量处理
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>

<style scoped>
/* ─── Layout ──────────────────────────────────────────────────────────────── */
.alarm-center {
  display: grid;
  gap: 16px;
}

/* ─── Header ──────────────────────────────────────────────────────────────── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.page-header h2,
.page-header p {
  margin: 0;
}

.page-header p {
  margin-top: 6px;
  color: #94a3b8;
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* ─── Stats ───────────────────────────────────────────────────────────────── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-radius: 8px;
  border: 1px solid #1e293b;
  background: #0f172a;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 10px;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}

.stat-active .stat-icon  { background: rgba(99,  102, 241, 0.15); color: #818cf8; }
.stat-critical .stat-icon { background: rgba(239,  68,  68, 0.15); color: #f87171; }
.stat-warning .stat-icon  { background: rgba(245, 158,  11, 0.15); color: #fbbf24; }
.stat-info .stat-icon     { background: rgba( 59, 130, 246, 0.15); color: #60a5fa; }
.stat-resolved .stat-icon { background: rgba( 34, 197,  94, 0.15); color: #4ade80; }

.stat-check { font-size: 22px; }

.stat-value {
  font-size: 26px;
  font-weight: 700;
  line-height: 1;
  color: #f1f5f9;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

/* ─── Chart ───────────────────────────────────────────────────────────────── */
.chart-card :deep(.el-card__header) {
  padding: 12px 20px;
  border-bottom-color: #1e293b;
}

.card-title {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}

.chart-container {
  height: 180px;
  width: 100%;
}

/* ─── Filters ─────────────────────────────────────────────────────────────── */
.filters {
  display: grid;
  grid-template-columns: 160px 120px 120px 1fr 1fr 100px auto;
  gap: 10px;
  margin-bottom: 16px;
  align-items: center;
}

/* ─── Table ───────────────────────────────────────────────────────────────── */
.alarm-table {
  cursor: pointer;
}

.alarm-table :deep(.el-table__row:hover) td {
  background-color: #1e293b !important;
}

.alarm-table :deep(.row-critical) td {
  background-color: rgba(239, 68, 68, 0.05);
}

.alarm-table :deep(.row-warning) td {
  background-color: rgba(245, 158, 11, 0.05);
}

.alarm-table :deep(.row-resolved) td {
  opacity: 0.55;
}

.alarm-table :deep(.severity-bar-col) {
  padding: 0 !important;
}

.severity-bar {
  width: 4px;
  height: 100%;
  min-height: 36px;
  border-radius: 2px;
}

.severity-bar--critical { background: #ef4444; }
.severity-bar--warning  { background: #f59e0b; }
.severity-bar--info     { background: #3b82f6; }

.mono {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 12px;
}

.dim { color: #64748b; }

.category-text {
  font-size: 12px;
  color: #94a3b8;
}

/* ─── Empty State ─────────────────────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 0 32px;
  gap: 12px;
  color: #64748b;
  font-size: 14px;
}

.empty-state p { margin: 0; }

/* ─── Drawer ──────────────────────────────────────────────────────────────── */
.drawer-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #1e293b;
}

:deep(.detail-label) {
  width: 90px;
  color: #64748b;
  font-size: 13px;
}

/* ─── Dialog ──────────────────────────────────────────────────────────────── */
.dialog-alarm-msg {
  margin: 0 0 16px;
  font-size: 14px;
  line-height: 1.6;
  color: #cbd5e1;
}

.dialog-warn-text {
  margin: 0 0 16px;
  font-size: 14px;
  color: #94a3b8;
  line-height: 1.6;
}

.dialog-warn-text strong { color: #f87171; }

/* ─── Responsive ──────────────────────────────────────────────────────────── */
@media (max-width: 1100px) {
  .stats-row {
    grid-template-columns: repeat(3, 1fr);
  }

  .filters {
    grid-template-columns: 1fr 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .filters {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
