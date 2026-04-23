<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { cleanupData, getCleanupStats, cleanupAllData, type CleanupResult, type CleanupStats } from '@/api/dataCleanup'

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

const cleanupHours = ref(1)
const cleanupLoading = ref(false)
const cleanupAllLoading = ref(false)
const cleanupStats = ref<CleanupStats | null>(null)

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
    metricsText.value = res
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
    <!-- 页头 -->
    <div class="page-title-row">
      <h2>系统设置</h2>
      <el-tag size="small" type="warning" effect="plain">管理员</el-tag>
    </div>

    <!-- 数据管理 -->
    <div class="admin-section">
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
    <div class="admin-section">
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
    <div class="admin-section">
      <div class="section-label">
        MQTT 接入记录
        <el-button text size="small" @click="loadIngestionRecords">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
      <el-table
        v-loading="ingestionLoading"
        :data="ingestionRecords"
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
    <div class="admin-section">
      <div class="section-label">
        Prometheus Metrics
        <el-button text size="small" @click="loadMetrics">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
      <pre class="metrics-pre">{{ metricsText || '暂无输出' }}</pre>
    </div>

    <!-- 关于系统 -->
    <div class="admin-section">
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
/* ── 基础（14" Mac：内容区约 1050–1200px） ── */
.settings-page {
  padding: 20px 24px;
  max-width: 1200px;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title-row h2 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.admin-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.data-grid {
  display: grid;
  grid-template-columns: minmax(240px, 320px) 1fr;
  gap: 14px;
  align-items: start;
}

/* 窄屏单列（≤860px） */
@media (max-width: 860px) {
  .settings-page {
    padding: 14px 16px;
    gap: 18px;
  }
  .data-grid {
    grid-template-columns: 1fr;
  }
}

/* ── 27" 显示器（内容区 ≥1600px，含侧边栏后约 ≥1400px） ── */
@media (min-width: 1600px) {
  .settings-page {
    max-width: 1680px;
    padding: 28px 40px;
    gap: 32px;
  }
  .page-title-row h2 {
    font-size: 22px;
  }
  .data-grid {
    grid-template-columns: minmax(280px, 360px) 1fr;
    gap: 20px;
  }
  .admin-section {
    gap: 14px;
  }
  .inner-panel {
    padding: 18px 20px;
  }
  .stat-row {
    padding: 9px 0;
    font-size: 14px;
  }
  .status-strip {
    gap: 32px;
  }
  .info-strip {
    gap: 32px;
    padding-top: 14px;
  }
  .metrics-pre {
    max-height: 400px;
    font-size: 12px;
  }
}

.inner-panel {
  background: var(--bg-panel);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px 16px;
}

.cleanup-select-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  font-size: 13px;
}

.cleanup-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.stat-table {
  display: flex;
  flex-direction: column;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 13px;
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-count {
  font-weight: 500;
  color: var(--text-primary);
}

.status-strip {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 12px;
}

.status-entry {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot--ok {
  background: var(--success-color);
}

.dot--err {
  background: var(--danger-color);
}

.info-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-items: center;
  font-size: 13px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
}

.info-entry {
  display: flex;
  gap: 6px;
}

.dim {
  color: var(--text-secondary);
}

.metrics-pre {
  margin: 0;
  padding: 12px 14px;
  font-family: 'JetBrains Mono', 'Menlo', monospace;
  font-size: 11px;
  line-height: 1.6;
  color: var(--text-secondary);
  background: var(--bg-panel);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  max-height: 260px;
  overflow-y: auto;
  overflow-x: auto;
  white-space: pre;
}

.about-strip {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 13px;
  padding: 12px 16px;
  background: var(--bg-panel);
  border: 1px solid var(--border-color);
  border-radius: 10px;
}

.app-name {
  font-weight: 600;
  color: var(--text-primary);
}

.about-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-left: auto;
}

:deep(.el-table) {
  background: var(--bg-panel);
  color: var(--text-primary);
}

:deep(.el-table th.el-table__cell),
:deep(.el-table tr),
:deep(.el-table td.el-table__cell) {
  background: transparent;
  border-bottom-color: var(--border-color);
  color: var(--text-primary);
}

:deep(.el-table__empty-block) {
  background: var(--bg-panel);
}

:deep(.el-table__header-wrapper th) {
  color: var(--text-secondary);
}
</style>
