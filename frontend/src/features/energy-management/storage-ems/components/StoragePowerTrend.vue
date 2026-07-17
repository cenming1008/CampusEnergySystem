<script setup lang="ts">
import type { StorageEnergyCurrent, StorageDispatchOverview } from '@/api/storageEnergy'

const props = defineProps<{
  current: StorageEnergyCurrent | null
  dispatch: StorageDispatchOverview | null
}>()

function metric(value: number | null | undefined, unit: string): string {
  return value == null ? '--' : `${value.toFixed(1)} ${unit}`
}

function barWidth(value: number | null | undefined): string {
  if (value == null) return '0%'
  const denominator = Math.max(
    Math.abs(props.dispatch?.target_power_kw ?? 0),
    Math.abs(props.dispatch?.actual_power_kw ?? 0),
    1,
  )
  return `${Math.min(100, Math.abs(value) / denominator * 100)}%`
}
</script>

<template>
  <section
    class="power-trend"
    aria-labelledby="power-trend-title"
  >
    <div class="power-trend__heading">
      <div>
        <p class="storage-eyebrow">
          POWER / SOC
        </p>
        <h2 id="power-trend-title">
          调度功率与荷电状态
        </h2>
      </div>
      <strong>SOC {{ metric(current?.soc, '%') }}</strong>
    </div>
    <div
      class="power-trend__plot"
      aria-label="目标与实际功率对比"
    >
      <div class="power-row">
        <span>目标功率</span>
        <div class="power-track">
          <i
            class="power-bar power-bar--target"
            :style="{ width: barWidth(dispatch?.target_power_kw) }"
          />
        </div>
        <strong>{{ metric(dispatch?.target_power_kw, 'kW') }}</strong>
      </div>
      <div class="power-row">
        <span>实际功率</span>
        <div class="power-track">
          <i
            class="power-bar power-bar--actual"
            :style="{ width: barWidth(dispatch?.actual_power_kw) }"
          />
        </div>
        <strong>{{ metric(dispatch?.actual_power_kw, 'kW') }}</strong>
      </div>
      <div class="power-row">
        <span>功率偏差</span>
        <div class="power-track">
          <i
            class="power-bar power-bar--deviation"
            :style="{ width: barWidth(dispatch?.deviation_kw) }"
          />
        </div>
        <strong>{{ metric(dispatch?.deviation_kw, 'kW') }}</strong>
      </div>
      <div class="soc-scale">
        <span :style="{ width: current?.soc == null ? '0%' : `${Math.min(100, Math.max(0, current.soc))}%` }" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.power-trend { min-height: 220px; padding: 22px; border: 1px solid var(--em-border); border-radius: 14px; background: rgba(11, 17, 25, .82); }
.power-trend__heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.power-trend__heading h2 { margin: 3px 0 0; font-size: 19px; color: var(--em-text); }
.power-trend__heading > strong { color: var(--em-cyan); font-size: 15px; }
.storage-eyebrow { margin: 0; font-size: 9px; letter-spacing: .12em; color: var(--em-subtle); }
.power-trend__plot { display: grid; gap: 18px; margin-top: 34px; }
.power-row { display: grid; grid-template-columns: 78px minmax(120px, 1fr) 104px; gap: 14px; align-items: center; }
.power-row > span { color: var(--em-muted); font-size: 12px; }
.power-row > strong { color: var(--em-text); font-size: 13px; text-align: right; }
.power-track { height: 8px; overflow: hidden; border-radius: 999px; background: rgba(255,255,255,.055); }
.power-bar { display: block; height: 100%; border-radius: inherit; }
.power-bar--target { background: var(--em-blue); opacity: .7; }
.power-bar--actual { background: var(--em-cyan); }
.power-bar--deviation { background: var(--em-amber); }
.soc-scale { height: 3px; margin-top: 3px; background: rgba(255,255,255,.05); }
.soc-scale span { display: block; height: 100%; background: linear-gradient(90deg, var(--em-blue), var(--em-cyan)); }
</style>
