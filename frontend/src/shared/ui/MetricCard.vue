<script setup lang="ts">
defineProps<{
  accent?: 'cyan' | 'green' | 'pink' | 'purple' | 'blue'
  icon: string
  label: string
  value: string | number
  unit?: string
  badge?: string
  progress?: number
}>()
</script>

<template>
  <div class="metric-card" :class="accent || 'cyan'">
    <div class="metric-card__bg"></div>
    <div class="metric-card__content">
      <div class="metric-card__icon">{{ icon }}</div>
      <div class="metric-card__info">
        <div class="metric-card__label">
          <span>{{ label }}</span>
          <span v-if="badge" class="metric-card__badge">{{ badge }}</span>
        </div>
        <div class="metric-card__value">
          {{ value }}
          <small v-if="unit">{{ unit }}</small>
        </div>
      </div>
    </div>
    <div v-if="progress !== undefined" class="metric-card__bar">
      <div class="metric-card__bar-fill" :style="{ width: `${Math.max(0, Math.min(progress, 100))}%` }"></div>
    </div>
  </div>
</template>

<style scoped>
.metric-card {
  position: relative;
  overflow: hidden;
  border-radius: 18px;
  background: rgba(8, 17, 34, 0.84);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 16px 40px rgba(1, 9, 24, 0.24);
  transition: transform 0.25s ease, border-color 0.25s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
}

.metric-card__bg {
  position: absolute;
  inset: 0;
  opacity: 0.16;
}

.metric-card__content {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
}

.metric-card__icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  background: rgba(255,255,255,0.08);
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
  color: #9ba9c4;
}

.metric-card__badge {
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 10px;
  color: inherit;
  background: rgba(255,255,255,0.1);
}

.metric-card__value {
  margin-top: 6px;
  font-size: 28px;
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

.metric-card__bar {
  height: 4px;
  background: rgba(255,255,255,0.08);
}

.metric-card__bar-fill {
  height: 100%;
  background: linear-gradient(90deg, currentColor, rgba(255,255,255,0.9));
  transition: width 0.45s ease;
}

.cyan {
  color: #00f2fe;
  border-color: rgba(0,242,254,0.28);
}

.cyan .metric-card__bg {
  background: linear-gradient(135deg, rgba(0,242,254,0.65), transparent 65%);
}

.green {
  color: #10b981;
  border-color: rgba(16,185,129,0.28);
}

.green .metric-card__bg {
  background: linear-gradient(135deg, rgba(16,185,129,0.65), transparent 65%);
}

.pink {
  color: #f093fb;
  border-color: rgba(240,147,251,0.28);
}

.pink .metric-card__bg {
  background: linear-gradient(135deg, rgba(240,147,251,0.65), transparent 65%);
}

.purple {
  color: #a78bfa;
  border-color: rgba(167,139,250,0.28);
}

.purple .metric-card__bg {
  background: linear-gradient(135deg, rgba(167,139,250,0.65), transparent 65%);
}

.blue {
  color: #4facfe;
  border-color: rgba(79,172,254,0.28);
}

.blue .metric-card__bg {
  background: linear-gradient(135deg, rgba(79,172,254,0.65), transparent 65%);
}
</style>
