<script setup lang="ts">
import type { PropType } from 'vue'
import type { CompensationProfileItem } from './types'

defineProps({
  summaryItems: {
    type: Array as PropType<CompensationProfileItem[]>,
    default: () => [],
  },
  capacityExpansionItems: {
    type: Array as PropType<CompensationProfileItem[]>,
    default: () => [],
  },
  hasSummaryData: {
    type: Boolean,
    default: false,
  },
})
</script>

<template>
  <section class="side-panel side-panel--muted control-summary-panel">
    <div class="side-panel__head">
      <div class="control-summary-headline">
        <h3>控制参数摘要</h3>
        <div class="control-summary-badges">
          <span class="control-summary-badge">只读摘要</span>
          <span class="control-summary-badge control-summary-badge--accent">控制台查看完整参数</span>
        </div>
      </div>
    </div>

    <div
      v-if="hasSummaryData"
      class="profile-list"
    >
      <div
        v-for="item in summaryItems"
        :key="item.label"
        class="profile-row"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </div>
    </div>

    <div
      v-if="capacityExpansionItems.length"
      class="capacity-expansion-list"
    >
      <div class="capacity-expansion-list__head">
        <strong>容量展开</strong>
        <span>按 JKWF 容量编码与阶梯容量推导每一路配置</span>
      </div>
      <div
        v-for="item in capacityExpansionItems"
        :key="item.label"
        class="capacity-expansion-row"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </div>
    </div>

    <div
      v-else
      class="control-summary-empty"
    >
      <strong>暂无参数</strong>
      <span>当前设备还没有可回读的 JKWF 参数快照。</span>
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

.side-panel--muted {
  opacity: 0.92;
}

.side-panel__head {
  margin-bottom: 12px;
}

.side-panel__head h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.control-summary-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-summary-headline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.control-summary-badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.control-summary-badge {
  flex-shrink: 0;
  padding: 3px 8px;
  border-radius: 999px;
  border: 1px solid rgba(83, 110, 140, 0.55);
  background: rgba(34, 52, 77, 0.72);
  color: #9eb3cf;
  font-size: 11px;
  line-height: 1.4;
  white-space: nowrap;
}

.control-summary-badge--accent {
  border-color: rgba(76, 171, 255, 0.35);
  background: rgba(22, 90, 146, 0.2);
  color: #b9ddff;
}

.profile-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.profile-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(41, 57, 77, 0.72);
}

.profile-row:last-child {
  border-bottom: none;
}

.profile-row span {
  color: #91a5c4;
  font-size: 12px;
}

.profile-row strong {
  color: #dfe8f5;
  font-size: 12px;
  text-align: right;
  max-width: 60%;
  line-height: 1.5;
  word-break: break-word;
}

.control-summary-empty {
  min-height: 92px;
  border: 1px dashed rgba(63, 82, 107, 0.72);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 6px;
  color: #8ea0bc;
  text-align: center;
  padding: 12px;
}

.control-summary-empty strong {
  color: #eef4ff;
}

.capacity-expansion-list {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed rgba(93, 115, 145, 0.35);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.capacity-expansion-list__head {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.capacity-expansion-list__head strong {
  color: #edf3ff;
  font-size: 13px;
}

.capacity-expansion-list__head span {
  color: #8ea0bc;
  font-size: 11px;
}

.capacity-expansion-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(60, 79, 103, 0.6);
  background: rgba(18, 28, 42, 0.82);
}

.capacity-expansion-row span {
  color: #90a2bf;
  font-size: 11px;
}

.capacity-expansion-row strong {
  color: #f5f7fb;
  font-size: 12px;
  line-height: 1.5;
}
</style>
