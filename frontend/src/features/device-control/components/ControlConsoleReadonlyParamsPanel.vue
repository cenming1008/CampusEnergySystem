<script setup lang="ts">
import type {
  ControlConsoleReadonlySectionView,
  ControlConsoleReadonlySummaryView,
} from '@/features/device-control/viewMapping'
import ControlConsoleParameterSection from '@/features/device-control/components/ControlConsoleParameterSection.vue'

defineProps<{
  sectionView: ControlConsoleReadonlySectionView
  readonlySummaryView: ControlConsoleReadonlySummaryView
}>()
</script>

<template>
  <ControlConsoleParameterSection
    :title="sectionView.title"
    :section-label="sectionView.sectionLabel"
    :tone="sectionView.tone"
    :tags="sectionView.tags"
    :meta-text="sectionView.metaText"
  >
    <div
      v-if="sectionView.showCapacityExpansion"
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
    <div class="param-groups">
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

.capacity-expansion-panel {
  margin-bottom: 16px;
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
