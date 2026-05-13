<script setup lang="ts">
import { computed, ref } from 'vue'
import type { StorageRunState, StorageTone } from './types'

const props = defineProps<{
  runState: StorageRunState
  runStateLabel: string
  controlMode: string
  soh: string
  cycleCount: string
  cellTempMax: string
  cellTempMin: string
  cellTempAvg: string
  faultCode: string
  alarmCode: string
  ingestionStatus: string
  ingestionTone: StorageTone
  unresolvedAlarmCount: number
  latestSampleText: string
}>()

const PINNED_COUNT = 5
const collapsed = ref(true)

interface StatusRow { label: string; value: string; tone?: StorageTone; hint?: string }

const allItems = computed<StatusRow[]>(() => [
  {
    label: '工作状态',
    value: props.runStateLabel,
    tone: props.runState === 'charging' ? 'info'
        : props.runState === 'discharging' ? 'success'
        : props.runState === 'fault' ? 'danger'
        : undefined,
  },
  { label: '控制模式', value: props.controlMode },
  { label: '健康状态（SOH）', value: props.soh },
  { label: '循环次数', value: props.cycleCount },
  { label: '电池最高温', value: props.cellTempMax },
  { label: '电池最低温', value: props.cellTempMin },
  { label: '电池平均温', value: props.cellTempAvg },
  {
    label: '故障码',
    value: props.faultCode,
    tone: props.faultCode !== '--' ? 'danger' : undefined,
  },
  {
    label: '告警码',
    value: props.alarmCode,
    tone: props.alarmCode !== '--' ? 'warning' : undefined,
  },
  { label: '采集状态', value: props.ingestionStatus, tone: props.ingestionTone },
  {
    label: '未处理告警',
    value: `${props.unresolvedAlarmCount} 条`,
    tone: props.unresolvedAlarmCount > 0 ? 'danger' : undefined,
  },
  { label: '最近采样', value: props.latestSampleText },
])

const visibleItems = computed(() =>
  collapsed.value ? allItems.value.slice(0, PINNED_COUNT) : allItems.value,
)
const hasMore = computed(() => allItems.value.length > PINNED_COUNT)

function textClass(tone?: StorageTone) {
  if (tone === 'success') return 'is-success'
  if (tone === 'warning') return 'is-warning'
  if (tone === 'danger') return 'is-danger'
  if (tone === 'info') return 'is-info'
  return ''
}

function toneIcon(tone?: StorageTone) {
  if (tone === 'success') return '✓'
  if (tone === 'warning') return '!'
  if (tone === 'danger') return '✕'
  if (tone === 'info') return 'ℹ'
  return ''
}
</script>

<template>
  <section class="side-panel">
    <div class="side-panel__head">
      <h3>运行状态</h3>
    </div>

    <div class="status-list">
      <div
        v-for="item in visibleItems"
        :key="item.label"
        class="status-row"
      >
        <div class="status-row__meta">
          <el-tooltip v-if="item.hint" :content="item.hint" placement="top">
            <span class="label-with-hint">{{ item.label }}</span>
          </el-tooltip>
          <span v-else>{{ item.label }}</span>
        </div>
        <div
          class="status-row__value"
          :class="textClass(item.tone)"
        >
          <span v-if="item.tone" class="tone-icon">{{ toneIcon(item.tone) }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
    </div>

    <button
      v-if="hasMore"
      class="collapse-toggle"
      @click="collapsed = !collapsed"
    >
      {{ collapsed ? `展开全部 (${allItems.length - PINNED_COUNT} 项)` : '收起' }}
    </button>
  </section>
</template>

<style scoped>
.side-panel {
  padding: 16px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
}

.side-panel__head {
  margin-bottom: 12px;
}

.side-panel__head h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.status-list {
  display: flex;
  flex-direction: column;
}

.status-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 9px 0;
  border-bottom: 1px solid rgba(41, 57, 77, 0.72);
}

.status-row:last-child {
  border-bottom: none;
}

.status-row__meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-row__meta span {
  color: #aebbd0;
  font-size: 12px;
}

.label-with-hint {
  cursor: default;
  border-bottom: 1px dashed rgba(110, 132, 165, 0.4);
}

.status-row__value {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.status-row__value strong {
  font-size: 13px;
  color: #f5f7fb;
  text-align: right;
}

.tone-icon {
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.is-success strong,
.is-success .tone-icon { color: #4ade80; }

.is-warning strong,
.is-warning .tone-icon { color: #fbbf24; }

.is-danger strong,
.is-danger .tone-icon { color: #fb7185; }

.is-info strong,
.is-info .tone-icon { color: #60a5fa; }

.collapse-toggle {
  display: block;
  width: 100%;
  margin-top: 10px;
  padding: 6px 0;
  border: 1px solid rgba(53, 72, 97, 0.5);
  border-radius: 8px;
  background: transparent;
  color: #7f93b2;
  font-size: 11px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.collapse-toggle:hover {
  color: #c5d2e7;
  border-color: rgba(90, 120, 160, 0.5);
}
</style>
