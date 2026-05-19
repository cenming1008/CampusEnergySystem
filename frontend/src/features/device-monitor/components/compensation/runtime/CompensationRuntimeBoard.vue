<script setup lang="ts">
import { computed, ref } from 'vue'
import type { PropType } from 'vue'
import type { DeviceMonitorPageModel } from '@/features/device-monitor/composables/useDeviceMonitorPage'
import type { CompensationCircuitPick } from '../types'
import CompensationPfTrendCard from './CompensationPfTrendCard.vue'
import CompensationPqQuadrantCard from './CompensationPqQuadrantCard.vue'
import CompensationHealthCard from './CompensationHealthCard.vue'
import CompensationBankTopology from './CompensationBankTopology.vue'
import CompensationPhaseMatrix from './CompensationPhaseMatrix.vue'
import CompensationCircuitDrawer from './CompensationCircuitDrawer.vue'
import CompensationThreePhasePanel from '../CompensationThreePhasePanel.vue'
import CompensationModeToggle from './CompensationModeToggle.vue'

const props = defineProps({
  page: {
    type: Object as PropType<DeviceMonitorPageModel>,
    required: true,
  },
})

const pickedCircuit = ref<CompensationCircuitPick | null>(null)

const modeSwitchCard = computed(() =>
  props.page.controlConsoleActionCards.find((card) => card.key === 'switch_control_mode'),
)
const controlMode = computed<'auto' | 'manual' | 'unknown'>(() => {
  const label = props.page.controlConsoleCurrentControlModeLabel || ''
  if (label.includes('自动')) return 'auto'
  if (label.includes('手动')) return 'manual'
  return 'unknown'
})

const RANGE_MS: Record<'10m' | '1h' | '24h', number> = {
  '10m': 10 * 60 * 1000,
  '1h': 60 * 60 * 1000,
  '24h': 24 * 60 * 60 * 1000,
}

const timeRangeKey = computed<'10m' | '1h' | '24h'>(() => {
  const range = props.page.timeRange
  if (!range) return '1h'
  const span = range[1].getTime() - range[0].getTime()
  if (span <= RANGE_MS['10m'] * 1.5) return '10m'
  if (span >= RANGE_MS['24h'] * 0.75) return '24h'
  return '1h'
})

function handleRangeChange(key: '10m' | '1h' | '24h') {
  const now = new Date()
  props.page.timeRange = [new Date(now.getTime() - RANGE_MS[key]), now]
  void props.page.handleRangeChange()
}

const circuitEvents = computed(() => {
  if (!pickedCircuit.value) return []
  const phaseToken = pickedCircuit.value.phase === 'COMMON' ? '公补' : `${pickedCircuit.value.phase} 相`
  return props.page.compensationEvents.filter(
    (ev) => !ev.isMock && (ev.title.includes(phaseToken) || ev.detail.includes(phaseToken)),
  )
})

function handleCircuitSwitch(payload: {
  phase: 'A' | 'B' | 'C' | 'COMMON'
  commonGroup: 1 | 2 | 3 | null
  action: 'on' | 'off'
}) {
  if (!props.page.controlConsoleCanRunManualSwitch) return
  props.page.controlConsoleManualSwitchForm.phase = payload.phase
  props.page.controlConsoleManualSwitchForm.switch_action = payload.action
  if (payload.phase === 'COMMON' && payload.commonGroup) {
    props.page.controlConsoleManualSwitchForm.group = payload.commonGroup
  }
  void props.page.handleControlConsoleManualSwitchCommand()
  pickedCircuit.value = null
}
</script>

<template>
  <div class="runtime-board">
    <div class="rt-hero">
      <CompensationPfTrendCard
        :pf="page.realtime?.power_factor ?? null"
        :p="page.compensationPqPoint.p"
        :q="page.compensationPqPoint.q"
        :pf-trend="page.compensationPowerFactorTrend"
        :time-range-key="timeRangeKey"
        @range-change="handleRangeChange"
      />
      <CompensationPqQuadrantCard
        :point="page.compensationPqPoint"
        :history="page.compensationPqHistory"
      />
      <CompensationHealthCard :model="page.compensationHealthModel" />
    </div>

    <div class="rt-topology">
      <CompensationBankTopology
        :telemetry="page.compensationCapacitorBankTelemetry"
        :circuit-profile="page.compensationCircuitProfile"
        @pick="pickedCircuit = $event"
      >
        <template #header-actions>
          <CompensationModeToggle
            :mode="controlMode"
            :disabled="!modeSwitchCard || !modeSwitchCard.enabled"
            :disabled-reason="modeSwitchCard?.disabledReason || '远程控制当前不可用'"
            :submitting="page.controlConsoleToggleSubmitting"
            @switch="page.handleControlConsoleActionCard('switch_control_mode')"
          />
        </template>
      </CompensationBankTopology>
    </div>

    <div class="rt-bottom">
      <CompensationPhaseMatrix :telemetry="page.compensationCapacitorBankTelemetry" />
      <CompensationThreePhasePanel
        :capacitor-bank-telemetry="page.compensationCapacitorBankTelemetry"
        :is-capacitor-bank="true"
        :measurement-metrics="page.compensationMeasurementMetrics"
      />
    </div>

    <CompensationCircuitDrawer
      v-if="pickedCircuit"
      :circuit="pickedCircuit"
      :can-control="page.controlConsoleCanRunManualSwitch && !page.isPendingArchiveDevice"
      :events="circuitEvents"
      @close="pickedCircuit = null"
      @switch="handleCircuitSwitch"
    />
  </div>
</template>

<style scoped>
.runtime-board {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}
.rt-hero {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1fr;
  gap: 12px;
}
.rt-hero > * {
  min-height: 244px;
  min-width: 0;
}
.rt-bottom {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  align-items: start;
}
.rt-bottom > * {
  min-width: 0;
}
@media (max-width: 1280px) {
  .rt-hero {
    grid-template-columns: 1fr;
  }
  .rt-bottom {
    grid-template-columns: 1fr;
  }
}
</style>
