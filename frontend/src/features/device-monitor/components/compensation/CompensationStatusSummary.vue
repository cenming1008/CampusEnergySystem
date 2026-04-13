<script setup lang="ts">
import type { PropType } from 'vue'
import type { CompensationStatusItem } from './types'

defineProps({
  items: {
    type: Array as PropType<CompensationStatusItem[]>,
    default: () => [],
  },
})

function textClass(tone?: CompensationStatusItem['tone']) {
  if (tone === 'success') return 'is-success'
  if (tone === 'warning') return 'is-warning'
  if (tone === 'danger') return 'is-danger'
  if (tone === 'info') return 'is-info'
  return ''
}
</script>

<template>
  <section class="side-panel">
    <div class="side-panel__head">
      <h3>运行状态</h3>
      <span>聚焦补偿器当前可操作与运行稳定性</span>
    </div>

    <div class="status-list">
      <div
        v-for="item in items"
        :key="item.label"
        class="status-row"
      >
        <div class="status-row__meta">
          <span>{{ item.label }}</span>
          <small v-if="item.hint">{{ item.hint }}</small>
        </div>
        <strong :class="textClass(item.tone)">{{ item.value }}</strong>
      </div>
    </div>
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

.side-panel__head span {
  display: block;
  margin-top: 4px;
  color: #8ea0bc;
  font-size: 12px;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 0;
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

.status-row__meta small {
  color: #6f84a5;
  font-size: 11px;
}

.status-row strong {
  font-size: 13px;
  color: #f5f7fb;
  text-align: right;
}

.is-success {
  color: #4ade80;
}

.is-warning {
  color: #fbbf24;
}

.is-danger {
  color: #fb7185;
}

.is-info {
  color: #60a5fa;
}
</style>
