<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataAnalysis, DataBoard, Monitor, InfoFilled, Refresh, CircleCheck, Connection, Delete } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { getDevices, type Device } from '@/api/device'
import { cleanupData, getCleanupStats, cleanupAllData, type CleanupResult } from '@/api/dataCleanup'

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

interface DeviceStats {
  total_count?: number
  days?: number
  earliest_time?: string
  latest_time?: string
  [key: string]: unknown
}

interface CleanupStats {
  energy_data?: { total?: number }
  alarm_data?: { total?: number }
  [key: string]: unknown
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) return error.message
  return fallback
}

// --- 状态 ---
const activeTab = ref('data')
const loading = ref(false)
const deviceList = ref<Device[]>([])

// 数据生成
const generateForm = reactive({
  device_id: undefined as number | undefined,
  days: 60,
  interval_minutes: 60,
  data_type: 'load',
  clear_existing: false
})

// 系统状态
const systemStatus = ref<SystemStatus | null>(null)
const metricsText = ref('')
const ingestionRecords = ref<IngestionRecord[]>([])
const ingestionLoading = ref(false)

// 数据统计
const dataStats = ref<DeviceStats | null>(null)
const selectedDeviceForStats = ref<number | undefined>(undefined)

// 数据清理
const cleanupHours = ref(1)
const cleanupLoading = ref(false)
const cleanupAllLoading = ref(false)
const cleanupStats = ref<CleanupStats | null>(null)

// --- API 调用 ---
const generateDeviceData = async () => {
  if (generateForm.device_id == null) {
    ElMessage.warning('请选择设备')
    return
  }
  
  loading.value = true
  try {
    const res = await request.post<{
      days: number
      interval_minutes: number
      data_type: string
      clear_existing: boolean
    }, MessageResponse>(`/data-generator/generate/device/${generateForm.device_id}`, {
      days: generateForm.days,
      interval_minutes: generateForm.interval_minutes,
      data_type: generateForm.data_type,
      clear_existing: generateForm.clear_existing
    })
    ElMessage.success(res.message || '数据生成成功')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '生成失败'))
  } finally {
    loading.value = false
  }
}

const generateAllData = async () => {
  try {
    await ElMessageBox.confirm('确定为所有设备生成模拟数据？', '提示', {
      type: 'warning'
    })
  } catch {
    return
  }
  
  loading.value = true
  try {
    const res = await request.post<{
      days: number
      interval_minutes: number
      clear_existing: boolean
    }, MessageResponse>('/data-generator/generate/all', {
      days: generateForm.days,
      interval_minutes: generateForm.interval_minutes,
      clear_existing: generateForm.clear_existing
    })
    ElMessage.success(res.message || '数据生成成功')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '生成失败'))
  } finally {
    loading.value = false
  }
}

const clearDeviceData = async () => {
  if (selectedDeviceForStats.value == null) {
    ElMessage.warning('请先选择设备')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定清除该设备的所有数据？此操作不可恢复！', '警告', {
      type: 'error'
    })
  } catch {
    return
  }
  
  loading.value = true
  try {
    await request.delete<never, MessageResponse>(`/data-generator/clear/${selectedDeviceForStats.value}`)
    ElMessage.success('数据已清除')
    loadDeviceStats()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '清除失败'))
  } finally {
    loading.value = false
  }
}

const loadDeviceStats = async () => {
  if (!selectedDeviceForStats.value) {
    dataStats.value = null
    return
  }
  
  try {
    const res = await request.get<never, DeviceStats>(`/data-generator/stats/${selectedDeviceForStats.value}`)
    dataStats.value = res
  } catch {
    // 由 axios 拦截器统一提示
  }
}

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
    const res = await request.get<never, string>('/metrics', {
      responseType: 'text'
    })
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

const loadDevices = async () => {
  try {
    deviceList.value = await getDevices()
  } catch {
    // 设备列表加载失败
  }
}

// 清理一小时之前的数据
const handleCleanupData = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要清理 ${cleanupHours.value} 小时之前的所有数据吗？\n\n此操作将永久删除以下数据：\n- 时序数据（EnergyData）\n- 已解决的报警记录\n- 碳排放记录\n\n⚠️ 此操作不可恢复！`,
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
      ElMessage.success({
        message: `清理完成！共删除 ${total} 条记录`,
        duration: 5000
      })
      
      // 显示详细结果
      const details = []
      if (result.energy_data > 0) details.push(`时序数据: ${result.energy_data} 条`)
      if (result.alarm_data > 0) details.push(`报警记录: ${result.alarm_data} 条`)
      if (result.carbon_emission > 0) details.push(`碳排放记录: ${result.carbon_emission} 条`)
      
      // 重新加载统计信息
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

// 加载清理统计信息
const loadCleanupStats = async () => {
  try {
    const res = await getCleanupStats()
    cleanupStats.value = res
  } catch {
    // 清理统计加载失败
  }
}

// 清除所有数据
const handleCleanupAllData = async () => {
  try {
    // 双重确认
    await ElMessageBox.confirm(
      '⚠️ 危险操作警告！\n\n' +
      '此操作将永久删除以下所有数据：\n' +
      '• 所有时序数据（EnergyData）\n' +
      '• 所有已解决的报警记录\n' +
      '• 所有碳排放记录\n\n' +
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
    
    // 第二次确认
    await ElMessageBox.confirm(
      '最后确认：\n\n' +
      '您即将删除所有数据，此操作无法撤销！\n\n' +
      '请再次确认是否继续？',
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
      ElMessage.success({
        message: `清除完成！共删除 ${total} 条记录`,
        duration: 5000
      })
      
      // 显示详细结果
      const details = []
      if (result.energy_data > 0) details.push(`时序数据: ${result.energy_data} 条`)
      if (result.alarm_data > 0) details.push(`报警记录: ${result.alarm_data} 条`)
      if (result.carbon_emission > 0) details.push(`碳排放记录: ${result.carbon_emission} 条`)
      
      // 重新加载统计信息
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

// --- 生命周期 ---
onMounted(async () => {
  await loadDevices()
  await Promise.all([loadSystemStatus(), loadMetrics(), loadIngestionRecords()])
  await loadCleanupStats()
})
</script>

<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>

    <el-tabs
      v-model="activeTab"
      class="settings-tabs"
    >
      <!-- 数据管理 -->
      <el-tab-pane
        label="数据管理"
        name="data"
      >
        <div class="tab-content">
          <div class="section-row">
            <!-- 数据生成 -->
            <div class="section-card">
              <div class="card-header">
                <el-icon><DataAnalysis /></el-icon>
                <span>生成模拟数据</span>
              </div>
              <div class="card-body">
                <p class="section-desc">
                  为设备生成模拟的历史数据，用于系统测试和模型训练。
                </p>
                
                <el-form label-position="top">
                  <el-form-item label="选择设备">
                    <el-select
                      v-model="generateForm.device_id"
                      placeholder="选择设备"
                      style="width: 100%"
                      teleported
                      popper-class="app-select-popper"
                    >
                      <el-option
                        v-for="d in deviceList"
                        :key="d.id"
                        :label="d.name"
                        :value="d.id"
                      />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="生成天数">
                    <el-input-number
                      v-model="generateForm.days"
                      :min="1"
                      :max="365"
                      style="width: 100%"
                    />
                  </el-form-item>
                  
                  <el-form-item label="数据间隔(分钟)">
                    <el-select
                      v-model="generateForm.interval_minutes"
                      style="width: 100%"
                      teleported
                      popper-class="app-select-popper"
                    >
                      <el-option
                        :value="15"
                        label="15分钟"
                      />
                      <el-option
                        :value="30"
                        label="30分钟"
                      />
                      <el-option
                        :value="60"
                        label="1小时"
                      />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="数据类型">
                    <el-select
                      v-model="generateForm.data_type"
                      style="width: 100%"
                      teleported
                      popper-class="app-select-popper"
                    >
                      <el-option
                        value="load"
                        label="负荷数据"
                      />
                      <el-option
                        value="solar"
                        label="光伏数据"
                      />
                      <el-option
                        value="wind"
                        label="风电数据"
                      />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item>
                    <el-checkbox v-model="generateForm.clear_existing">
                      清除现有数据
                    </el-checkbox>
                  </el-form-item>
                  
                  <div class="button-group">
                    <el-button
                      type="primary"
                      :loading="loading"
                      @click="generateDeviceData"
                    >
                      生成数据
                    </el-button>
                    <el-button
                      type="warning"
                      :loading="loading"
                      @click="generateAllData"
                    >
                      为所有设备生成
                    </el-button>
                  </div>
                </el-form>
              </div>
            </div>

            <!-- 数据统计 -->
            <div class="section-card">
              <div class="card-header">
                <el-icon><DataBoard /></el-icon>
                <span>数据统计</span>
              </div>
              <div class="card-body">
                <p class="section-desc">
                  查看设备的数据量和时间范围。
                </p>
                
                <el-form label-position="top">
                  <el-form-item label="选择设备">
                    <el-select
                      v-model="selectedDeviceForStats"
                      placeholder="选择设备"
                      style="width: 100%"
                      teleported
                      popper-class="app-select-popper"
                      @change="loadDeviceStats"
                    >
                      <el-option
                        v-for="d in deviceList"
                        :key="d.id"
                        :label="d.name"
                        :value="d.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-form>
                
                <div
                  v-if="dataStats"
                  class="stats-display"
                >
                  <div class="stat-row">
                    <label>数据总量</label>
                    <span class="value">{{ dataStats.total_count?.toLocaleString() }} 条</span>
                  </div>
                  <div class="stat-row">
                    <label>时间跨度</label>
                    <span class="value">{{ dataStats.days || 0 }} 天</span>
                  </div>
                  <div class="stat-row">
                    <label>最早数据</label>
                    <span class="value">{{ dataStats.earliest_time ? new Date(dataStats.earliest_time).toLocaleString('zh-CN') : '-' }}</span>
                  </div>
                  <div class="stat-row">
                    <label>最新数据</label>
                    <span class="value">{{ dataStats.latest_time ? new Date(dataStats.latest_time).toLocaleString('zh-CN') : '-' }}</span>
                  </div>
                </div>
                
                <el-empty
                  v-else-if="!selectedDeviceForStats"
                  description="请选择设备"
                  :image-size="60"
                />
                
                <el-button
                  type="danger"
                  :loading="loading"
                  :disabled="!selectedDeviceForStats"
                  style="margin-top: 15px"
                  @click="clearDeviceData"
                >
                  清除数据
                </el-button>
              </div>
            </div>

            <!-- 数据清理 -->
            <div class="section-card">
              <div class="card-header">
                <el-icon><Delete /></el-icon>
                <span>数据清理</span>
              </div>
              <div class="card-body">
                <p class="section-desc">
                  清理指定时间之前的历史数据，释放存储空间。
                </p>
                
                <el-form label-position="top">
                  <el-form-item label="清理时间范围">
                    <el-select
                      v-model="cleanupHours"
                      style="width: 100%"
                    >
                      <el-option
                        :value="1"
                        label="1小时前"
                      />
                      <el-option
                        :value="6"
                        label="6小时前"
                      />
                      <el-option
                        :value="12"
                        label="12小时前"
                      />
                      <el-option
                        :value="24"
                        label="24小时前"
                      />
                    </el-select>
                  </el-form-item>
                </el-form>
                
                <div
                  v-if="cleanupStats"
                  class="cleanup-info"
                >
                  <div class="info-item">
                    <span class="label">时序数据总量：</span>
                    <span class="value">{{ cleanupStats.energy_data?.total?.toLocaleString() || 0 }} 条</span>
                  </div>
                  <div class="info-item">
                    <span class="label">报警记录总量：</span>
                    <span class="value">{{ cleanupStats.alarm_data?.total?.toLocaleString() || 0 }} 条</span>
                  </div>
                </div>
                
                <el-alert
                  type="warning"
                  :closable="false"
                  style="margin: 15px 0"
                >
                  <template #title>
                    <div style="font-size: 13px;">
                      <strong>⚠️ 警告：</strong>此操作将永久删除数据，无法恢复！<br>
                      建议在清理前先备份数据库。
                    </div>
                  </template>
                </el-alert>
                
                <el-button
                  type="danger"
                  :loading="cleanupLoading"
                  style="width: 100%"
                  @click="handleCleanupData"
                >
                  <el-icon><Delete /></el-icon>
                  清理 {{ cleanupHours }} 小时前的数据
                </el-button>
                
                <el-divider>或</el-divider>
                
                <el-alert
                  type="error"
                  :closable="false"
                  style="margin: 15px 0"
                >
                  <template #title>
                    <div style="font-size: 13px;">
                      <strong>🚨 危险操作：</strong>清除所有数据将删除数据库中的所有历史记录！<br>
                      此操作不可恢复，请务必先备份数据库！
                    </div>
                  </template>
                </el-alert>
                
                <el-button
                  type="danger"
                  :loading="cleanupAllLoading"
                  style="width: 100%"
                  plain
                  @click="handleCleanupAllData"
                >
                  <el-icon><Delete /></el-icon>
                  清除所有数据
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 系统状态 -->
      <el-tab-pane
        label="系统状态"
        name="status"
      >
        <div class="tab-content">
          <div class="section-card full-width">
            <div class="card-header">
              <el-icon><Monitor /></el-icon>
              <span>系统健康状态</span>
              <el-button
                text
                style="margin-left: auto"
                @click="loadSystemStatus"
              >
                <el-icon><Refresh /></el-icon>刷新
              </el-button>
            </div>
            <div class="card-body">
              <div
                v-if="systemStatus"
                class="status-grid"
              >
                <div class="status-item">
                  <div
                    class="status-icon"
                    :class="{ success: systemStatus.status === 'healthy' }"
                  >
                    <el-icon><CircleCheck /></el-icon>
                  </div>
                  <div class="status-info">
                    <div class="status-label">
                      系统状态
                    </div>
                    <div class="status-value">
                      {{ systemStatus.status === 'healthy' ? '运行正常' : '异常' }}
                    </div>
                  </div>
                </div>
                
                <div class="status-item">
                  <div
                    class="status-icon"
                    :class="{ success: systemStatus.services?.database === 'healthy' }"
                  >
                    <el-icon><Connection /></el-icon>
                  </div>
                  <div class="status-info">
                    <div class="status-label">
                      数据库
                    </div>
                    <div class="status-value">
                      {{ systemStatus.services?.database || 'unknown' }}
                    </div>
                  </div>
                </div>
                
                <div class="status-item">
                  <div
                    class="status-icon"
                    :class="{ success: systemStatus.services?.redis === 'healthy' }"
                  >
                    <el-icon><Connection /></el-icon>
                  </div>
                  <div class="status-info">
                    <div class="status-label">
                      Redis
                    </div>
                    <div class="status-value">
                      {{ systemStatus.services?.redis || 'unknown' }}
                    </div>
                  </div>
                </div>
                
                <div class="status-item">
                  <div
                    class="status-icon"
                    :class="{ success: systemStatus.services?.mqtt === 'healthy' }"
                  >
                    <el-icon><Connection /></el-icon>
                  </div>
                  <div class="status-info">
                    <div class="status-label">
                      MQTT
                    </div>
                    <div class="status-value">
                      {{ systemStatus.services?.mqtt || 'unknown' }}
                    </div>
                  </div>
                </div>

                <div class="status-item">
                  <div
                    class="status-icon"
                    :class="{ success: systemStatus.services?.scheduler === 'healthy' }"
                  >
                    <el-icon><Connection /></el-icon>
                  </div>
                  <div class="status-info">
                    <div class="status-label">
                      调度器
                    </div>
                    <div class="status-value">
                      {{ systemStatus.services?.scheduler || 'unknown' }}
                    </div>
                  </div>
                </div>
              </div>
              
              <div
                v-if="systemStatus"
                class="system-info"
              >
                <div class="info-row">
                  <label>服务版本</label>
                  <span>{{ systemStatus.version || '-' }}</span>
                </div>
                <div class="info-row">
                  <label>服务器时间</label>
                  <span>{{ systemStatus.timestamp ? new Date(systemStatus.timestamp).toLocaleString('zh-CN') : '-' }}</span>
                </div>
                <div class="info-row">
                  <label>MQTT 重复消息</label>
                  <span>{{ systemStatus.runtime?.counters?.mqtt_duplicates_total || 0 }}</span>
                </div>
                <div class="info-row">
                  <label>MQTT 处理失败</label>
                  <span>{{ systemStatus.runtime?.counters?.mqtt_processing_failed_total || 0 }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="section-row">
            <div class="section-card">
              <div class="card-header">
                <el-icon><Monitor /></el-icon>
                <span>Prometheus Metrics</span>
                <el-button
                  text
                  style="margin-left: auto"
                  @click="loadMetrics"
                >
                  <el-icon><Refresh /></el-icon>刷新
                </el-button>
              </div>
              <div class="card-body">
                <pre class="metrics-preview">{{ metricsText || '暂无 metrics 输出' }}</pre>
              </div>
            </div>

            <div class="section-card">
              <div class="card-header">
                <el-icon><Connection /></el-icon>
                <span>MQTT 接入记录</span>
                <el-button
                  text
                  style="margin-left: auto"
                  @click="loadIngestionRecords"
                >
                  <el-icon><Refresh /></el-icon>刷新
                </el-button>
              </div>
              <div class="card-body">
                <el-table
                  v-loading="ingestionLoading"
                  :data="ingestionRecords"
                  size="small"
                >
                  <el-table-column
                    prop="device_id"
                    label="设备"
                    width="80"
                  />
                  <el-table-column
                    prop="status"
                    label="状态"
                    width="110"
                  />
                  <el-table-column
                    prop="retry_count"
                    label="重试"
                    width="70"
                  />
                  <el-table-column
                    prop="replay_count"
                    label="重放"
                    width="70"
                  />
                  <el-table-column
                    prop="error_reason"
                    label="错误原因"
                    min-width="160"
                  />
                  <el-table-column
                    prop="received_at"
                    label="接收时间"
                    min-width="180"
                  />
                  <el-table-column
                    label="操作"
                    width="100"
                  >
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
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 关于系统 -->
      <el-tab-pane
        label="关于系统"
        name="about"
      >
        <div class="tab-content">
          <div class="section-card full-width">
            <div class="card-header">
              <el-icon><InfoFilled /></el-icon>
              <span>关于 MINE EMS</span>
            </div>
            <div class="card-body about-content">
              <div class="logo-section">
                <div class="logo">
                  ⚡
                </div>
                <h3>MINE Energy Management System</h3>
                <p class="version">
                  Version 2.2.0
                </p>
              </div>
              
              <div class="feature-list">
                <h4>系统功能</h4>
                <ul>
                  <li>🏠 驾驶舱首页 - 实时监控与数据概览</li>
                  <li>📊 设备台账 - 设备全生命周期管理</li>
                  <li>📍 位置管理 - 设备物理位置层级管理</li>
                  <li>📁 设备分组 - 灵活的设备分组策略</li>
                  <li>⚡ 多能源管理 - 电/水/气/热多能源统计</li>
                  <li>📈 负荷预测 - 基于LSTM的智能预测</li>
                  <li>🔧 设备维护 - 维护计划与记录管理</li>
                  <li>🩺 故障诊断 - 实时故障检测与告警</li>
                  <li>📄 报表导出 - 灵活的数据导出功能</li>
                </ul>
              </div>
              
              <div class="tech-stack">
                <h4>技术栈</h4>
                <div class="tech-tags">
                  <el-tag>Vue 3</el-tag>
                  <el-tag>TypeScript</el-tag>
                  <el-tag>Element Plus</el-tag>
                  <el-tag>ECharts</el-tag>
                  <el-tag>FastAPI</el-tag>
                  <el-tag>TimescaleDB</el-tag>
                  <el-tag>Redis</el-tag>
                  <el-tag>MQTT</el-tag>
                  <el-tag>TensorFlow</el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.settings-page {
  padding: 10px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: var(--text-primary);
}

.settings-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
}

.tab-content {
  padding: 10px 0;
}

.section-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.section-card {
  flex: 1;
  min-width: 400px;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.section-card.full-width {
  min-width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 20px;
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
  color: var(--text-primary);
}

.card-body {
  padding: 20px;
}

.section-desc {
  color: var(--text-secondary);
  margin-bottom: 20px;
  font-size: 14px;
}

.button-group {
  display: flex;
  gap: 10px;
}

.stats-display {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  padding: 15px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row label {
  color: var(--text-secondary);
}

.stat-row .value {
  font-weight: 500;
  color: var(--text-primary);
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
}

.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.status-icon.success {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.status-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.status-value {
  font-weight: 600;
  color: var(--text-primary);
}

.system-info {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  padding: 15px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
}

.info-row label {
  color: var(--text-secondary);
}

.info-row span {
  color: var(--text-primary);
}

.about-content {
  text-align: center;
}

.logo-section {
  margin-bottom: 30px;
}

.logo {
  font-size: 64px;
  margin-bottom: 10px;
}

.logo-section h3 {
  margin: 0 0 10px;
  color: var(--text-primary);
}

.version {
  color: var(--text-secondary);
}

.feature-list {
  text-align: left;
  max-width: 500px;
  margin: 0 auto 30px;
}

.feature-list h4 {
  color: var(--text-primary);
  margin-bottom: 15px;
}

.feature-list ul {
  list-style: none;
  padding: 0;
}

.feature-list li {
  padding: 8px 0;
  color: var(--text-secondary);
}

.tech-stack h4 {
  color: var(--text-primary);
  margin-bottom: 15px;
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.cleanup-info {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  color: var(--text-secondary);
  font-size: 13px;
}

.info-item .value {
  color: var(--text-primary);
  font-weight: 500;
}
</style>
