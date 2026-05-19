<script setup lang="ts">
import type { PropType } from 'vue'
import type { CompensationHealthModel } from '../types'

defineProps({
  model: {
    type: Object as PropType<CompensationHealthModel>,
    required: true,
  },
})

function barColor(value: number): string {
  if (value >= 90) return '#34d399'
  if (value >= 70) return '#22d3ee'
  if (value >= 50) return '#f59e0b'
  return '#ef4444'
}
</script>

<template>
  <section class="health-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />设备健康度</span>
      <span class="health-tag">实时计算</span>
    </header>

    <div v-if="model.score === null" class="health-empty">暂无健康度数据</div>

    <div v-else class="health-body">
      <div class="health-score">
        <strong class="health-score-val">{{ model.score }}</strong>
        <span class="health-score-max">/100</span>
      </div>
      <div class="health-rating">
        状态评级 · <span :class="`tone-${model.ratingTone}`">{{ model.rating }}</span>
      </div>
      <div class="health-bars">
        <div
          v-for="dim in model.breakdown"
          :key="dim.key"
          class="health-bar"
          data-test="health-bar"
        >
          <span class="health-bar-lbl">{{ dim.label }}</span>
          <div class="health-bar-track">
            <div
              v-if="dim.value !== null"
              class="health-bar-fill"
              :style="{ width: `${dim.value}%`, background: barColor(dim.value) }"
            />
          </div>
          <span
            class="health-bar-val"
            :style="{ color: dim.value !== null ? barColor(dim.value) : '#5e6c83' }"
          >{{ dim.value === null ? '待采集' : dim.value }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.health-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  min-height: 0;
}
.rt-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rt-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
}
.rt-accent {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #22d3ee;
}
.health-tag {
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 10px;
  color: #67e8f9;
  border: 1px solid rgba(34, 211, 238, 0.4);
  background: rgba(34, 211, 238, 0.08);
}
.health-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9aa7bd;
  font-size: 12px;
}
.health-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 14px;
  flex: 1;
  min-height: 0;
}
.health-score {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.health-score-val {
  font-size: 40px;
  font-weight: 300;
  line-height: 0.95;
  color: #67e8f9;
  font-variant-numeric: tabular-nums;
}
.health-score-max {
  color: #5e6c83;
}
.health-rating {
  font-size: 11px;
  color: #5e6c83;
}
.tone-success { color: #34d399; }
.tone-warning { color: #f59e0b; }
.tone-danger { color: #ef4444; }
.tone-info,
.tone-neutral { color: #67e8f9; }
.health-bars {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 1;
  justify-content: center;
}
.health-bar {
  display: grid;
  grid-template-columns: 64px 1fr 40px;
  gap: 8px;
  align-items: center;
}
.health-bar-lbl {
  font-size: 10px;
  color: #9aa7bd;
}
.health-bar-track {
  height: 5px;
  background: #0b1623;
  border: 1px solid #1f2c41;
  border-radius: 3px;
  overflow: hidden;
}
.health-bar-fill {
  height: 100%;
  border-radius: 2px;
}
.health-bar-val {
  font-size: 10px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
</style>
