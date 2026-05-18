<script setup lang="ts">
import { computed, ref } from 'vue'
import type {
  ControlConsoleReadonlySectionView,
  ControlConsoleReadonlySummaryView,
} from '@/features/device-control/viewMapping'
import ControlConsoleParameterSection from '@/features/device-control/components/ControlConsoleParameterSection.vue'

const props = defineProps<{
  sectionView: ControlConsoleReadonlySectionView
  readonlySummaryView: ControlConsoleReadonlySummaryView
}>()

const capacityExpanded = ref(false)
const parametersExpanded = ref(false)

const compactSummaryItems = computed(() => props.readonlySummaryView.summaryItems.slice(0, 6))
const snapshotTimeText = computed(() => {
  const marker = '快照：'
  const value = props.sectionView.metaText || ''
  return value.includes(marker) ? value.split(marker).pop()?.trim() || '' : value
})
</script>

<template>
  <ControlConsoleParameterSection
    title=""
    :section-label="sectionView.sectionLabel"
    :tone="sectionView.tone"
    :tags="sectionView.tags"
    :meta-text="snapshotTimeText"
  >
    <div class="readonly-summary-grid">
      <div
        v-for="item in compactSummaryItems"
        :key="item.label"
        class="readonly-summary-card"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </div>
    </div>

    <div class="readonly-detail-actions">
      <button
        v-if="sectionView.showCapacityExpansion"
        type="button"
        class="readonly-detail-toggle"
        data-test="toggle-capacity"
        @click="capacityExpanded = !capacityExpanded"
      >
        <span>容量展开详情</span>
        <strong>{{ capacityExpanded ? '收起' : '展开' }}</strong>
      </button>
      <button
        type="button"
        class="readonly-detail-toggle"
        data-test="toggle-parameters"
        @click="parametersExpanded = !parametersExpanded"
      >
        <span>全部参数明细</span>
        <strong>{{ parametersExpanded ? '收起' : '展开' }}</strong>
      </button>
    </div>

    <div
      v-if="sectionView.showCapacityExpansion && capacityExpanded"
      class="capacity-expansion-panel"
    >
      <div class="capacity-expansion-panel__head">
        <strong>容量展开详情</strong>
      </div>
      <div class="capacity-expansion-grid">
        <div
          v-for="item in readonlySummaryView.capacityExpansionItems"
          :key="item.label"
          class="capacity-expansion-card"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
    </div>
    <div
      v-if="parametersExpanded"
      class="param-groups"
    >
      <section
        v-for="group in readonlySummaryView.groupedParameters"
        :key="group.key"
        class="param-group"
      >
        <header class="param-group__head">
          <h4>{{ group.label }}</h4>
          <span>{{ group.items.length }} 个参数</span>
        </header>
        <div class="param-table">
          <div class="param-table__row param-table__row--head">
            <span>参数 / 说明</span>
            <span>当前值</span>
            <span class="param-table__meta-col">寄存器 · 读写</span>
          </div>
          <div
            v-for="item in group.items"
            :key="item.key"
            class="param-table__row"
          >
            <div class="param-table__label">
              <strong>{{ item.label }}</strong>
              <small>{{ item.description }}</small>
            </div>
            <span class="param-table__value">{{ item.currentValue }}</span>
            <div class="param-table__meta param-table__meta-col">
              <span>{{ item.register }}</span>
              <small>{{ item.readWrite }}</small>
            </div>
          </div>
        </div>
      </section>
    </div>
  </ControlConsoleParameterSection>
</template>

<style scoped>
.readonly-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.readonly-summary-card {
  min-height: 72px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(48, 70, 95, 0.68);
  background:
    linear-gradient(180deg, rgba(45, 212, 191, 0.035), rgba(12, 24, 39, 0.74)),
    rgba(16, 28, 44, 0.72);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}

.readonly-summary-card span {
  color: #91a5c2;
  font-size: 11px;
}

.readonly-summary-card strong {
  color: #f7fbff;
  font-size: 14px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.readonly-detail-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.readonly-detail-toggle {
  min-height: 40px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid rgba(71, 100, 135, 0.4);
  background: rgba(12, 22, 38, 0.62);
  color: #c8d8ee;
  font: inherit;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  cursor: pointer;
}

.readonly-detail-toggle:hover {
  border-color: rgba(45, 212, 191, 0.42);
}

.readonly-detail-toggle span {
  font-size: 12px;
}

.readonly-detail-toggle strong {
  color: #5eead4;
  font-size: 12px;
}

.capacity-expansion-panel {
  margin-top: 12px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background: rgba(12, 22, 38, 0.64);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.capacity-expansion-panel__head {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.capacity-expansion-panel__head strong {
  color: #f7fbff;
  font-size: 13px;
}


.capacity-expansion-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.capacity-expansion-card {
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(55, 73, 96, 0.58);
  background: rgba(16, 28, 44, 0.68);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.capacity-expansion-card span {
  color: #91a5c2;
  font-size: 11px;
}

.capacity-expansion-card strong {
  color: #f7fbff;
  font-size: 12px;
  line-height: 1.5;
}

.param-groups {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.param-group {
  border: 1px solid rgba(44, 65, 89, 0.7);
  border-radius: 12px;
  background: rgba(12, 22, 38, 0.7);
  overflow: hidden;
}

.param-group__head {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(44, 65, 89, 0.7);
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.param-group__head h4 {
  margin: 0;
  font-size: 13px;
  color: #c8d8ee;
}

.param-group__head span {
  color: #6a84a2;
  font-size: 11px;
}

.param-table {
  display: flex;
  flex-direction: column;
}

.param-table__row {
  display: grid;
  grid-template-columns: 1fr 160px 120px;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(33, 52, 74, 0.6);
  align-items: center;
}

.param-table__row:last-child {
  border-bottom: none;
}

.param-table__row--head {
  background: rgba(20, 36, 57, 0.9);
  color: #6a84a2;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.param-table__label {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.param-table__label strong {
  color: #eef5ff;
  font-size: 13px;
}

.param-table__label small {
  color: #7a90ab;
  font-size: 12px;
  line-height: 1.5;
}

.param-table__value {
  color: #c8d8ee;
  font-size: 13px;
  line-height: 1.5;
}

.param-table__meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.param-table__meta span {
  color: #8ca0ba;
  font-size: 12px;
}

.param-table__meta small {
  color: #5d7699;
  font-size: 11px;
}

@media (max-width: 800px) {
  .readonly-summary-grid,
  .readonly-detail-actions,
  .summary-strip,
  .capacity-expansion-grid {
    grid-template-columns: 1fr;
  }

  .param-table__row {
    grid-template-columns: minmax(0, 1fr) 120px;
  }

  .param-table__meta-col {
    display: none;
  }
}
</style>
