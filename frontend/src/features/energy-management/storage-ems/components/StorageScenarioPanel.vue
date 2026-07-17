<script setup lang="ts">
import type { StorageScenarioKey } from '@/api/storageEnergy'

defineProps<{
  scenario: StorageScenarioKey
  seed: number
  initialSoc: number
  loading: boolean
}>()

const emit = defineEmits<{
  'update:scenario': [value: StorageScenarioKey]
  'update:seed': [value: number]
  'update:initialSoc': [value: number]
  compare: []
}>()

const scenarios: Array<{ value: StorageScenarioKey; label: string }> = [
  { value: 'sunny_workday', label: '晴天工作日' },
  { value: 'cloudy_workday', label: '阴天工作日' },
  { value: 'weekend_low_load', label: '周末低负荷' },
  { value: 'pv_surplus', label: '光伏富余' },
  { value: 'evening_peak', label: '晚高峰' },
]

function numberValue(event: Event): number {
  return Number((event.target as HTMLInputElement).value)
}
</script>

<template>
  <section
    class="storage-panel"
    aria-labelledby="scenario-title"
  >
    <div>
      <p class="storage-eyebrow">
        REPLAY INPUT
      </p>
      <h3 id="scenario-title">
        策略重放场景
      </h3>
    </div>
    <label>
      <span>场景</span>
      <select
        :value="scenario"
        @change="emit('update:scenario', ($event.target as HTMLSelectElement).value as StorageScenarioKey)"
      >
        <option
          v-for="item in scenarios"
          :key="item.value"
          :value="item.value"
        >{{ item.label }}</option>
      </select>
    </label>
    <div class="storage-panel__fields">
      <label>
        <span>固定种子</span>
        <input
          type="number"
          :value="seed"
          @input="emit('update:seed', numberValue($event))"
        >
      </label>
      <label>
        <span>初始 SOC (%)</span>
        <input
          type="number"
          min="0"
          max="100"
          :value="initialSoc"
          @input="emit('update:initialSoc', numberValue($event))"
        >
      </label>
    </div>
    <button
      type="button"
      :disabled="loading"
      @click="emit('compare')"
    >
      比较三种策略
    </button>
  </section>
</template>

<style scoped>
.storage-panel { padding: 18px; border-top: 1px solid var(--em-border); background: rgba(255,255,255,.018); }
.storage-eyebrow { margin: 0; font-size: 9px; letter-spacing: .12em; color: var(--em-subtle); }
h3 { margin: 3px 0 18px; color: var(--em-text); font-size: 15px; }
label { display: grid; gap: 6px; color: var(--em-muted); font-size: 11px; }
.storage-panel__fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 10px; }
select, input { width: 100%; min-height: 36px; box-sizing: border-box; border: 1px solid var(--em-border); border-radius: 8px; background: rgba(8,14,21,.8); color: var(--em-text); padding: 0 10px; }
button { width: 100%; margin-top: 16px; padding: 9px 12px; border: 1px solid rgba(94,234,212,.28); border-radius: 8px; background: rgba(94,234,212,.08); color: var(--em-cyan); cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .45; }
</style>
