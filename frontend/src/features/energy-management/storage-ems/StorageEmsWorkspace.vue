<script setup lang="ts">
import { onMounted } from 'vue'
import StorageDispatchPanel from './components/StorageDispatchPanel.vue'
import StorageEnergyFlow from './components/StorageEnergyFlow.vue'
import StoragePowerTrend from './components/StoragePowerTrend.vue'
import StorageScenarioPanel from './components/StorageScenarioPanel.vue'
import StorageStrategyComparison from './components/StorageStrategyComparison.vue'
import { useStorageEms } from './composables/useStorageEms'

defineOptions({ name: 'StorageEmsWorkspace' })

withDefaults(defineProps<{
  canGeneratePlan?: boolean
}>(), {
  canGeneratePlan: false,
})

const {
  scenario,
  seed,
  initialSoc,
  overview,
  comparison,
  generationResult,
  error,
  overviewLoading,
  comparisonLoading,
  generationLoading,
  generationError,
  refresh,
  generatePlan,
  compareStrategies,
} = useStorageEms()

onMounted(async () => {
  const refreshed = await refresh()
  if (refreshed && overview.value?.storage_device_ids.length) {
    await compareStrategies()
  }
})

function sourceLabel(source?: string | null): string {
  if (source === 'simulated') return '仿真数据'
  if (source === 'real') return '真实设备'
  return '--'
}
</script>

<template>
  <section
    class="storage-ems"
    data-testid="storage-ems-workspace"
    aria-label="光储 EMS 工作区"
  >
    <div class="storage-ems__statusbar">
      <div>
        <strong>光储 EMS</strong>
        <span>园区级实时能流、调度证据与同输入策略重放</span>
      </div>
      <span
        class="storage-ems__source"
        :data-source="overview?.data_source || 'unknown'"
      >
        {{ sourceLabel(overview?.data_source) }}
      </span>
    </div>

    <p
      v-if="error"
      class="storage-ems__error"
      role="alert"
    >
      {{ error }}
    </p>

    <StorageEnergyFlow :current="overview?.current ?? null" />
    <StoragePowerTrend
      :current="overview?.current ?? null"
      :dispatch="overview?.dispatch ?? null"
    />

    <div class="storage-ems__controls">
      <StorageDispatchPanel
        :overview="overview"
        :refreshing="overviewLoading"
        :generating="generationLoading"
        :generation-result="generationResult"
        :generation-error="generationError"
        :can-generate-plan="canGeneratePlan"
        @refresh="refresh"
        @generate="generatePlan"
      />
      <StorageScenarioPanel
        v-model:scenario="scenario"
        v-model:seed="seed"
        v-model:initial-soc="initialSoc"
        :loading="comparisonLoading"
        @compare="compareStrategies"
      />
    </div>

    <StorageStrategyComparison :comparison="comparison" />
  </section>
</template>

<style scoped>
.storage-ems { position: relative; z-index: 1; display: grid; gap: 12px; }
.storage-ems__statusbar { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 4px 2px; }
.storage-ems__statusbar > div { display: flex; align-items: baseline; gap: 12px; }
.storage-ems__statusbar strong { color: var(--em-text); font-size: 16px; }
.storage-ems__statusbar span { color: var(--em-muted); font-size: 12px; }
.storage-ems__source { flex: none; padding: 5px 10px; border: 1px solid var(--em-border); border-radius: 999px; }
.storage-ems__source[data-source='simulated'] { border-color: rgba(248,196,113,.32); background: rgba(248,196,113,.08); color: var(--em-amber); }
.storage-ems__source[data-source='real'] { border-color: rgba(94,234,212,.3); background: rgba(94,234,212,.08); color: var(--em-cyan); }
.storage-ems__error { margin: 0; padding: 10px 12px; border-left: 2px solid var(--em-coral); background: rgba(251,113,133,.07); color: var(--em-coral); font-size: 12px; }
.storage-ems__controls { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(280px, .85fr); overflow: hidden; border: 1px solid var(--em-border); border-radius: 14px; }
.storage-ems__controls > :first-child { border-right: 1px solid var(--em-border); }
@media (max-width: 860px) {
  .storage-ems__statusbar, .storage-ems__statusbar > div { align-items: flex-start; flex-direction: column; }
  .storage-ems__controls { grid-template-columns: 1fr; }
  .storage-ems__controls > :first-child { border-right: 0; }
}
</style>
