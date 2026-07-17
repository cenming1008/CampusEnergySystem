<script setup lang="ts">
import type {
  StorageDispatchGenerationResult,
  StorageEnergyOverview,
} from '@/api/storageEnergy'

defineProps<{
  overview: StorageEnergyOverview | null
  refreshing: boolean
  generating: boolean
  generationResult: StorageDispatchGenerationResult | null
  generationError: string | null
  canGeneratePlan: boolean
}>()

defineEmits<{
  generate: [deviceId: number]
  refresh: []
}>()

function value(input: string | number | null | undefined): string {
  return input == null || input === '' ? '--' : String(input)
}

function percentage(input: number | null | undefined): string {
  return input == null ? '--' : `${input.toFixed(1)}%`
}
</script>

<template>
  <section
    class="storage-panel"
    aria-labelledby="dispatch-title"
  >
    <div class="storage-panel__heading">
      <div>
        <p class="storage-eyebrow">
          DISPATCH
        </p>
        <h3 id="dispatch-title">
          当前调度
        </h3>
      </div>
      <button
        type="button"
        :disabled="refreshing"
        @click="$emit('refresh')"
      >
        刷新
      </button>
    </div>
    <dl>
      <div><dt>计划状态</dt><dd>{{ value(overview?.dispatch.plan_status) }}</dd></div>
      <div><dt>策略</dt><dd>{{ value(overview?.dispatch.strategy) }}</dd></div>
      <div><dt>求解状态</dt><dd>{{ value(overview?.dispatch.solver_status) }}</dd></div>
      <div><dt>真实执行率</dt><dd>{{ percentage(overview?.plan_execution_rate) }}</dd></div>
      <div><dt>时段</dt><dd>{{ value(overview?.dispatch.slot_index) }}</dd></div>
      <div><dt>输入时差</dt><dd>{{ overview?.provenance.time_skew_seconds == null ? '--' : `${overview.provenance.time_skew_seconds.toFixed(1)} s` }}</dd></div>
    </dl>
    <p
      v-if="overview?.dispatch.fallback_reason"
      class="storage-panel__fallback"
    >
      回退原因：{{ overview.dispatch.fallback_reason }}
    </p>
    <p
      v-if="overview?.provenance.is_stale"
      class="storage-panel__warning"
    >
      输入数据已过期，不应视为实时控制依据。
    </p>
    <div
      v-if="generationResult"
      class="storage-panel__generation-result"
    >
      <span>生成返回状态：{{ value(generationResult.status) }}</span>
      <span>求解器：{{ value(generationResult.solver_status) }}</span>
    </div>
    <p
      v-if="generationError"
      class="storage-panel__warning"
      role="alert"
    >
      计划生成失败：{{ generationError }}
    </p>
    <p
      v-if="!canGeneratePlan"
      class="storage-panel__readonly"
    >
      当前账号仅可查看，不能生成调度计划。
    </p>
    <button
      class="storage-panel__primary"
      data-testid="generate-storage-plan"
      type="button"
      :disabled="generating || !canGeneratePlan || !overview?.storage_device_ids.length"
      @click="overview?.storage_device_ids[0] != null && $emit('generate', overview.storage_device_ids[0])"
    >
      生成今日计划
    </button>
  </section>
</template>

<style scoped>
.storage-panel { padding: 18px; border-top: 1px solid var(--em-border); background: rgba(255,255,255,.018); }
.storage-panel__heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.storage-eyebrow { margin: 0; font-size: 9px; letter-spacing: .12em; color: var(--em-subtle); }
h3 { margin: 3px 0 0; color: var(--em-text); font-size: 15px; }
button { padding: 7px 11px; border: 1px solid var(--em-border); border-radius: 8px; background: rgba(255,255,255,.04); color: var(--em-muted); cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .45; }
dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 16px; margin: 18px 0; }
dl div { min-width: 0; }
dt { color: var(--em-subtle); font-size: 11px; }
dd { margin: 3px 0 0; overflow-wrap: anywhere; color: var(--em-text); font-size: 13px; }
.storage-panel__fallback, .storage-panel__warning { margin: 0 0 12px; padding: 9px 10px; border-left: 2px solid var(--em-amber); background: rgba(248,196,113,.07); color: var(--em-amber); font-size: 12px; line-height: 1.5; }
.storage-panel__warning { border-color: var(--em-coral); color: var(--em-coral); }
.storage-panel__generation-result { display: flex; justify-content: space-between; gap: 12px; margin: 0 0 12px; color: var(--em-muted); font-size: 12px; }
.storage-panel__readonly { margin: 0 0 12px; color: var(--em-subtle); font-size: 12px; }
.storage-panel__primary { width: 100%; border-color: rgba(94,234,212,.28); color: var(--em-cyan); }
</style>
