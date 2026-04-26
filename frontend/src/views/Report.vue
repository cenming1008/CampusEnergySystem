<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { DataAnalysis, Document, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { getDevices, type Device } from '@/api/device'
import { buildReportDownloadName, downloadReport, type ReportType } from '@/api/report'
import { useAuthStore } from '@/stores/useAuthStore'
import { usePermissions } from '@/shared/composables/usePermissions'

const downloading = ref(false)
const deviceList = ref<Device[]>([])
const authStore = useAuthStore()
const { hasScopedAccess } = usePermissions()

const filters = ref<{
  report_type: ReportType
  device_id?: number
  energy_type?: string
  resolved?: boolean
  start_time?: string
  end_time?: string
  limit: number
}>({
  report_type: 'energy_detail',
  limit: 1000,
})

const reportTypeOptions: Array<{ label: string; value: ReportType; description: string }> = [
  { label: '能耗明细', value: 'energy_detail', description: '导出设备逐条能耗与遥测记录' },
  { label: '报警历史', value: 'alarm_history', description: '导出报警产生、恢复与处理记录' },
  { label: '碳排放', value: 'carbon_emission', description: '导出碳排放与能耗记录' },
  { label: '多能源汇总', value: 'multi_energy_summary', description: '导出分能源周期消耗、瞬时统计与展示级碳排估算' },
]

const energyTypeOptions = [
  { label: '电力', value: 'electricity' },
  { label: '水', value: 'water' },
  { label: '燃气', value: 'gas' },
  { label: '热力', value: 'heat' },
  { label: '冷量', value: 'cooling' },
  { label: '蒸汽', value: 'steam' },
]

const exportHint = computed(() => {
  if (!authStore.locationScope) {
    return '报表会按当前账号权限范围导出，可进一步按设备、能源类型和时间窗筛选。'
  }
  return `当前账号位置范围为 ${authStore.locationScope}，导出结果会自动限制在该范围内。`
})

const selectedReportMeta = computed(() => (
  reportTypeOptions.find((item) => item.value === filters.value.report_type) ?? reportTypeOptions[0]
))

const selectedDeviceName = computed(() => {
  if (!filters.value.device_id) return '全部设备'
  return deviceList.value.find((device) => device.id === filters.value.device_id)?.name || `设备 ${filters.value.device_id}`
})

const selectedEnergyName = computed(() => {
  if (filters.value.report_type === 'alarm_history') return '不适用'
  if (!filters.value.energy_type) return '全部能源'
  return energyTypeOptions.find((item) => item.value === filters.value.energy_type)?.label || filters.value.energy_type
})

const selectedStatusName = computed(() => {
  if (filters.value.report_type !== 'alarm_history') return '不适用'
  if (filters.value.resolved === true) return '仅已恢复'
  if (filters.value.resolved === false) return '仅未恢复'
  return '全部状态'
})

const exportScopeRows = computed(() => [
  { label: '报表类型', value: selectedReportMeta.value.label },
  { label: '设备范围', value: selectedDeviceName.value },
  { label: '能源类型', value: selectedEnergyName.value },
  { label: '报警状态', value: selectedStatusName.value },
  { label: '开始时间', value: filters.value.start_time || '不限' },
  { label: '结束时间', value: filters.value.end_time || '不限' },
  { label: '导出上限', value: `${filters.value.limit.toLocaleString()} 条` },
])

function normalizeDateRange() {
  if (!filters.value.start_time || !filters.value.end_time) {
    return
  }
  if (filters.value.start_time > filters.value.end_time) {
    const start = filters.value.start_time
    filters.value.start_time = filters.value.end_time
    filters.value.end_time = start
  }
}

async function loadDevices() {
  deviceList.value = await getDevices()
}

async function handleDownload() {
  normalizeDateRange()
  downloading.value = true
  try {
    const blob = await downloadReport(filters.value)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute(
      'download',
      buildReportDownloadName(filters.value)
    )
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('报表下载成功')
  } catch {
    ElMessage.error('报表下载失败，请稍后重试')
  } finally {
    downloading.value = false
  }
}

onMounted(() => {
  loadDevices().catch(() => {
    ElMessage.warning('设备列表加载失败，仍可导出全量权限范围数据')
  })
})
</script>

<template>
  <div class="report-page">
    <div class="report-noise" />

    <header class="report-header glass-panel">
      <div class="report-brand-block">
        <div class="report-brand-mark">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="report-brand-text">
          <p class="report-eyebrow">Report Center</p>
          <h1>数据报表</h1>
          <p class="report-subtitle">{{ selectedReportMeta.description }}</p>
          <div class="report-tags">
            <span class="report-tag">CSV 导出</span>
            <span
              v-if="hasScopedAccess"
              class="report-tag report-tag--warn"
            >
              权限范围过滤中
            </span>
          </div>
        </div>
      </div>
      <div class="report-header-actions">
        <el-button
          type="primary"
          :icon="Download"
          :loading="downloading"
          @click="handleDownload"
        >
          {{ downloading ? '生成中' : '导出报表' }}
        </el-button>
      </div>
    </header>

    <section class="report-workspace">
      <article class="report-panel report-panel--form glass-panel">
        <div class="panel-title-row">
          <div>
            <p class="section-label">导出参数</p>
            <h2>{{ selectedReportMeta.label }}</h2>
          </div>
          <el-icon class="panel-title-icon"><Document /></el-icon>
        </div>

        <el-form
          label-position="top"
          class="report-form"
        >
          <el-form-item label="报表类型">
            <el-radio-group
              v-model="filters.report_type"
              class="report-type-group"
            >
              <el-radio-button
                v-for="option in reportTypeOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="设备">
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
          </el-form-item>

          <el-form-item
            v-if="filters.report_type !== 'alarm_history'"
            label="能源类型"
          >
            <el-select
              v-model="filters.energy_type"
              clearable
              placeholder="全部能源类型"
              teleported
              popper-class="app-select-popper"
            >
              <el-option
                v-for="option in energyTypeOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item
            v-if="filters.report_type === 'alarm_history'"
            label="报警状态"
          >
            <el-select
              v-model="filters.resolved"
              clearable
              placeholder="全部状态"
              teleported
              popper-class="app-select-popper"
            >
              <el-option
                label="仅未恢复"
                :value="false"
              />
              <el-option
                label="仅已恢复"
                :value="true"
              />
            </el-select>
          </el-form-item>

          <div class="date-row">
            <el-form-item label="开始日期">
              <el-date-picker
                v-model="filters.start_time"
                type="datetime"
                value-format="YYYY-MM-DDTHH:mm:ss"
                placeholder="选择开始时间"
              />
            </el-form-item>
            <el-form-item label="结束日期">
              <el-date-picker
                v-model="filters.end_time"
                type="datetime"
                value-format="YYYY-MM-DDTHH:mm:ss"
                placeholder="选择结束时间"
              />
            </el-form-item>
          </div>

          <el-form-item label="导出条数">
            <el-input-number
              v-model="filters.limit"
              :min="100"
              :max="20000"
              :step="100"
            />
          </el-form-item>
        </el-form>

        <el-button
          type="primary"
          size="large"
          :icon="Download"
          :loading="downloading"
          class="download-btn"
          @click="handleDownload"
        >
          {{ downloading ? '正在生成报表...' : '导出 CSV 报表' }}
        </el-button>
      </article>

      <aside class="report-panel report-panel--summary glass-panel">
        <div class="panel-title-row">
          <div>
            <p class="section-label">导出范围</p>
            <h2>当前配置</h2>
          </div>
        </div>

        <el-alert
          :title="exportHint"
          :type="hasScopedAccess ? 'warning' : 'info'"
          :closable="false"
          show-icon
        />

        <div class="scope-list">
          <div
            v-for="row in exportScopeRows"
            :key="row.label"
            class="scope-row"
          >
            <span>{{ row.label }}</span>
            <strong>{{ row.value }}</strong>
          </div>
        </div>
      </aside>
    </section>
  </div>
</template>

<style scoped>
.report-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100%;
  width: 100%;
  padding: 16px;
  overflow-x: hidden;
  box-sizing: border-box;
  color: #f5f7fa;
  background:
    radial-gradient(circle at top left, rgba(96, 165, 250, 0.08), transparent 28%),
    radial-gradient(circle at bottom right, rgba(52, 211, 153, 0.05), transparent 26%),
    #090e17;
}

.report-noise {
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

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 112px;
  padding: 22px;
  box-sizing: border-box;
}

.report-brand-block {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.report-brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  margin-top: 2px;
  border-radius: 14px;
  flex-shrink: 0;
  color: #67e8f9;
  background: rgba(103, 232, 249, 0.12);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
}

.report-brand-mark :deep(svg) {
  width: 22px;
  height: 22px;
}

.report-brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.report-eyebrow {
  margin: 0;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.46);
}

.report-brand-text h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.02;
  letter-spacing: 0;
  color: #f5f7fa;
}

.report-subtitle {
  margin: 0;
  max-width: 600px;
  font-size: 12px;
  line-height: 1.3;
  color: rgba(255,255,255,0.44);
}

.report-tags,
.report-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.report-tags {
  margin-top: 8px;
}

.report-header-actions {
  justify-content: flex-end;
  flex-shrink: 0;
}

.report-tag {
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

.report-tag--warn {
  color: #fdba74;
  border-color: rgba(251, 146, 60, 0.28);
  background: rgba(251, 146, 60, 0.08);
}

.report-workspace {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 12px;
  align-items: start;
}

.report-panel {
  padding: 18px 20px 20px;
}

.report-panel--summary {
  position: sticky;
  top: 12px;
}

.panel-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  margin-bottom: 14px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.section-label {
  margin: 0 0 4px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.4);
}

.panel-title-row h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
  letter-spacing: 0;
  color: #f0f6ff;
}

.panel-title-icon {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  color: #93c5fd;
  background: rgba(96, 165, 250, 0.1);
}

.scope-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 14px;
}

.scope-row {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  min-height: 36px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(255,255,255,0.035);
  border: 1px solid rgba(255,255,255,0.055);
}

.scope-row span {
  font-size: 12px;
  color: rgba(255,255,255,0.42);
}

.scope-row strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 600;
  color: rgba(248,250,252,0.86);
}

.report-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 16px;
}

.report-form :deep(.el-form-item__label) {
  color: rgba(226,232,240,0.62);
  font-weight: 500;
}

.report-form :deep(.el-form-item:first-child) {
  grid-column: 1 / -1;
}

.report-form :deep(.el-select),
.report-form :deep(.el-date-editor),
.report-form :deep(.el-input-number) {
  width: 100%;
}

.report-form :deep(.el-input__wrapper),
.report-form :deep(.el-select__wrapper),
.report-form :deep(.el-input-number .el-input__wrapper) {
  min-height: 38px;
  border-radius: 8px;
  background: rgba(255,255,255,0.055);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
}

.report-form :deep(.el-input__inner),
.report-form :deep(.el-select__selected-item),
.report-form :deep(.el-select__placeholder) {
  color: rgba(255,255,255,0.84);
}

.report-form :deep(.el-input__inner::placeholder),
.report-form :deep(.el-select__placeholder.is-transparent) {
  color: rgba(255,255,255,0.3);
}

.report-form :deep(.el-input-number__decrease),
.report-form :deep(.el-input-number__increase) {
  border-color: rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.055);
  color: rgba(255,255,255,0.58);
}

.report-type-group {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  width: 100%;
}

.report-type-group :deep(.el-radio-button__inner) {
  width: 100%;
  min-height: 38px;
  padding: 10px 12px;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  background: rgba(255,255,255,0.04);
  color: rgba(226,232,240,0.72);
  box-shadow: none;
}

.report-type-group :deep(.el-radio-button:first-child .el-radio-button__inner),
.report-type-group :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 10px;
}

.report-type-group :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  border-color: rgba(103, 232, 249, 0.46);
  background: rgba(103, 232, 249, 0.14);
  color: #67e8f9;
}

.date-row {
  display: contents;
}

.download-btn {
  width: 100%;
  min-height: 42px;
  margin-top: 8px;
  border-radius: 22px;
  grid-column: 1 / -1;
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

:deep(.el-alert) {
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.04);
}

:deep(.el-alert__title) {
  line-height: 1.5;
  color: rgba(226,232,240,0.68);
}

:deep(.el-alert--warning) {
  border-color: rgba(251, 146, 60, 0.24);
  background: rgba(251, 146, 60, 0.08);
}

:deep(.el-alert--info) {
  border-color: rgba(96, 165, 250, 0.2);
  background: rgba(96, 165, 250, 0.08);
}

@media (max-width: 1100px) {
  .report-workspace {
    grid-template-columns: 1fr;
  }

  .report-panel--summary {
    position: relative;
    top: auto;
  }
}

@media (max-width: 768px) {
  .report-page {
    padding: 12px;
    gap: 10px;
  }

  .report-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 14px 16px;
  }

  .report-brand-text h1 {
    font-size: 22px;
  }

  .report-header-actions {
    justify-content: flex-start;
    width: 100%;
  }

  .report-form,
  .report-type-group {
    grid-template-columns: 1fr;
  }

  .report-panel {
    padding: 14px 16px;
  }

  .scope-row {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
