<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { cleanupData, getCleanupStats, cleanupAllData, type CleanupResult, type CleanupStats } from '@/api/dataCleanup'
import { isDemoModeEnabled, setDemoModeEnabled } from '@/shared/demoMode'

interface MessageResponse {
  message?: string
}

interface SystemStatus {
  status?: string
  timestamp?: string
  version?: string
  services?: {
    database?: string
    redis?: string
    mqtt?: string
    scheduler?: string
  }
  runtime?: {
    counters?: {
      mqtt_duplicates_total?: number
      mqtt_processing_failed_total?: number
    }
  }
  [key: string]: unknown
}

interface IngestionRecord {
  id: number
  topic?: string
  received_at?: string
  status?: string
  payload?: string
  [key: string]: unknown
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) return error.message
  return fallback
}

const cleanupResultLabels: Array<{ key: keyof CleanupResult; label: string }> = [
  { key: 'energy_data', label: '业务时序' },
  { key: 'alarm_data', label: '已解决告警' },
  { key: 'carbon_emission', label: '碳排放记录' },
  { key: 'mqtt_ingestion', label: 'MQTT 接入流水' },
  { key: 'audit_event', label: '审计事件' },
  { key: 'svg_telemetry', label: 'SVG 遥测' },
  { key: 'capacitor_bank_telemetry', label: '电容补偿遥测' },
  { key: 'statistics', label: '统计汇总' },
]

const cleanupStatRows: Array<{ key: keyof CleanupStats; label: string }> = [
  { key: 'energy_data', label: '业务时序' },
  { key: 'mqtt_ingestion', label: 'MQTT 接入流水' },
  { key: 'audit_event', label: '审计事件' },
  { key: 'capacitor_bank_telemetry', label: '电容补偿遥测' },
  { key: 'svg_telemetry', label: 'SVG 遥测' },
  { key: 'carbon_emission', label: '碳排放记录' },
  { key: 'alarm_data', label: '告警记录' },
]

const buildCleanupDetails = (result: CleanupResult) => cleanupResultLabels
  .map(({ key, label }) => ({ label, count: Number(result[key] || 0) }))
  .filter(({ count }) => count > 0)
  .map(({ label, count }) => `${label}: ${count.toLocaleString()} 条`)

const formatCleanupTotal = (stats: CleanupStats | null, key: keyof CleanupStats) => {
  const stat = stats?.[key]
  if (!stat || typeof stat !== 'object' || !('total' in stat)) return '0'
  return Number(stat.total || 0).toLocaleString()
}

const mqttStatusType = (s: string) => {
  if (s === 'success') return ''
  if (s === 'failed' || s === 'dead_letter') return 'danger'
  if (s === 'pending') return 'warning'
  return 'info'
}

const serviceEntries = [
  { key: 'status' as const, label: '系统', getValue: (s: SystemStatus) => s.status },
  { key: 'database' as const, label: '数据库', getValue: (s: SystemStatus) => s.services?.database },
  { key: 'redis' as const, label: 'Redis', getValue: (s: SystemStatus) => s.services?.redis },
  { key: 'mqtt' as const, label: 'MQTT', getValue: (s: SystemStatus) => s.services?.mqtt },
  { key: 'scheduler' as const, label: '调度器', getValue: (s: SystemStatus) => s.services?.scheduler },
]

const techStack = ['Vue 3', 'TypeScript', 'Element Plus', 'ECharts', 'FastAPI', 'TimescaleDB', 'Redis', 'MQTT']

// --- 状态 ---
const systemStatus = ref<SystemStatus | null>(null)
const metricsText = ref('')
const ingestionRecords = ref<IngestionRecord[]>([])
const ingestionLoading = ref(false)
const demoModeEnabled = ref(isDemoModeEnabled())

const cleanupHours = ref(1)
const cleanupLoading = ref(false)
const cleanupAllLoading = ref(false)
const cleanupStats = ref<CleanupStats | null>(null)

const healthyServiceCount = computed(() => {
  if (!systemStatus.value) return 0
  return serviceEntries.filter((svc) => svc.getValue(systemStatus.value as SystemStatus) === 'healthy').length
})

const cleanupTotalCount = computed(() => {
  if (!cleanupStats.value) return 0
  return cleanupStatRows.reduce((sum, row) => {
    const stat = cleanupStats.value?.[row.key]
    if (!stat || typeof stat !== 'object' || !('total' in stat)) return sum
    return sum + Number(stat.total || 0)
  }, 0)
})

const ingestionIssueCount = computed(() => (
  ingestionRecords.value.filter((item) => ['failed', 'dead_letter'].includes(String(item.status))).length
))

const metricsLineCount = computed(() => (
  String(metricsText.value || '').split('\n').filter((line) => line.trim() && !line.startsWith('#')).length
))

const demoModeStatusText = computed(() => (
  demoModeEnabled.value ? '已开启，使用演示数据' : '已关闭，不使用演示数据'
))

const handleDemoModeChange = (enabled: boolean) => {
  demoModeEnabled.value = enabled
  setDemoModeEnabled(enabled)
  ElMessage.success(enabled ? '已开启演示数据模式，页面即将刷新' : '已关闭演示数据模式，页面即将刷新')
  window.setTimeout(() => {
    window.location.reload()
  }, 350)
}

// --- API 调用 ---
const loadSystemStatus = async () => {
  try {
    const res = await request.get<never, SystemStatus>('/health')
    systemStatus.value = res
  } catch {
    // 由 axios 拦截器统一提示
  }
}

const loadMetrics = async () => {
  try {
    const res = await request.get<never, string>('/metrics', { responseType: 'text' })
    metricsText.value = typeof res === 'string' ? res : ''
  } catch {
    metricsText.value = ''
  }
}

const loadIngestionRecords = async () => {
  ingestionLoading.value = true
  try {
    const res = await request.get<never, { items?: IngestionRecord[] }>('/devices/ingestion-records', {
      params: { limit: 20 }
    })
    ingestionRecords.value = res.items || []
  } catch {
    // MQTT 接入记录加载失败
  } finally {
    ingestionLoading.value = false
  }
}

const replayIngestionRecord = async (recordId: number) => {
  try {
    await request.post<Record<string, never>, MessageResponse>(`/devices/ingestion-records/${recordId}/replay`, {})
    ElMessage.success('已触发消息重放')
    await loadIngestionRecords()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '重放失败'))
  }
}

const handleCleanupData = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要清理 ${cleanupHours.value} 小时之前的历史数据和运行流水吗？\n\n此操作将永久删除以下数据：\n- 业务时序数据与碳排放记录\n- 已解决的报警记录\n- MQTT 接入流水与审计事件\n- SVG / 电容补偿控制器遥测\n\n⚠️ 此操作不可恢复！`,
      '警告',
      {
        type: 'warning',
        confirmButtonText: '确定清理',
        cancelButtonText: '取消',
        dangerouslyUseHTMLString: false
      }
    )
  } catch {
    return
  }

  cleanupLoading.value = true
  try {
    const result: CleanupResult = await cleanupData(cleanupHours.value)
    if (result.status === 'success' || result.status === 'partial') {
      const total = result.total_deleted || 0
      const details = buildCleanupDetails(result)
      ElMessage.success({
        message: `清理完成！共删除 ${total} 条记录${details.length ? `（${details.join('，')}）` : ''}`,
        duration: 5000
      })
      await loadCleanupStats()
    } else {
      ElMessage.warning('清理完成，但可能有一些错误')
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '清理失败'))
  } finally {
    cleanupLoading.value = false
  }
}

const loadCleanupStats = async () => {
  try {
    const res = await getCleanupStats()
    cleanupStats.value = res
  } catch {
    // 清理统计加载失败
  }
}

const handleCleanupAllData = async () => {
  try {
    await ElMessageBox.confirm(
      '⚠️ 危险操作警告！\n\n' +
      '此操作将永久删除以下所有数据：\n' +
      '• 所有业务时序数据（EnergyData）\n' +
      '• 所有已解决的报警记录\n' +
      '• 所有碳排放记录和统计汇总\n' +
      '• 所有 MQTT 接入流水和审计事件\n' +
      '• 所有 SVG / 电容补偿控制器遥测\n\n' +
      '设备、用户、位置、控制日志和参数档案将保留。\n\n' +
      '⚠️ 此操作不可恢复！\n' +
      '⚠️ 建议先备份数据库！\n\n' +
      '确定要继续吗？',
      '清除所有数据',
      {
        type: 'error',
        confirmButtonText: '确定清除所有数据',
        cancelButtonText: '取消',
        dangerouslyUseHTMLString: false,
        distinguishCancelAndClose: true,
        confirmButtonClass: 'el-button--danger'
      }
    )
    await ElMessageBox.confirm(
      '最后确认：\n\n您即将删除所有数据，此操作无法撤销！\n\n请再次确认是否继续？',
      '最后确认',
      {
        type: 'error',
        confirmButtonText: '我确定，清除所有数据',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger'
      }
    )
  } catch {
    return
  }

  cleanupAllLoading.value = true
  try {
    const result: CleanupResult = await cleanupAllData()
    if (result.status === 'success' || result.status === 'partial') {
      const total = result.total_deleted || 0
      const details = buildCleanupDetails(result)
      ElMessage.success({
        message: `清除完成！共删除 ${total} 条记录${details.length ? `（${details.join('，')}）` : ''}`,
        duration: 5000
      })
      await loadCleanupStats()
    } else {
      ElMessage.warning('清除完成，但可能有一些错误')
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '清除失败'))
  } finally {
    cleanupAllLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadSystemStatus(), loadMetrics(), loadIngestionRecords()])
  await loadCleanupStats()
})
</script>

<template>
  <div class="settings-page">
    <div class="settings-noise" />

    <header class="settings-header glass-panel">
      <div class="settings-brand-block">
        <div class="settings-brand-mark">
          <span class="settings-brand-mark__dot" />
        </div>
        <div class="settings-brand-text">
          <p class="settings-eyebrow">System Console</p>
          <h1>系统设置</h1>
          <p class="settings-subtitle">查看运行状态、接入流水、指标输出，并执行受控的数据维护操作。</p>
          <div class="settings-tags">
            <span class="settings-tag">管理员</span>
            <span class="settings-tag settings-tag--cyan">{{ healthyServiceCount }}/{{ serviceEntries.length }} 服务健康</span>
          </div>
        </div>
      </div>
      <div class="settings-header-actions">
        <el-button type="primary" :icon="Refresh" @click="loadSystemStatus">刷新状态</el-button>
        <el-button :icon="Refresh" @click="loadMetrics">刷新指标</el-button>
      </div>
    </header>

    <div class="settings-kpi-strip">
      <div class="settings-kpi settings-kpi--health">
        <span class="settings-kpi__label">服务健康</span>
        <div class="settings-kpi__value">
          <strong>{{ healthyServiceCount }}</strong>
          <span>/ {{ serviceEntries.length }}</span>
        </div>
        <span class="settings-kpi__sub">Health checks</span>
      </div>
      <div class="settings-kpi settings-kpi--data">
        <span class="settings-kpi__label">可维护数据</span>
        <div class="settings-kpi__value">
          <strong>{{ cleanupTotalCount.toLocaleString() }}</strong>
          <span>条</span>
        </div>
        <span class="settings-kpi__sub">Cleanup scope</span>
      </div>
      <div class="settings-kpi" :class="ingestionIssueCount > 0 ? 'settings-kpi--warn' : 'settings-kpi--safe'">
        <span class="settings-kpi__label">接入异常</span>
        <div class="settings-kpi__value">
          <strong>{{ ingestionIssueCount }}</strong>
          <span>条</span>
        </div>
        <span class="settings-kpi__sub">MQTT replay queue</span>
      </div>
      <div class="settings-kpi settings-kpi--metrics">
        <span class="settings-kpi__label">指标序列</span>
        <div class="settings-kpi__value">
          <strong>{{ metricsLineCount }}</strong>
          <span>项</span>
        </div>
        <span class="settings-kpi__sub">Prometheus output</span>
      </div>
    </div>

    <!-- 演示数据模式 -->
    <div class="admin-section glass-panel">
      <div class="section-label">演示数据模式</div>
      <div class="demo-mode-panel inner-panel">
        <div class="demo-mode-copy">
          <span class="demo-mode-title">使用演示数据</span>
          <span class="dim">
            开启后页面使用演示数据展示；关闭后页面不再使用演示数据。
          </span>
          <span class="demo-mode-status">{{ demoModeStatusText }}</span>
        </div>
        <el-switch
          v-model="demoModeEnabled"
          size="large"
          active-text="开启"
          inactive-text="关闭"
          @change="handleDemoModeChange"
        />
      </div>
    </div>

    <!-- 数据管理 -->
    <div class="admin-section glass-panel danger-panel">
      <div class="section-label">数据管理</div>
      <div class="data-grid">
        <!-- 清理操作 -->
        <div class="inner-panel">
          <div class="cleanup-select-row">
            <span class="dim">清理时间范围</span>
            <el-select v-model="cleanupHours" size="small" style="width: 130px">
              <el-option :value="1" label="1 小时前" />
              <el-option :value="6" label="6 小时前" />
              <el-option :value="12" label="12 小时前" />
              <el-option :value="24" label="24 小时前" />
            </el-select>
          </div>
          <div class="cleanup-actions">
            <el-button
              type="danger"
              size="small"
              :loading="cleanupLoading"
              :icon="Delete"
              @click="handleCleanupData"
            >
              清理 {{ cleanupHours }}h 前数据
            </el-button>
            <el-button
              type="danger"
              size="small"
              plain
              :loading="cleanupAllLoading"
              :icon="Delete"
              @click="handleCleanupAllData"
            >
              清除所有数据
            </el-button>
          </div>
        </div>

        <!-- 数据统计 -->
        <div class="inner-panel">
          <div v-if="cleanupStats" class="stat-table">
            <div
              v-for="row in cleanupStatRows"
              :key="row.key"
              class="stat-row"
            >
              <span class="dim">{{ row.label }}</span>
              <span class="stat-count">{{ formatCleanupTotal(cleanupStats, row.key) }} 条</span>
            </div>
          </div>
          <span v-else class="dim">加载中…</span>
        </div>
      </div>
    </div>

    <!-- 系统状态 -->
    <div class="admin-section glass-panel">
      <div class="section-label">
        系统状态
        <el-button text size="small" @click="loadSystemStatus">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
      <div v-if="systemStatus" class="inner-panel">
        <div class="status-strip">
          <div
            v-for="svc in serviceEntries"
            :key="svc.key"
            class="status-entry"
          >
            <span
              class="dot"
              :class="svc.getValue(systemStatus) === 'healthy' ? 'dot--ok' : 'dot--err'"
            />
            <span>{{ svc.label }}</span>
            <span class="dim">{{ svc.getValue(systemStatus) || 'unknown' }}</span>
          </div>
        </div>
        <div class="info-strip">
          <div class="info-entry">
            <span class="dim">版本</span>
            <span>{{ systemStatus.version || '-' }}</span>
          </div>
          <div class="info-entry">
            <span class="dim">服务器时间</span>
            <span>{{ systemStatus.timestamp ? new Date(systemStatus.timestamp).toLocaleString('zh-CN') : '-' }}</span>
          </div>
          <div class="info-entry">
            <span class="dim">MQTT 重复消息</span>
            <span>{{ systemStatus.runtime?.counters?.mqtt_duplicates_total ?? 0 }}</span>
          </div>
          <div class="info-entry">
            <span class="dim">MQTT 处理失败</span>
            <span>{{ systemStatus.runtime?.counters?.mqtt_processing_failed_total ?? 0 }}</span>
          </div>
        </div>
      </div>
      <span v-else class="dim">加载中…</span>
    </div>

    <!-- MQTT 接入记录 -->
    <div class="admin-section glass-panel">
      <div class="section-label">
        MQTT 接入记录
        <el-button text size="small" @click="loadIngestionRecords">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
      <el-table
        v-loading="ingestionLoading"
        :data="ingestionRecords"
        empty-text="暂无接入记录"
        size="small"
      >
        <el-table-column prop="device_id" label="设备" width="80" />
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="mqttStatusType(row.status)" size="small" disable-transitions>
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="retry_count" label="重试" width="70" />
        <el-table-column prop="replay_count" label="重放" width="70" />
        <el-table-column prop="error_reason" label="错误原因" min-width="160" />
        <el-table-column prop="received_at" label="接收时间" min-width="180" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              :disabled="!['failed', 'dead_letter'].includes(row.status)"
              @click="replayIngestionRecord(row.id)"
            >
              重放
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Prometheus Metrics -->
    <div class="admin-section glass-panel metrics-panel">
      <div class="section-label">
        Prometheus Metrics
        <el-button text size="small" @click="loadMetrics">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
      <pre class="metrics-pre">{{ metricsText || '暂无输出' }}</pre>
    </div>

    <!-- 关于系统 -->
    <div class="admin-section glass-panel">
      <div class="section-label">关于系统</div>
      <div class="about-strip">
        <span class="app-name">Park Energy Management System</span>
        <el-tag size="small" effect="plain">v2.2.0</el-tag>
        <div class="about-tags">
          <el-tag
            v-for="t in techStack"
            :key="t"
            size="small"
            effect="plain"
            type="info"
          >
            {{ t }}
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  min-height: 100%;
  height: auto;
  padding: 16px;
  overflow-x: hidden;
  box-sizing: border-box;
  color: #f5f7fa;
  background:
    radial-gradient(circle at top left, rgba(107, 184, 255, 0.08), transparent 28%),
    radial-gradient(circle at bottom right, rgba(52, 211, 153, 0.05), transparent 26%),
    #090e17;
}

.settings-noise {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(255,255,255,0.012), transparent 20%, transparent 80%, rgba(255,255,255,0.012));
  opacity: 0.3;
}

.glass-panel {
  position: relative;
  z-index: 1;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(18px) saturate(145%);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06), 0 10px 28px rgba(0,0,0,0.18);
  overflow: hidden;
}

.settings-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 108px;
  padding: 22px;
  box-sizing: border-box;
}

.settings-brand-block {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.settings-brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  margin-top: 2px;
  border-radius: 14px;
  flex-shrink: 0;
  background: rgba(96, 165, 250, 0.12);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
}

.settings-brand-mark__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #60a5fa;
  box-shadow: 0 0 12px rgba(96, 165, 250, 0.58);
}

.settings-brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.settings-eyebrow {
  margin: 0;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.46);
}

.settings-brand-text h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.02;
  letter-spacing: 0;
}

.settings-subtitle {
  margin: 0;
  max-width: 560px;
  font-size: 12px;
  line-height: 1.3;
  color: rgba(255,255,255,0.44);
}

.settings-tags,
.settings-header-actions,
.cleanup-actions,
.about-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.settings-tags {
  margin-top: 8px;
}

.settings-header-actions {
  justify-content: flex-end;
  flex-shrink: 0;
}

.settings-tag {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  color: rgba(255,255,255,0.62);
  background: rgba(255,255,255,0.045);
  border: 1px solid rgba(255,255,255,0.08);
}

.settings-tag--cyan {
  color: #67e8f9;
  border-color: rgba(103, 232, 249, 0.28);
  background: rgba(103, 232, 249, 0.08);
}

.settings-kpi-strip {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.settings-kpi {
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

.settings-kpi:hover {
  background: rgba(255, 255, 255, 0.06);
}

.settings-kpi--health { --kpi-accent: #60a5fa; }
.settings-kpi--data { --kpi-accent: #38bdf8; }
.settings-kpi--safe { --kpi-accent: #34d399; }
.settings-kpi--warn { --kpi-accent: #fb923c; }
.settings-kpi--metrics { --kpi-accent: #a78bfa; }

.settings-kpi__label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.46);
}

.settings-kpi__value {
  display: flex;
  align-items: baseline;
  gap: 5px;
  line-height: 1;
}

.settings-kpi__value strong {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0;
  color: #f0f6ff;
}

.settings-kpi__value span,
.settings-kpi__sub {
  font-size: 12px;
  color: rgba(255,255,255,0.42);
}

.demo-mode-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.demo-mode-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.demo-mode-title {
  font-size: 14px;
  font-weight: 700;
  color: #f0f6ff;
}

.demo-mode-status {
  font-size: 12px;
  color: #67e8f9;
}

.admin-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 20px;
}

.danger-panel {
  border: 1px solid rgba(248, 113, 113, 0.14);
}

.section-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.4);
}

.data-grid {
  display: grid;
  grid-template-columns: minmax(260px, 0.75fr) minmax(0, 1.25fr);
  gap: 12px;
  align-items: start;
}

.inner-panel {
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(255,255,255,0.035);
  border: 1px solid rgba(255,255,255,0.06);
}

.cleanup-select-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  font-size: 13px;
}

.stat-table {
  display: flex;
  flex-direction: column;
}

.stat-row,
.info-entry,
.status-entry {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.stat-row {
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-count,
.app-name {
  font-weight: 600;
  color: #f0f6ff;
}

.status-strip,
.info-strip,
.about-strip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.status-strip {
  gap: 22px;
  margin-bottom: 12px;
}

.info-strip {
  gap: 24px;
  padding-top: 12px;
  border-top: 1px solid rgba(255,255,255,0.06);
  font-size: 13px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot--ok {
  background: #34d399;
  box-shadow: 0 0 10px rgba(52, 211, 153, 0.5);
}

.dot--err {
  background: #f87171;
  box-shadow: 0 0 10px rgba(248, 113, 113, 0.5);
}

.dim {
  color: rgba(255,255,255,0.46);
}

.metrics-pre {
  margin: 0;
  max-height: 300px;
  padding: 14px 16px;
  overflow: auto;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(5, 10, 18, 0.58);
  color: rgba(226, 232, 240, 0.66);
  font-family: 'JetBrains Mono', 'Menlo', monospace;
  font-size: 11px;
  line-height: 1.6;
  white-space: pre;
}

.about-strip {
  gap: 10px;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(255,255,255,0.035);
  border: 1px solid rgba(255,255,255,0.06);
  font-size: 13px;
}

.about-tags {
  margin-left: auto;
}

:deep(.el-button) {
  min-height: 34px;
  border-radius: 20px;
  font-weight: 500;
}

:deep(.el-button--primary) {
  border-color: rgba(96, 165, 250, 0.34);
  background: linear-gradient(135deg, rgba(96, 165, 250, 0.9), rgba(103, 232, 249, 0.72));
  color: #06111f;
}

:deep(.el-button--danger) {
  border-color: rgba(248, 113, 113, 0.5);
  background: linear-gradient(135deg, rgba(248, 113, 113, 0.92), rgba(251, 146, 60, 0.78));
  color: #fff7ed;
}

:deep(.el-button--danger.is-plain) {
  border-color: rgba(248, 113, 113, 0.32);
  background: rgba(248, 113, 113, 0.1);
  color: #fca5a5;
}

:deep(.el-button:not(.el-button--primary):not(.el-button--danger)) {
  border-color: rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.045);
  color: rgba(255,255,255,0.72);
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  min-height: 34px;
  border-radius: 8px;
  background: rgba(255,255,255,0.05);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
}

:deep(.el-input__inner),
:deep(.el-select__selected-item),
:deep(.el-select__placeholder) {
  color: rgba(255,255,255,0.82);
}

:deep(.el-select__placeholder.is-transparent),
:deep(.el-input__inner::placeholder) {
  color: rgba(255,255,255,0.3);
}

:deep(.el-tag) {
  border-radius: 7px;
  border-color: rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.06);
  color: rgba(226,232,240,0.76);
}

:deep(.el-tag.el-tag--primary) {
  border-color: rgba(96, 165, 250, 0.26);
  background: rgba(96, 165, 250, 0.1);
  color: #93c5fd;
}

:deep(.el-tag.el-tag--info) {
  border-color: rgba(148, 163, 184, 0.18);
  background: rgba(148, 163, 184, 0.08);
  color: rgba(226,232,240,0.64);
}

:deep(.el-tag.el-tag--warning) {
  border-color: rgba(251, 146, 60, 0.3);
  background: rgba(251, 146, 60, 0.1);
  color: #fdba74;
}

:deep(.el-tag.el-tag--danger) {
  border-color: rgba(248, 113, 113, 0.34);
  background: rgba(248, 113, 113, 0.11);
  color: #fca5a5;
}

:deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255,255,255,0.035);
  --el-table-row-hover-bg-color: rgba(255,255,255,0.055);
  --el-table-border-color: rgba(255,255,255,0.06);
  --el-table-text-color: rgba(255,255,255,0.78);
  --el-table-header-text-color: rgba(255,255,255,0.46);
  --el-bg-color: transparent;
  overflow: hidden;
  border-radius: 12px;
  background: transparent;
  color: rgba(255,255,255,0.78);
}

:deep(.el-table__inner-wrapper),
:deep(.el-table__body-wrapper),
:deep(.el-table__header-wrapper),
:deep(.el-scrollbar),
:deep(.el-scrollbar__view) {
  background: transparent;
}

:deep(.el-table__inner-wrapper::before),
:deep(.el-table::before) {
  display: none;
}

:deep(.el-table th.el-table__cell),
:deep(.el-table tr),
:deep(.el-table td.el-table__cell) {
  background: transparent !important;
  border-bottom-color: rgba(255,255,255,0.05);
  color: rgba(255,255,255,0.78);
}

:deep(.el-table__header-wrapper th) {
  background: rgba(255,255,255,0.035) !important;
  color: rgba(255,255,255,0.42);
  font-size: 11px;
}

:deep(.el-table__body tr:hover > td.el-table__cell) {
  background: rgba(255,255,255,0.055) !important;
}

:deep(.el-table__empty-block) {
  background: transparent;
}

@media (max-width: 1100px) {
  .settings-kpi-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .data-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .settings-page {
    padding: 12px;
    gap: 10px;
  }

  .settings-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 14px 16px;
  }

  .settings-brand-text h1 {
    font-size: 22px;
  }

  .settings-header-actions {
    justify-content: flex-start;
    width: 100%;
  }

  .settings-kpi-strip {
    grid-template-columns: 1fr;
  }
}
</style>
