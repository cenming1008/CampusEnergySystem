<script setup lang="ts">
import { computed } from 'vue'
import type {
  ControlConsoleReadonlySectionView,
  ControlConsoleReadonlySummaryView,
} from '@/features/device-control/viewMapping'
import ControlConsoleParameterSection from '@/features/device-control/components/ControlConsoleParameterSection.vue'

const props = defineProps<{
  sectionView: ControlConsoleReadonlySectionView
  readonlySummaryView: ControlConsoleReadonlySummaryView
}>()

const compactSummaryItems = computed(() => props.readonlySummaryView.summaryItems.slice(0, 6))
const snapshotTimeText = computed(() => {
  const marker = '快照：'
  const value = props.sectionView.metaText || ''
  return value.includes(marker) ? value.split(marker).pop()?.trim() || '' : value
})

function capacitySlotLabel(groupLabel: string, index: number) {
  const range = groupLabel.match(/(\d+)\s*-\s*(\d+)/)
  if (range) return `${Number(range[1]) + index}路`
  const phase = groupLabel.match(/^([ABC])相/)
  if (phase) return `${phase[1]}${index + 1}`
  return `${index + 1}路`
}

function capacitySlots(item: { label: string; value: string }) {
  return item.value
    .split('/')
    .map((value) => value.trim())
    .filter(Boolean)
    .map((value, index) => ({
      key: `${item.label}-${index}`,
      label: capacitySlotLabel(item.label, index),
      value,
    }))
}
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
          <div class="capacity-slot-grid">
            <div
              v-for="slot in capacitySlots(item)"
              :key="slot.key"
              class="capacity-slot"
              data-test="capacity-slot"
            >
              <small>{{ slot.label }}</small>
              <strong>{{ slot.value }}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="param-groups">
      <div class="param-group-grid">
        <section
          v-for="group in readonlySummaryView.groupedParameters"
          :key="group.key"
          class="param-group"
          data-test="param-group-card"
        >
          <header class="param-group__head">
            <h4>{{ group.label }}</h4>
            <span>{{ group.items.length }} 个参数</span>
          </header>
          <div class="param-list">
            <div
              v-for="item in group.items"
              :key="item.key"
              class="param-list__row"
            >
              <span>{{ item.label }}</span>
              <strong>{{ item.currentValue }}</strong>
            </div>
          </div>
        </section>
      </div>
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
  gap: 10px;
}

.capacity-expansion-card span {
  color: #91a5c2;
  font-size: 11px;
}

.capacity-slot-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}

.capacity-slot {
  padding: 7px 8px;
  border-radius: 8px;
  border: 1px solid rgba(48, 70, 95, 0.62);
  background: rgba(8, 17, 30, 0.42);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.capacity-slot small {
  color: #6ddbd0;
  font-size: 11px;
  line-height: 1.3;
  white-space: nowrap;
}

.capacity-slot strong {
  color: #f7fbff;
  font-size: 12px;
  line-height: 1.35;
  text-align: right;
  overflow-wrap: anywhere;
}

.param-groups {
  margin-top: 12px;
}

.param-group-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  align-items: start;
}

.param-group {
  border: 1px solid rgba(44, 65, 89, 0.7);
  border-radius: 10px;
  background: rgba(12, 22, 38, 0.7);
  overflow: hidden;
}

.param-group__head {
  padding: 10px 14px;
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

.param-list {
  display: flex;
  flex-direction: column;
}

.param-list__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  padding: 9px 14px;
  border-bottom: 1px solid rgba(33, 52, 74, 0.6);
  align-items: center;
}

.param-list__row:last-child {
  border-bottom: none;
}

.param-list__row span {
  color: #91a5c2;
  font-size: 12px;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.param-list__row strong {
  color: #f7fbff;
  font-size: 13px;
  line-height: 1.4;
  text-align: right;
  overflow-wrap: anywhere;
}

@media (max-width: 800px) {
  .readonly-summary-grid,
  .summary-strip,
  .capacity-expansion-grid {
    grid-template-columns: 1fr;
  }

  .param-group-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .param-group-grid {
    grid-template-columns: 1fr;
  }
}
</style>
