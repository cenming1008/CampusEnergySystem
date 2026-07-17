<script setup lang="ts">
import { computed } from 'vue'
import type {
  StorageStrategyComparisonResult,
  StorageStrategyMetrics,
} from '@/api/storageEnergy'

const props = defineProps<{
  comparison: StorageStrategyComparisonResult | null
}>()

const rows = computed<Array<{ key: string; label: string; metrics: StorageStrategyMetrics | null }>>(() => [
  { key: 'baseline', label: '基线策略', metrics: props.comparison?.strategies.baseline ?? null },
  { key: 'rule', label: '规则策略', metrics: props.comparison?.strategies.rule ?? null },
  { key: 'day_ahead', label: '日前策略', metrics: props.comparison?.strategies.day_ahead ?? null },
])

function number(value: number | null | undefined, digits = 1): string {
  return value == null ? '--' : value.toFixed(digits)
}

function rate(value: number | null | undefined): string {
  return value == null ? '--' : `${value.toFixed(1)}%`
}
</script>

<template>
  <section
    class="strategy-comparison"
    aria-labelledby="comparison-title"
  >
    <div class="strategy-comparison__heading">
      <div>
        <p class="storage-eyebrow">
          STRATEGY REPLAY
        </p>
        <h2 id="comparison-title">
          同输入策略对比
        </h2>
      </div>
      <p>
        求解状态 {{ comparison?.solver_status || '--' }}
        <span v-if="comparison">
          · 场景 {{ comparison.scenario_key }}
          · seed {{ comparison.seed }}
          · 初始 SOC {{ comparison.initial_soc.toFixed(1) }}%
          · 校验 {{ comparison.input_series_checksum.slice(0, 8) }}
        </span>
      </p>
    </div>
    <div class="strategy-comparison__scroll">
      <table>
        <thead>
          <tr>
            <th>策略</th>
            <th>总成本</th>
            <th>购电量</th>
            <th>峰值</th>
            <th>光伏自用率</th>
            <th>电池吞吐量</th>
            <th>终端 SOC</th>
            <th>计划执行率</th>
            <th>重放可执行率</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row.key"
            :data-strategy="row.key"
          >
            <th scope="row">
              {{ row.label }}
            </th>
            <td>{{ number(row.metrics?.cost, 2) }}</td>
            <td>{{ number(row.metrics?.grid_import_kwh) }} kWh</td>
            <td>{{ number(row.metrics?.peak_grid_kw) }} kW</td>
            <td>{{ rate(row.metrics?.pv_self_use_rate) }}</td>
            <td>{{ number(row.metrics?.throughput_kwh) }} kWh</td>
            <td>{{ rate(row.metrics?.terminal_soc) }}</td>
            <td>{{ rate(row.metrics?.plan_execution_rate) }}</td>
            <td>{{ rate(row.metrics?.feasible_slot_rate) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="strategy-comparison__note">
      重放可执行率仅表示场景重放的可行时段比例，不代表真实计划执行成功。
    </p>
  </section>
</template>

<style scoped>
.strategy-comparison { padding: 20px; border: 1px solid var(--em-border); border-radius: 14px; background: rgba(11,17,25,.78); }
.strategy-comparison__heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.storage-eyebrow { margin: 0; font-size: 9px; letter-spacing: .12em; color: var(--em-subtle); }
h2 { margin: 3px 0 0; font-size: 17px; color: var(--em-text); }
.strategy-comparison__heading > p { margin: 0; color: var(--em-muted); font-size: 11px; }
.strategy-comparison__scroll { overflow-x: auto; }
table { width: 100%; min-width: 920px; border-collapse: collapse; color: var(--em-text); font-size: 12px; }
th, td { padding: 11px 10px; border-bottom: 1px solid var(--em-border); text-align: right; white-space: nowrap; }
thead th { color: var(--em-subtle); font-weight: 500; }
th:first-child { text-align: left; }
tbody th { color: var(--em-text); font-weight: 600; }
tbody td { color: var(--em-muted); }
.strategy-comparison__note { margin: 12px 0 0; color: var(--em-subtle); font-size: 11px; }
</style>
