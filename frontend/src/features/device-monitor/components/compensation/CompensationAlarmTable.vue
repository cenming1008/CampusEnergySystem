<script setup lang="ts">
import { computed, ref } from 'vue'
import { CircleCheck, Warning } from '@element-plus/icons-vue'
import type { PropType } from 'vue'
import type { DeviceAlarmRecord } from '@/api/deviceMonitor'

const props = defineProps({
  rows: {
    type: Array as PropType<DeviceAlarmRecord[]>,
    default: () => [],
  },
  actionId: {
    type: Number as PropType<number | null>,
    default: null,
  },
})

defineEmits<{
  resolve: [row: DeviceAlarmRecord]
}>()

const PAGE_SIZE_OPTIONS = [10, 50, 100]

const severityFilter = ref<string>('')
const resolvedFilter = ref<string>('')
const currentPage = ref(1)
const pageSize = ref(50)

const filteredRows = computed(() => {
  let result = props.rows
  if (severityFilter.value) {
    result = result.filter(r => r.severity === severityFilter.value)
  }
  if (resolvedFilter.value === 'resolved') {
    result = result.filter(r => r.is_resolved)
  } else if (resolvedFilter.value === 'unresolved') {
    result = result.filter(r => !r.is_resolved)
  }
  return result
})

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRows.value.slice(start, start + pageSize.value)
})

const showPagination = computed(() => filteredRows.value.length > pageSize.value)

const unresolvedCount = computed(() => props.rows.filter(r => !r.is_resolved).length)

function severityToneClass(severity?: string) {
  if (severity === 'critical') return 'severity-pill--critical'
  if (severity === 'warning') return 'severity-pill--warning'
  if (severity === 'info') return 'severity-pill--info'
  return 'severity-pill--unknown'
}

function severityLabel(severity?: string) {
  if (severity === 'critical') return '紧急'
  if (severity === 'warning') return '警告'
  if (severity === 'info') return '信息'
  return severity || '未知'
}

function actionLabel(row: DeviceAlarmRecord) {
  return row.is_resolved ? '已处理' : '处理'
}

function actionToneClass(row: DeviceAlarmRecord) {
  return row.is_resolved ? 'alarm-action-pill--resolved' : 'alarm-action-pill--pending'
}

function formatTime(value?: string | null) {
  if (!value) return '暂无数据'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

function resetPage() {
  currentPage.value = 1
}

function handlePageSizeChange() {
  resetPage()
}

defineExpose({
  actionLabel,
  actionToneClass,
  severityLabel,
  severityToneClass,
})
</script>

<template>
  <section class="alarm-panel">
    <div class="alarm-panel__head">
      <div>
        <h3>
          告警记录
          <span
            v-if="unresolvedCount > 0"
            class="unresolved-badge"
          >{{ unresolvedCount }} 未处理</span>
        </h3>
      </div>

      <div class="alarm-filters">
        <div class="page-size-tabs">
          <span>每页</span>
          <el-segmented
            v-model="pageSize"
            aria-label="每页条数"
            :options="PAGE_SIZE_OPTIONS"
            size="small"
            @change="handlePageSizeChange"
          />
        </div>
        <el-select
          v-model="severityFilter"
          placeholder="全部级别"
          size="small"
          clearable
          style="width: 100px"
          @change="resetPage"
        >
          <el-option label="紧急" value="critical" />
          <el-option label="警告" value="warning" />
          <el-option label="信息" value="info" />
        </el-select>
        <el-select
          v-model="resolvedFilter"
          placeholder="全部状态"
          size="small"
          clearable
          style="width: 100px"
          @change="resetPage"
        >
          <el-option label="未处理" value="unresolved" />
          <el-option label="已处理" value="resolved" />
        </el-select>
      </div>
    </div>

    <el-table
      :data="pagedRows"
      class="dark-table"
      empty-text="当前暂无匹配告警记录"
      max-height="520"
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
        label="告警内容"
        min-width="280"
      />
      <el-table-column
        prop="severity"
        label="级别"
        width="110"
      >
        <template #default="{ row }">
          <span
            class="severity-pill"
            :class="severityToneClass(row.severity)"
          >
            <i />
            {{ severityLabel(row.severity) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column
        label="操作"
        width="132"
        align="center"
      >
        <template #default="{ row }">
          <el-button
            v-if="!row.is_resolved"
            class="alarm-action-button"
            :class="actionToneClass(row)"
            :icon="Warning"
            :loading="actionId === row.id"
            @click="$emit('resolve', row)"
          >
            {{ actionLabel(row) }}
          </el-button>
          <span
            v-else
            class="alarm-action-state"
            :class="actionToneClass(row)"
          >
            <el-icon><CircleCheck /></el-icon>
            {{ actionLabel(row) }}
          </span>
        </template>
      </el-table-column>
    </el-table>

    <div
      v-if="showPagination"
      class="alarm-pagination"
    >
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="filteredRows.length"
        layout="prev, pager, next, total"
        small
        background
      />
    </div>
  </section>
</template>

<style scoped>
.alarm-panel {
  padding: 18px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
}

.alarm-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.alarm-panel__head h3 {
  margin: 0;
  font-size: 16px;
  color: #f5f7fb;
  display: flex;
  align-items: center;
  gap: 8px;
}

.alarm-panel__head span {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #8ea0bc;
}

.unresolved-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 7px;
  border-radius: 10px;
  background: rgba(248, 113, 113, 0.15);
  border: 1px solid rgba(248, 113, 113, 0.35);
  color: #fb7185;
}

.alarm-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.page-size-tabs {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #8ea0bc;
  font-size: 12px;
}

.page-size-tabs :deep(.el-segmented) {
  --el-segmented-bg-color: rgba(7, 15, 26, 0.72);
  --el-segmented-item-selected-color: #eff6ff;
  --el-segmented-item-selected-bg-color: rgba(37, 99, 235, 0.56);
  --el-border-radius-base: 8px;
  height: 30px;
  padding: 0 2px;
  display: flex;
  align-items: center;
  border: 1px solid rgba(72, 96, 130, 0.72);
}

.page-size-tabs :deep(.el-segmented__item) {
  min-height: 24px;
  padding: 0 8px;
  color: #9fb3d1;
}

.page-size-tabs :deep(.el-segmented__item-label) {
  line-height: 24px;
}

.alarm-filters :deep(.el-select__wrapper) {
  min-height: 30px;
  background: rgba(7, 15, 26, 0.72);
  border: 1px solid rgba(72, 96, 130, 0.72);
  border-radius: 8px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.alarm-filters :deep(.el-select__wrapper.is-hovering),
.alarm-filters :deep(.el-select__wrapper.is-focused) {
  border-color: rgba(96, 165, 250, 0.5);
  box-shadow: 0 0 0 1px rgba(96, 165, 250, 0.18);
}

.alarm-filters :deep(.el-select__placeholder),
.alarm-filters :deep(.el-select__selected-item) {
  color: #dbeafe;
}

.alarm-filters :deep(.el-select__caret) {
  color: #7f93b2;
}

.severity-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-width: 72px;
  height: 26px;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  border: 1px solid transparent;
  background: rgba(15, 23, 42, 0.7);
}

.severity-pill i {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  flex-shrink: 0;
  box-shadow: 0 0 0 3px currentColor;
  opacity: 0.55;
}

.severity-pill--critical {
  color: #fecaca;
  background: rgba(127, 29, 29, 0.28);
  border-color: rgba(248, 113, 113, 0.48);
}

.severity-pill--warning {
  color: #fde68a;
  background: rgba(120, 53, 15, 0.28);
  border-color: rgba(251, 191, 36, 0.46);
}

.severity-pill--info {
  color: #bfdbfe;
  background: rgba(30, 64, 175, 0.24);
  border-color: rgba(96, 165, 250, 0.42);
}

.severity-pill--unknown {
  color: #cbd5e1;
  background: rgba(51, 65, 85, 0.35);
  border-color: rgba(148, 163, 184, 0.32);
}

.alarm-action-button {
  height: 28px;
  min-width: 74px;
  padding: 0 12px;
  border-radius: 999px;
  font-weight: 700;
  letter-spacing: 0;
  border: 1px solid rgba(251, 191, 36, 0.46);
  background: rgba(120, 53, 15, 0.18);
  color: #fbbf24;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.alarm-action-button:hover,
.alarm-action-button:focus {
  border-color: rgba(251, 191, 36, 0.72);
  background: rgba(120, 53, 15, 0.32);
  color: #fde68a;
}

.alarm-action-state {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  height: 28px;
  min-width: 74px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
}

.alarm-action-pill--pending {
  color: #fbbf24;
}

.alarm-action-pill--resolved {
  color: #9fb3d1;
  background: rgba(51, 65, 85, 0.28);
  border: 1px solid rgba(148, 163, 184, 0.24);
}

.alarm-action-state :deep(.el-icon) {
  font-size: 13px;
}

.alarm-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

:deep(.dark-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(14, 24, 37, 0.92);
  --el-table-border-color: #243244;
  --el-table-row-hover-bg-color: rgba(22, 33, 48, 0.92);
  --el-table-text-color: #dbe6f5;
  --el-table-header-text-color: #8ea0bc;
}
</style>
