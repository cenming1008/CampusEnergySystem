<script setup lang="ts">
import { type PropType } from 'vue'
import type { CompensationMetric } from './types'

defineProps({
  items: {
    type: Array as PropType<CompensationMetric[]>,
    default: () => [],
  },
  columns: {
    type: Number,
    default: 6,
  },
})

function stateTagText(state: CompensationMetric['state']) {
  if (state === 'live') return '● 实时'
  if (state === 'mock') return '◑ 估算'
  if (state === 'missing') return '✕ 缺测'
  if (state === 'offline') return '⊘ 离线'
  if (state === 'unconfigured') return '○ 待配置'
  return ''
}

function stateTagType(state: CompensationMetric['state']) {
  if (state === 'live') return 'success'
  if (state === 'mock') return 'warning'
  if (state === 'missing' || state === 'offline') return 'danger'
  if (state === 'unconfigured') return 'info'
  return 'info'
}

function isUnavailableState(state: CompensationMetric['state']) {
  return state === 'missing' || state === 'offline'
}

function displayMetricValue(item: CompensationMetric) {
  if (isUnavailableState(item.state)) return '--'
  if (item.value === '暂无数据' || item.value === '通讯中断') return '--'
  return item.value
}
</script>

<template>
  <div
    class="metric-strip"
    :style="{ '--strip-columns': columns }"
  >
    <div
      v-for="item in items"
      :key="item.key"
      class="metric-strip__cell"
      :class="{ 'metric-strip__cell--waiting': isUnavailableState(item.state) }"
    >
      <div class="metric-strip__label-row">
        <el-tooltip
          :content="item.hint"
          placement="top"
          :disabled="!item.hint"
        >
          <span class="metric-strip__label">{{ item.label }}</span>
        </el-tooltip>
        <el-tag
          v-if="item.state && item.state !== 'live'"
          size="small"
          effect="plain"
          :type="stateTagType(item.state)"
        >
          {{ stateTagText(item.state) }}
        </el-tag>
      </div>
      <div
        class="metric-strip__value"
        :class="item.tone ? `tone-${item.tone}` : ''"
      >
        <strong>{{ displayMetricValue(item) }}</strong>
        <small v-if="item.unit && !isUnavailableState(item.state)">{{ item.unit }}</small>
      </div>
    </div>
  </div>
</template>

<style scoped>
.metric-strip {
  display: grid;
  grid-template-columns: repeat(var(--strip-columns, 6), minmax(0, 1fr));
  gap: 8px;
}

.metric-strip__cell {
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-top: 3px solid rgba(59, 130, 246, 0.25);
  border-radius: 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 6px;
  min-height: 88px;
}

.metric-strip__cell--waiting {
  border-top-color: rgba(100, 116, 139, 0.22);
}

.metric-strip__label-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.metric-strip__label {
  font-size: 13px;
  color: #8ea0bc;
  line-height: 1.3;
  font-weight: 600;
}

.metric-strip__value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  width: 100%;
}

.metric-strip__value strong {
  font-size: 26px;
  line-height: 1;
  color: #f5f7fb;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
}

.metric-strip__value small {
  font-size: 12px;
  color: #7f93b2;
}

.metric-strip__cell--waiting .metric-strip__value strong {
  color: #a8b6ca;
}

.tone-success .metric-strip__value strong { color: #4ade80; }
.tone-warning .metric-strip__value strong { color: #fbbf24; }
.tone-danger  .metric-strip__value strong { color: #fb7185; }
.tone-info    .metric-strip__value strong { color: #60a5fa; }

@media (max-width: 1380px) {
  .metric-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .metric-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
