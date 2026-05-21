<script setup lang="ts">
import type { PropType } from 'vue'
import type {
  CompensationCapacitorBankControlProfile,
  CompensationCapacitorBankTelemetry,
} from '@/api/compensation'
import HarmonicSpectrumPanel from '../HarmonicSpectrumPanel.vue'
import CurveKpiStrip from './CurveKpiStrip.vue'
import CompensationMetricGrid from './CompensationMetricGrid.vue'

defineProps({
  telemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
  history: {
    type: Array as PropType<CompensationCapacitorBankTelemetry[]>,
    default: () => [],
  },
  controlProfile: {
    type: Object as PropType<CompensationCapacitorBankControlProfile | null>,
    default: null,
  },
})
</script>

<template>
  <div class="curve-workspace">
    <CurveKpiStrip :telemetry="telemetry" :history="history" />

    <HarmonicSpectrumPanel
      :telemetry="telemetry"
      :control-profile="controlProfile"
    />

    <CompensationMetricGrid :telemetry="telemetry" :history="history" />
  </div>
</template>

<style scoped>
.curve-workspace {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}
</style>
