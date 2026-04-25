<script setup lang="ts">
defineProps<{
  rankings: Array<{ name: string; score: number; online: number; total: number }>
}>()

function fmt(v: number, d = 1) {
  return Number.isFinite(v) ? v.toFixed(d) : '0.0'
}

const rankColors = ['#38bdf8', '#34d399', '#a78bfa', '#fb923c', '#f87171']
</script>

<template>
  <section class="glass-card ranking-card">
    <div class="card-head">
      <span class="card-eyebrow">Regional Ranking</span>
      <span class="card-title">区域能耗排行</span>
    </div>

    <div v-if="rankings.length" class="ranking-list">
      <article
        v-for="(item, index) in rankings"
        :key="item.name"
        class="ranking-row"
      >
        <span class="ranking-row__index" :style="{ color: rankColors[index] }">
          {{ index + 1 }}
        </span>
        <div class="ranking-row__body">
          <div class="ranking-row__top">
            <strong>{{ item.name }}</strong>
            <strong class="ranking-row__score">{{ fmt(item.score) }} kW</strong>
          </div>
          <div class="ranking-row__bar-wrap">
            <div
              class="ranking-row__bar"
              :style="{
                width: rankings[0]?.score > 0 ? `${(item.score / rankings[0].score) * 100}%` : '0%',
                background: rankColors[index]
              }"
            />
            <span class="ranking-row__sub">{{ item.online }}/{{ item.total }} 台启用</span>
          </div>
        </div>
      </article>
    </div>

    <div v-else class="ranking-empty">
      暂无区域数据
    </div>
  </section>
</template>

<style scoped>
.ranking-card {
  padding: 14px;
}

.card-head {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 10px;
}

.card-eyebrow {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: rgba(255, 255, 255, 0.38);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ranking-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.ranking-row__index {
  font-size: 15px;
  font-weight: 700;
  line-height: 1;
  margin-top: 2px;
  min-width: 16px;
  text-align: center;
  letter-spacing: -0.02em;
}

.ranking-row__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ranking-row__top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
}

.ranking-row__top strong {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.78);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ranking-row__score {
  font-size: 12px;
  font-weight: 600;
  color: #cce4ff;
  flex-shrink: 0;
}

.ranking-row__bar-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ranking-row__bar {
  height: 3px;
  border-radius: 2px;
  opacity: 0.6;
  transition: width 0.4s ease;
  flex-shrink: 0;
}

.ranking-row__sub {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.34);
  white-space: nowrap;
}

.ranking-empty {
  padding: 12px;
  text-align: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
}
</style>
