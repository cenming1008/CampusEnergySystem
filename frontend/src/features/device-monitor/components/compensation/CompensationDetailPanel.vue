<script setup lang="ts">
import { computed, type PropType } from 'vue'
import type {
  CompensationCapacitorBankTelemetry,
  CompensationSvgTelemetry,
} from '@/api/compensation'
import CompensationThreePhasePanel from './CompensationThreePhasePanel.vue'
import CompensationCircuitStatePanel from './CompensationCircuitStatePanel.vue'

export type CompensationDetailTab = 'three-phase' | 'circuit'

export interface CompensationCircuitProfileView {
  splitCircuitCount?: number
  commonCircuitCount?: number
  phaseACircuitTotalCount?: number
  phaseBCircuitTotalCount?: number
  phaseCCircuitTotalCount?: number
  common1CircuitTotalCount?: number
  common2CircuitTotalCount?: number
  common3CircuitTotalCount?: number
}

const props = defineProps({
  svgTelemetry: {
    type: Object as PropType<CompensationSvgTelemetry | null>,
    default: null,
  },
  capacitorBankTelemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
  isCapacitorBank: {
    type: Boolean,
    default: false,
  },
  circuitProfile: {
    type: Object as PropType<CompensationCircuitProfileView | null>,
    default: null,
  },
  activeTab: {
    type: String as PropType<CompensationDetailTab>,
    default: 'three-phase',
  },
})

const emit = defineEmits<{
  (event: 'update:activeTab', value: CompensationDetailTab): void
}>()

const showCircuitTab = computed(() => props.isCapacitorBank)

const segmentedOptions = computed(() => {
  const options: Array<{ label: string; value: CompensationDetailTab }> = [
    { label: '三相量测', value: 'three-phase' },
  ]
  if (showCircuitTab.value) {
    options.push({ label: '回路状态', value: 'circuit' })
  }
  return options
})

const resolvedTab = computed<CompensationDetailTab>(() =>
  showCircuitTab.value ? props.activeTab : 'three-phase',
)
</script>

<template>
  <section class="detail-panel">
    <header class="detail-panel__head">
      <div class="detail-panel__intro">
        <h3>实时详查</h3>
        <span>三相电气量与回路投切状态</span>
      </div>
      <div
        v-if="showCircuitTab"
        class="detail-panel__tab-switcher"
      >
        <el-segmented
          :model-value="resolvedTab"
          :options="segmentedOptions"
          size="small"
          @change="emit('update:activeTab', $event as CompensationDetailTab)"
        />
      </div>
    </header>

    <div class="detail-panel__body">
      <CompensationThreePhasePanel
        v-show="resolvedTab === 'three-phase'"
        :svg-telemetry="svgTelemetry"
        :capacitor-bank-telemetry="capacitorBankTelemetry"
        :is-capacitor-bank="isCapacitorBank"
      />

      <CompensationCircuitStatePanel
        v-if="showCircuitTab"
        v-show="resolvedTab === 'circuit'"
        :capacitor-bank-telemetry="capacitorBankTelemetry"
        :configured-split-circuit-count="circuitProfile?.splitCircuitCount"
        :configured-common-circuit-count="circuitProfile?.commonCircuitCount"
        :phase-a-circuit-total-count="circuitProfile?.phaseACircuitTotalCount"
        :phase-b-circuit-total-count="circuitProfile?.phaseBCircuitTotalCount"
        :phase-c-circuit-total-count="circuitProfile?.phaseCCircuitTotalCount"
        :common1-circuit-total-count="circuitProfile?.common1CircuitTotalCount"
        :common2-circuit-total-count="circuitProfile?.common2CircuitTotalCount"
        :common3-circuit-total-count="circuitProfile?.common3CircuitTotalCount"
      />
    </div>
  </section>
</template>

<style scoped>
.detail-panel {
  padding: 18px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-panel__head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.detail-panel__intro {
  min-width: 0;
}

.detail-panel__intro h3 {
  margin: 0;
  font-size: 16px;
  color: #f5f7fb;
}

.detail-panel__intro span {
  display: block;
  margin-top: 5px;
  font-size: var(--font-caption);
  color: var(--text-label);
}

.detail-panel__tab-switcher {
  flex: 0 1 auto;
  min-width: 0;
}

.detail-panel__tab-switcher :deep(.el-segmented) {
  white-space: nowrap;
  min-width: max-content;
  --el-segmented-bg-color: rgba(7, 15, 26, 0.7);
  --el-segmented-item-selected-bg-color: rgba(59, 130, 246, 0.28);
  --el-segmented-item-selected-color: #eaf4ff;
  --el-segmented-item-hover-bg-color: rgba(96, 165, 250, 0.16);
  --el-segmented-item-hover-color: #dbeafe;
  border: 1px solid rgba(72, 96, 130, 0.72);
  border-radius: 8px;
  padding: 2px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.detail-panel__tab-switcher :deep(.el-segmented__item) {
  color: #9fb1ca;
  border-radius: 6px;
  min-height: var(--touch-target);
}

.detail-panel__tab-switcher :deep(.el-segmented__item-selected) {
  box-shadow: 0 0 0 1px rgba(96, 165, 250, 0.35);
}

.detail-panel__body {
  display: flex;
  flex-direction: column;
}

.detail-panel__body :deep(.threephase-panel),
.detail-panel__body :deep(.circuit-panel) {
  border: none;
  border-radius: 0;
  padding: 0;
  background: transparent;
  box-shadow: none;
}

/* 嵌入 DetailPanel 后避免双层标题：三相头整体隐藏；回路只隐藏 h3（保留图例） */
.detail-panel__body :deep(.threephase-panel__head) {
  display: none;
}

.detail-panel__body :deep(.circuit-panel__head > h3) {
  display: none;
}
</style>
