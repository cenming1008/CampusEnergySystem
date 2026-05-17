<script setup lang="ts">
import type { PropType } from 'vue'
import type { CompensationProfileItem } from './types'
import { usePanelCollapse } from '@/shared/composables/usePanelCollapse'
import PanelCollapseToggle from '@/shared/components/PanelCollapseToggle.vue'

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

const emit = defineEmits<{
  (event: 'open-console'): void
}>()

const { collapsed, toggle } = usePanelCollapse('compensation-monitor:collapse:control-summary', false)
</script>

<template>
  <section class="side-panel side-panel--muted control-summary-panel">
    <div class="side-panel__head">
      <div class="control-summary-headline">
        <div class="control-summary-title">
          <h3>控制参数摘要</h3>
          <span class="control-summary-hint">仅展示参数概览</span>
        </div>
        <el-button
          link
          type="primary"
          class="control-summary-console-link"
          @click="emit('open-console')"
        >
          打开控制台 →
        </el-button>
        <PanelCollapseToggle
          :collapsed="collapsed"
          @toggle="toggle"
        />
      </div>
    </div>

    <div
      v-show="!collapsed"
      class="control-summary-body"
    >
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

.control-summary-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.control-summary-hint {
  font-size: var(--font-caption);
  color: var(--text-label);
  line-height: 1.4;
}

.control-summary-console-link {
  flex-shrink: 0;
  min-height: var(--touch-target);
  font-size: var(--font-caption);
  font-weight: 500;
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
  border-bottom: 1px solid var(--divider);
}

.profile-row:last-child {
  border-bottom: none;
}

.profile-row span {
  color: var(--text-label);
  font-size: var(--font-caption);
}

.profile-row strong {
  color: #dfe8f5;
  font-size: var(--font-caption);
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
  color: var(--text-label);
  font-size: var(--font-caption);
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
  color: var(--text-label);
  font-size: var(--font-caption);
}

.capacity-expansion-row strong {
  color: #f5f7fb;
  font-size: var(--font-caption);
  line-height: 1.5;
}

.control-summary-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
