<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bell, RefreshRight } from '@element-plus/icons-vue'

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
  <div class="alarm-cockpit">
    <div class="cockpit-noise" />

    <!-- ─── Header ─────────────────────────────────────────────────────────── -->
    <div class="top-header">
      <div class="brand-block">
        <div class="brand-mark">
          <div class="brand-mark__dot" />
        </div>
        <div class="brand-text">
          <p class="brand-kicker">Alarm Center</p>
          <h1>告警中心</h1>
          <p class="brand-subtitle">集中查看未处理、已恢复和历史告警，支持多维筛选。</p>
        </div>
      </div>
      <div class="header-right">
        <el-tooltip
          :content="autoRefresh ? '点击关闭自动刷新 (30s)' : '点击开启自动刷新 (30s)'"
          placement="bottom"
        >
          <button
            type="button"
            class="icon-btn"
            :class="autoRefresh ? 'icon-btn--active' : ''"
            @click="autoRefresh = !autoRefresh"
          >
            <el-icon size="16"><RefreshRight /></el-icon>
            <span>{{ autoRefresh ? '自动刷新' : '已暂停' }}</span>
          </button>
        </el-tooltip>
        <button
          type="button"
          class="action-btn action-btn--danger"
          :disabled="!hasActiveAlarms || bulkResolving"
          @click="openBulkResolveDialog"
        >
          <span v-if="bulkResolving">处理中…</span>
          <span v-else>一键处理全部</span>
        </button>
      </div>
    </div>

    <!-- ─── KPI Strip ──────────────────────────────────────────────────────── -->
    <div class="kpi-strip">
      <div class="kpi-tile" :class="stats.active > 0 ? 'kpi-tile--alarm' : 'kpi-tile--safe'">
        <span class="kpi-tile__label">活跃告警</span>
        <div class="kpi-tile__value">
          <strong>{{ stats.active }}</strong>
          <span class="kpi-tile__unit">条</span>
        </div>
        <span class="kpi-tile__sub">{{ stats.active > 0 ? '需立即处理' : '系统稳定' }}</span>
      </div>
      <div class="kpi-tile kpi-tile--critical">
        <span class="kpi-tile__label">严重</span>
        <div class="kpi-tile__value">
          <strong>{{ stats.critical }}</strong>
          <span class="kpi-tile__unit">条</span>
        </div>
        <span class="kpi-tile__sub">Critical</span>
      </div>
      <div class="kpi-tile kpi-tile--warning">
        <span class="kpi-tile__label">警告</span>
        <div class="kpi-tile__value">
          <strong>{{ stats.warning }}</strong>
          <span class="kpi-tile__unit">条</span>
        </div>
        <span class="kpi-tile__sub">Warning</span>
      </div>
      <div class="kpi-tile kpi-tile--info">
        <span class="kpi-tile__label">提示</span>
        <div class="kpi-tile__value">
          <strong>{{ stats.info }}</strong>
          <span class="kpi-tile__unit">条</span>
        </div>
        <span class="kpi-tile__sub">Info</span>
      </div>
      <div class="kpi-tile kpi-tile--resolved">
        <span class="kpi-tile__label">已处理</span>
        <div class="kpi-tile__value">
          <strong>{{ stats.resolved }}</strong>
          <span class="kpi-tile__unit">条</span>
        </div>
        <span class="kpi-tile__sub">Resolved</span>
      </div>
    </div>

    <!-- ─── Trend Chart ────────────────────────────────────────────────────── -->
    <div class="glass-card chart-glass">
      <p class="card-eyebrow">近 24 小时告警趋势</p>
      <div
        ref="chartRef"
        class="chart-mount"
      />
    </div>

    <!-- ─── Filter + Table ────────────────────────────────────────────────── -->
    <div class="glass-card table-glass">
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
          <el-option label="严重" value="critical" />
          <el-option label="警告" value="warning" />
          <el-option label="提示" value="info" />
        </el-select>

        <el-select
          v-model="filters.resolved"
          clearable
          placeholder="报警状态"
          teleported
          popper-class="app-select-popper"
        >
          <el-option label="仅活跃" :value="false" />
          <el-option label="仅已处理" :value="true" />
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

        <button
          type="button"
          class="action-btn action-btn--primary"
          :disabled="loading"
          @click="loadAlarms"
        >
          {{ loading ? '加载中…' : '查询' }}
        </button>
      </div>

      <el-table
        v-loading="loading"
        :data="alarms"
        :row-class-name="rowClassName"
        row-key="id"
        class="alarm-table"
        @row-click="openDetail"
      >
        <template #empty>
          <div />
        </template>

        <el-table-column width="6" class-name="severity-bar-col">
          <template #default="{ row }">
            <div :class="['severity-bar', `severity-bar--${row.severity ?? 'info'}`]" />
          </template>
        </el-table-column>

        <el-table-column label="严重级别" width="100">
          <template #default="{ row }">
            <el-tag :type="severityTagType(row.severity)" size="small" effect="dark">
              {{ severityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="告警时间" min-width="170">
          <template #default="{ row }">
            <span class="mono">{{ formatDateTime(row.timestamp) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="设备" min-width="150">
          <template #default="{ row }">
            {{ resolveDeviceName(row.device_id) }}
          </template>
        </el-table-column>

        <el-table-column label="类别" width="130">
          <template #default="{ row }">
            <span class="category-text">{{ categoryLabel(row.category) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="message" label="告警内容" min-width="240" show-overflow-tooltip />

        <el-table-column label="最后触发" min-width="170">
          <template #default="{ row }">
            <span class="mono dim">{{ formatDateTime(row.last_seen_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag
              :type="row.is_resolved ? 'success' : (row.recovered_at ? 'warning' : 'danger')"
              size="small"
            >
              {{ row.is_resolved ? '已处理' : row.recovered_at ? '已恢复' : '活跃' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="处理人" width="110">
          <template #default="{ row }">
            <span>{{ row.resolved_by ?? '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <button
              type="button"
              class="resolve-btn"
              :disabled="row.is_resolved || resolving === row.id"
              @click="openResolveDialog(row, $event)"
            >
              {{ resolving === row.id ? '…' : '处理' }}
            </button>
          </template>
        </el-table-column>
      </el-table>

      <div
        v-if="!loading && alarms.length === 0"
        class="empty-state"
      >
        <div class="empty-state__icon">
          <el-icon size="32" color="#34d399"><Bell /></el-icon>
        </div>
        <p>当前无告警记录</p>
        <span>系统运行稳定</span>
      </div>
    </div>

    <!-- ─── Detail Drawer ──────────────────────────────────────────────────── -->
    <el-drawer
      v-model="detailDrawer"
      title="告警详情"
      direction="rtl"
      size="420px"
    >
      <template v-if="selectedAlarm">
        <el-descriptions :column="1" border label-class-name="detail-label">
          <el-descriptions-item label="告警 ID">{{ selectedAlarm.id }}</el-descriptions-item>
          <el-descriptions-item label="严重级别">
            <el-tag :type="severityTagType(selectedAlarm.severity)" effect="dark" size="small">
              {{ severityLabel(selectedAlarm.severity) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="设备">{{ resolveDeviceName(selectedAlarm.device_id) }}</el-descriptions-item>
          <el-descriptions-item label="类别">{{ categoryLabel(selectedAlarm.category) }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ selectedAlarm.source ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="告警内容">{{ selectedAlarm.message }}</el-descriptions-item>
          <el-descriptions-item label="首次触发">{{ formatDateTime(selectedAlarm.timestamp) }}</el-descriptions-item>
          <el-descriptions-item label="最后触发">{{ formatDateTime(selectedAlarm.last_seen_at) }}</el-descriptions-item>
          <el-descriptions-item label="系统恢复">{{ formatDateTime(selectedAlarm.recovered_at) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag
              :type="selectedAlarm.is_resolved ? 'success' : (selectedAlarm.recovered_at ? 'warning' : 'danger')"
              size="small"
            >
              {{ selectedAlarm.is_resolved ? '已处理' : selectedAlarm.recovered_at ? '已恢复' : '活跃' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedAlarm.is_resolved" label="处理时间">
            {{ formatDateTime(selectedAlarm.resolved_at) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedAlarm.is_resolved" label="处理人">
            {{ selectedAlarm.resolved_by ?? '-' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedAlarm.handling_note" label="处理备注">
            {{ selectedAlarm.handling_note }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedAlarm.instance_key" label="实例键">
            <span class="mono dim">{{ selectedAlarm.instance_key }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="!selectedAlarm.is_resolved" class="drawer-footer">
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
          <el-tag :type="severityTagType(resolveTarget.severity)" effect="dark" size="small">
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
        <el-button type="primary" @click="confirmResolve">确认处理</el-button>
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
        <el-button type="danger" :loading="bulkResolving" @click="confirmBulkResolve">
          确认批量处理
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>

<style scoped>
/* ─── Page Container ──────────────────────────────────────────────────────── */
.alarm-cockpit {
  position: relative;
  width: 100%;
  min-height: 100%;
  height: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  overflow-y: auto;
  overflow-x: hidden;
  color: #f5f7fa;
  background:
    radial-gradient(circle at top left,  rgba(239, 68,  68, 0.07), transparent 30%),
    radial-gradient(circle at bottom right, rgba(56, 189, 248, 0.04), transparent 28%),
    #090e17;
  box-sizing: border-box;
}

.cockpit-noise {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(255,255,255,0.012), transparent 20%, transparent 80%, rgba(255,255,255,0.012));
  opacity: 0.3;
  z-index: 0;
}

/* ─── Header ──────────────────────────────────────────────────────────────── */
.top-header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 108px;
  padding: 22px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px) saturate(135%);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06), 0 8px 24px rgba(0,0,0,0.18);
  box-sizing: border-box;
}

.brand-block {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: rgba(248, 113, 113, 0.12);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
  flex-shrink: 0;
  margin-top: 2px;
}

.brand-mark__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #f87171;
  box-shadow: 0 0 12px rgba(248, 113, 113, 0.6);
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.brand-kicker {
  margin: 0;
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.46);
}

.brand-text h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.02;
  letter-spacing: 0;
}

.brand-subtitle {
  margin: 0;
  font-size: 12px;
  color: rgba(255,255,255,0.44);
  line-height: 1.3;
  max-width: 520px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

/* ─── Icon / Action Buttons ───────────────────────────────────────────────── */
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: auto;
  height: auto;
  min-height: 36px;
  padding: 7px 14px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.7);
  font-size: 12px;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.18s;
}

.icon-btn:hover { background: rgba(255,255,255,0.09); }

.icon-btn--active {
  border-color: rgba(52, 211, 153, 0.35);
  background: rgba(52, 211, 153, 0.1);
  color: #6ee7b7;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 7px 18px;
  border-radius: 20px;
  border: 1px solid transparent;
  font-size: 13px;
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: opacity 0.18s, background 0.18s;
}

.action-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.action-btn--primary {
  background: #3b82f6;
  color: #fff;
}
.action-btn--primary:hover:not(:disabled) { background: #2563eb; }

.action-btn--danger {
  background: rgba(239, 68, 68, 0.18);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
}
.action-btn--danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.28);
}

/* ─── KPI Strip ───────────────────────────────────────────────────────────── */
.kpi-strip {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}

.kpi-tile {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 16px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom: 2px solid var(--kpi-accent, rgba(255,255,255,0.1));
  transition: background 0.18s ease;
}

.kpi-tile:hover { background: rgba(255, 255, 255, 0.06); }

.kpi-tile--alarm    { --kpi-accent: #f87171; }
.kpi-tile--safe     { --kpi-accent: #34d399; }
.kpi-tile--critical { --kpi-accent: #f87171; }
.kpi-tile--warning  { --kpi-accent: #fb923c; }
.kpi-tile--info     { --kpi-accent: #38bdf8; }
.kpi-tile--resolved { --kpi-accent: #34d399; }

.kpi-tile__label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.46);
}

.kpi-tile__value {
  display: flex;
  align-items: baseline;
  gap: 5px;
  line-height: 1;
}

.kpi-tile__value strong {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0;
  color: #f0f6ff;
}

.kpi-tile__unit {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.kpi-tile__sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.38);
  margin-top: 2px;
}

.kpi-tile--alarm .kpi-tile__value strong { color: #fca5a5; }
.kpi-tile--safe  .kpi-tile__value strong { color: #86efac; }

/* ─── Glass Card ──────────────────────────────────────────────────────────── */
.glass-card {
  position: relative;
  z-index: 1;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(18px) saturate(145%);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06), 0 10px 28px rgba(0,0,0,0.18);
  padding: 18px 20px;
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}

.glass-card:hover {
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08), 0 14px 32px rgba(0,0,0,0.22);
}

/* ─── Chart ───────────────────────────────────────────────────────────────── */
.card-eyebrow {
  margin: 0 0 14px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.4);
}

.chart-mount {
  height: 180px;
  width: 100%;
}

/* ─── Filters ─────────────────────────────────────────────────────────────── */
.filters {
  display: grid;
  grid-template-columns:
    minmax(150px, 1.1fr)
    minmax(128px, 0.8fr)
    minmax(128px, 0.8fr)
    minmax(170px, 1fr)
    minmax(170px, 1fr)
    116px
    auto;
  gap: 10px;
  margin-bottom: 16px;
  align-items: center;
}

/* El-Select / El-DatePicker deep theming */
.filters > * {
  min-width: 0;
}

.filters :deep(.el-select__wrapper),
.filters :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06) !important;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08) !important;
  border-radius: 8px;
  min-height: 36px;
}

.filters :deep(.el-select__wrapper.is-focused),
.filters :deep(.el-input__wrapper.is-focus) {
  box-shadow: inset 0 0 0 1px rgba(96, 165, 250, 0.5) !important;
}

.filters :deep(.el-select__selected-item),
.filters :deep(.el-select__placeholder),
.filters :deep(.el-input__inner) {
  color: rgba(255, 255, 255, 0.8);
}

.filters :deep(.el-select__placeholder.is-transparent),
.filters :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.filters :deep(.el-date-editor.el-input),
.filters :deep(.el-input-number) {
  width: 100%;
}

.filters :deep(.el-input-number__decrease),
.filters :deep(.el-input-number__increase) {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
}

.filters :deep(.el-select__caret),
.filters :deep(.el-input__prefix),
.filters :deep(.el-input__suffix) {
  color: rgba(255, 255, 255, 0.42);
}

/* ─── Table ───────────────────────────────────────────────────────────────── */
.alarm-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.035);
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.055);
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  --el-table-text-color: rgba(255, 255, 255, 0.82);
  --el-table-header-text-color: rgba(255, 255, 255, 0.46);
  --el-bg-color: transparent;
  --el-fill-color-lighter: rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  cursor: pointer;
  overflow: hidden;
}

.alarm-table :deep(.el-table),
.alarm-table :deep(.el-table__inner-wrapper),
.alarm-table :deep(.el-scrollbar),
.alarm-table :deep(.el-scrollbar__view),
.alarm-table :deep(.el-table__body-wrapper),
.alarm-table :deep(.el-table__header-wrapper) {
  background: transparent;
  color: rgba(255, 255, 255, 0.82);
}

.alarm-table :deep(.el-table__inner-wrapper::before),
.alarm-table :deep(.el-table::before),
.alarm-table :deep(.el-table__border-left-patch) {
  display: none;
}

.alarm-table :deep(th.el-table__cell) {
  background: rgba(255, 255, 255, 0.03);
  color: rgba(255, 255, 255, 0.46);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border-bottom-color: rgba(255, 255, 255, 0.06);
}

.alarm-table :deep(td.el-table__cell) {
  background: transparent !important;
  border-bottom-color: rgba(255, 255, 255, 0.04);
  font-size: 13px;
}

.alarm-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: rgba(255, 255, 255, 0.05) !important;
}

.alarm-table :deep(.row-critical > td.el-table__cell) {
  background: rgba(239, 68, 68, 0.075) !important;
}

.alarm-table :deep(.row-warning > td.el-table__cell) {
  background: rgba(245, 158, 11, 0.07) !important;
}

.alarm-table :deep(.row-resolved > td.el-table__cell) {
  opacity: 0.5;
}

.alarm-table :deep(.el-table-fixed-column--right),
.alarm-table :deep(.el-table-fixed-column--left) {
  background: #101827 !important;
}

.alarm-table :deep(.row-critical .el-table-fixed-column--right),
.alarm-table :deep(.row-critical .el-table-fixed-column--left) {
  background: #1f1721 !important;
}

.alarm-table :deep(.row-warning .el-table-fixed-column--right),
.alarm-table :deep(.row-warning .el-table-fixed-column--left) {
  background: #1d1a18 !important;
}

.alarm-table :deep(.el-table__body tr.hover-row > td.el-table__cell),
.alarm-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: rgba(255, 255, 255, 0.055) !important;
}

.alarm-table :deep(.el-loading-mask) {
  background: rgba(9, 14, 23, 0.7);
}

.alarm-table :deep(.severity-bar-col) {
  padding: 0 !important;
}

.severity-bar {
  width: 4px;
  height: 100%;
  min-height: 44px;
  border-radius: 2px;
}

.severity-bar--critical { background: #ef4444; }
.severity-bar--warning  { background: #f59e0b; }
.severity-bar--info     { background: #3b82f6; }

.mono {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 12px;
}

.dim { color: rgba(255, 255, 255, 0.36); }

.category-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

/* ─── Resolve Button (inline table) ──────────────────────────────────────── */
.resolve-btn {
  min-width: 52px;
  min-height: 30px;
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid rgba(59, 130, 246, 0.35);
  background: rgba(59, 130, 246, 0.12);
  color: #93c5fd;
  font-size: 12px;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.15s;
}

.resolve-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.22);
}

.resolve-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* ─── Empty State ─────────────────────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 52px 0 36px;
  gap: 8px;
}

.empty-state__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: rgba(52, 211, 153, 0.1);
  margin-bottom: 4px;
}

.empty-state p {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
}

.empty-state span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
}

/* ─── Drawer ──────────────────────────────────────────────────────────────── */
.drawer-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

:deep(.detail-label) {
  width: 90px;
  color: rgba(255, 255, 255, 0.4);
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
  .kpi-strip {
    grid-template-columns: repeat(3, 1fr);
  }

  .filters {
    grid-template-columns: 1fr 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .kpi-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .filters {
    grid-template-columns: 1fr 1fr;
  }

  .top-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .brand-text h1 {
    font-size: 22px;
  }

  .header-right {
    width: 100%;
    justify-content: flex-end;
  }
}

/* ─── Drawer dark theme ───────────────────────────────────────────────────── */
:deep(.el-drawer) {
  --el-drawer-bg-color: #0d1420;
  background: #0d1420;
  border-left: 1px solid rgba(255, 255, 255, 0.06);
}

:deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 18px 20px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  color: #f0f6ff;
}

:deep(.el-drawer__title) {
  font-size: 15px;
  font-weight: 600;
  color: #f0f6ff;
}

:deep(.el-drawer__close-btn) {
  color: rgba(255, 255, 255, 0.45) !important;
}
:deep(.el-drawer__close-btn:hover) {
  color: rgba(255, 255, 255, 0.8) !important;
}

:deep(.el-drawer__body) {
  padding: 20px;
  color: rgba(255, 255, 255, 0.82);
}

/* el-descriptions dark overrides (used inside drawer) */
:deep(.el-descriptions__body) {
  background: transparent;
}

:deep(.el-descriptions__cell) {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.07) !important;
  color: rgba(255, 255, 255, 0.82);
  font-size: 13px;
}

:deep(.detail-label.el-descriptions__label) {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.4);
}

/* ─── Dialog dark theme ───────────────────────────────────────────────────── */
:deep(.el-dialog) {
  --el-dialog-bg-color: #111827;
  background: #111827;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 16px;
}

:deep(.el-dialog__header) {
  padding: 20px 22px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-right: 0;
}

:deep(.el-dialog__title) {
  font-size: 15px;
  font-weight: 600;
  color: #f0f6ff;
}

:deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.45);
}
:deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

:deep(.el-dialog__body) {
  padding: 20px 22px;
  color: rgba(255, 255, 255, 0.82);
}

:deep(.el-dialog__footer) {
  padding: 12px 22px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

/* Form items inside dialogs */
:deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
}

:deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05) !important;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.09) !important;
  color: rgba(255, 255, 255, 0.82);
  border-radius: 8px;
}

:deep(.el-textarea__inner::placeholder) {
  color: rgba(255, 255, 255, 0.28);
}

:deep(.el-input__count) {
  background: transparent;
  color: rgba(255, 255, 255, 0.3);
}
</style>
