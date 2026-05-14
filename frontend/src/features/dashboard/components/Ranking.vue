<script setup lang="ts">
import { computed, ref } from 'vue'

export interface RankItem {
  name: string
  value: number
  deltaPct: number
  trend?: 'up' | 'down' | 'flat'
}

interface Props {
  items: RankItem[]
  unit?: string
  rangeTabs?: string[]
  /** Show a "示例数据" badge when source data isn't authoritative */
  isSample?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  unit: 'kW',
  rangeTabs: () => ['实时', '今日', '本周'],
  isSample: false
})

const activeRange = ref(0)
const items = computed(() => props.items || [])
const max = computed(() => Math.max(1, ...items.value.map(i => i.value)))

function trendOf(it: RankItem): 'up' | 'down' | 'flat' {
  if (it.trend) return it.trend
  if (it.deltaPct > 0.05) return 'up'
  if (it.deltaPct < -0.05) return 'down'
  return 'flat'
}
function trendColor(t: 'up' | 'down' | 'flat') {
  if (t === 'up') return 'var(--err)'
  if (t === 'down') return 'var(--ok)'
  return 'var(--flat)'
}
function trendArrow(t: 'up' | 'down' | 'flat') {
  if (t === 'up') return '↑'
  if (t === 'down') return '↓'
  return '–'
}
</script>

<template>
  <div class="card">
    <div class="card-head">
      <div class="title-block">
        <span class="title">能耗排行</span>
        <span v-if="isSample" class="sample mono">示例数据</span>
      </div>
      <div class="range">
        <span
          v-for="(t, i) in rangeTabs"
          :key="t"
          :class="{ active: i === activeRange }"
          @click="activeRange = i"
        >{{ t }}</span>
      </div>
    </div>
    <div v-if="items.length === 0" class="empty">暂无数据</div>
    <div v-else class="list">
      <div v-for="(it, i) in items" :key="`${it.name}-${i}`" class="row">
        <span class="rank mono" :class="{ top: i < 3 }">{{ i + 1 }}</span>
        <div class="content">
          <div class="line1">
            <span class="nm">{{ it.name }}</span>
            <div class="vals">
              <span class="dp mono" :style="{ color: trendColor(trendOf(it)) }">
                {{ trendArrow(trendOf(it)) }} {{ Math.abs(it.deltaPct).toFixed(1) }}%
              </span>
              <span class="vl mono">{{ it.value }}</span>
              <span class="un">{{ unit }}</span>
            </div>
          </div>
          <div class="bar">
            <div class="fill" :style="{ width: `${(it.value / max) * 100}%`, background: trendColor(trendOf(it)) }" />
          </div>
        </div>
      </div>
    </div>
    <div class="legend">
      <span class="lg-label">颜色 = 同比</span>
      <span class="lg-pair"><span class="lg-bar" style="background: var(--err)" /> 上升</span>
      <span class="lg-pair"><span class="lg-bar" style="background: var(--ok)" /> 下降</span>
      <span class="lg-pair"><span class="lg-bar" style="background: var(--flat)" /> 持平</span>
    </div>
  </div>
</template>

<style scoped>
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
  box-sizing: border-box;
}
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.title-block { display: flex; align-items: baseline; gap: 10px; }
.title { font-size: 13px; font-weight: 600; color: var(--text); letter-spacing: 0.2px; }
.sample { font-size: 9px; color: var(--text-dim); padding: 2px 5px; border: 1px dashed var(--border-hi); border-radius: 3px; }
.range { display: flex; gap: 4px; }
.range span {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 3px;
  color: var(--text-dim);
  cursor: pointer;
}
.range span.active { color: var(--accent); background: rgba(77, 208, 196, 0.10); }
.empty { padding: 20px 12px; font-size: 12px; color: var(--text-dim); text-align: center; }
.list { display: flex; flex-direction: column; gap: 9px; }
.row { display: flex; align-items: center; gap: 10px; }
.rank { width: 18px; font-size: 11px; text-align: center; color: var(--text-dim); }
.rank.top { color: var(--text); font-weight: 700; }
.content { flex: 1; min-width: 0; }
.line1 { display: flex; justify-content: space-between; margin-bottom: 4px; }
.nm { font-size: 12px; color: var(--text); }
.vals { display: flex; align-items: baseline; gap: 6px; }
.dp { font-size: 10px; font-weight: 600; }
.vl { font-size: 12px; color: var(--text); font-weight: 600; width: 44px; text-align: right; }
.un { font-size: 9px; color: var(--text-dim); width: 14px; }
.bar { height: 6px; background: var(--surface-hi); border-radius: 3px; overflow: hidden; }
.fill { height: 100%; border-radius: 3px; }
.legend { display: flex; gap: 12px; margin-top: 10px; font-size: 10px; color: var(--text-dim); align-items: center; }
.lg-label { letter-spacing: 0.4px; }
.lg-pair { display: flex; align-items: center; gap: 4px; }
.lg-bar { width: 8px; height: 3px; border-radius: 1px; }
</style>
