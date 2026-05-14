<script setup lang="ts">
import { computed, ref } from 'vue'
import { Warning } from '@element-plus/icons-vue'
import type { PropType } from 'vue'
import type { DeviceAlarmRecord } from '@/api/deviceMonitor'
import { alarmSourceLabel } from '@/features/alarm/sourceLabels'

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

const PAGE_SIZE = 20

const severityFilter = ref<string>('')
const resolvedFilter = ref<string>('')
const currentPage = ref(1)

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
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredRows.value.slice(start, start + PAGE_SIZE)
})

const showPagination = computed(() => filteredRows.value.length > PAGE_SIZE)

const unresolvedCount = computed(() => props.rows.filter(r => !r.is_resolved).length)

function severityTagType(severity?: string) {
  if (severity === 'critical') return 'danger'
  if (severity === 'warning') return 'warning'
  if (severity === 'info') return 'primary'
  return 'info'
}

function formatTime(value?: string | null) {
  if (!value) return '暂无数据'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

function resetPage() {
  currentPage.value = 1
}
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
          <el-tag :type="severityTagType(row.severity)">
            {{ row.severity || 'info' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="source"
        label="来源"
        width="110"
      >
        <template #default="{ row }">
          <el-tag type="info" effect="plain">
            {{ alarmSourceLabel(row.source) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="is_resolved"
        label="状态"
        width="110"
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
            class="alarm-action-button"
            type="warning"
            link
            :icon="Warning"
            :loading="actionId === row.id"
            @click="$emit('resolve', row)"
          >
            标记处理
          </el-button>
          <span
            v-else
            class="muted-text"
          >
            已关闭
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
        :page-size="PAGE_SIZE"
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
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
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

.alarm-action-button {
  color: #fbbf24;
}

.alarm-action-button:hover {
  color: #fde68a;
}

.muted-text {
  color: #8ea0bc;
  font-size: 12px;
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
