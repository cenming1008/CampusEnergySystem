<script setup lang="ts">
defineProps<{
  accent?: 'cyan' | 'green' | 'pink' | 'purple' | 'blue'
  icon: string
  label: string
  value: string | number
  unit?: string
  badge?: string
  progress?: number
  meta?: string
}>()
</script>

<template>
  <div
    class="metric-card"
    :class="accent || 'cyan'"
  >
    <div class="metric-card__bg" />
    <div class="metric-card__content">
      <div class="metric-card__icon">
        {{ icon }}
      </div>
      <div class="metric-card__info">
        <div class="metric-card__label">
          <span>{{ label }}</span>
          <span
            v-if="badge"
            class="metric-card__badge"
          >{{ badge }}</span>
        </div>
        <div class="metric-card__value">
          {{ value }}
          <small v-if="unit">{{ unit }}</small>
        </div>
        <div
          v-if="meta"
          class="metric-card__meta"
        >
          {{ meta }}
        </div>
      </div>
    </div>
    <div
      v-if="progress !== undefined"
      class="metric-card__bar"
    >
      <div
        class="metric-card__bar-fill"
        :style="{ width: `${Math.max(0, Math.min(progress, 100))}%` }"
      />
    </div>
  </div>
</template>

<style scoped>
.metric-card {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  background: #131d2b;
  border: 1px solid #243244;
  box-shadow: none;
  transition: transform 0.25s ease, border-color 0.25s ease;
}

.metric-card:hover {
  border-color: #314055;
}

.metric-card__bg {
  position: absolute;
  inset: 0;
  opacity: 0.04;
}

.metric-card__content {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
}

.metric-card__icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: #1b2838;
}

.metric-card__info {
  flex: 1;
  min-width: 0;
}

.metric-card__label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #9aacbf;
}

.metric-card__badge {
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 10px;
  color: inherit;
  background: #1d2938;
}

.metric-card__value {
  margin-top: 6px;
  font-size: 24px;
  line-height: 1.1;
  font-weight: 700;
  color: #fff;
  font-family: 'DIN', 'Monaco', monospace;
}

.metric-card__value small {
  margin-left: 4px;
  font-size: 12px;
  color: #8ea0bc;
}

.metric-card__meta {
  margin-top: 8px;
  font-size: 11px;
  color: #8ea0bc;
}

.metric-card__bar {
  height: 3px;
  background: #1d2938;
}

.metric-card__bar-fill {
  height: 100%;
  background: linear-gradient(90deg, currentColor, rgba(255,255,255,0.9));
  transition: width 0.45s ease;
}

.cyan {
  color: #38bdf8;
  border-color: #243244;
}

.cyan .metric-card__bg {
  background: linear-gradient(135deg, rgba(56,189,248,0.5), transparent 65%);
}

.green {
  color: #22c55e;
  border-color: #243244;
}

.green .metric-card__bg {
  background: linear-gradient(135deg, rgba(34,197,94,0.45), transparent 65%);
}

.pink {
  color: #f59e0b;
  border-color: #243244;
}

.pink .metric-card__bg {
  background: linear-gradient(135deg, rgba(245,158,11,0.45), transparent 65%);
}

.purple {
  color: #a78bfa;
  border-color: #243244;
}

.purple .metric-card__bg {
  background: linear-gradient(135deg, rgba(167,139,250,0.45), transparent 65%);
}

.blue {
  color: #60a5fa;
  border-color: #243244;
}

.blue .metric-card__bg {
  background: linear-gradient(135deg, rgba(96,165,250,0.45), transparent 65%);
}
</style>
