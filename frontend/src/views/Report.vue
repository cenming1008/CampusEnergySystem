<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Download, Document } from '@element-plus/icons-vue'
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
    <section class="report-hero">
      <div>
        <p class="eyebrow">
          Report Center
        </p>
        <h1>多类型报表导出</h1>
        <p class="hero-copy">
          {{ selectedReportMeta.description }}
        </p>
      </div>
      <el-alert
        :title="exportHint"
        :type="hasScopedAccess ? 'warning' : 'info'"
        :closable="false"
        show-icon
      />
    </section>

    <section class="report-grid">
      <article class="report-card">
        <div class="card-header">
          <el-icon class="card-icon">
            <Document />
          </el-icon>
          <div>
            <h2>{{ selectedReportMeta.label }}</h2>
            <p>按报表类型、设备、时间窗与状态导出 CSV。</p>
          </div>
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
    </section>
  </div>
</template>

<style scoped>
.report-page {
  min-height: calc(100vh - 120px);
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.12), transparent 30%),
    radial-gradient(circle at bottom right, rgba(16, 185, 129, 0.12), transparent 28%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.98));
}

.report-hero {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 20px;
  align-items: start;
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #93c5fd;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: #f8fafc;
  font-size: 32px;
}

.hero-copy {
  margin: 12px 0 0;
  color: #cbd5e1;
  line-height: 1.7;
}

.report-grid {
  display: grid;
  grid-template-columns: minmax(0, 900px);
}

.report-card {
  background: rgba(15, 23, 42, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.28);
  backdrop-filter: blur(12px);
}

.card-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  align-items: center;
}

.card-header h2 {
  margin: 0 0 6px;
  color: #f8fafc;
}

.card-header p {
  margin: 0;
  color: #94a3b8;
}

.card-icon {
  font-size: 32px;
  color: #60a5fa;
  background: rgba(59, 130, 246, 0.12);
  border-radius: 14px;
  padding: 14px;
}

.report-form :deep(.el-form-item__label) {
  color: #cbd5e1;
}

.report-type-group {
  display: flex;
  flex-wrap: wrap;
}

.date-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.download-btn {
  width: 100%;
  margin-top: 16px;
}

@media (max-width: 900px) {
  .report-hero,
  .date-row {
    grid-template-columns: 1fr;
  }

  .report-page {
    padding: 16px;
  }

  h1 {
    font-size: 26px;
  }
}
</style>
