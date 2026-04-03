<script setup lang="ts">
defineProps<{
  tone?: 'cyan' | 'green' | 'red' | 'purple' | 'blue'
  label: string
  value: string | number
  caption?: string
}>()
</script>

<template>
  <div
    class="stat-tile"
    :class="tone || 'cyan'"
  >
    <div
      class="stat-tile__value"
      :class="{ 'stat-tile__value--compact': String(value).length > 8 }"
    >
      {{ value }}
    </div>
    <div class="stat-tile__label">
      {{ label }}
    </div>
    <div
      v-if="caption"
      class="stat-tile__caption"
    >
      {{ caption }}
    </div>
  </div>
</template>

<style scoped>
.stat-tile {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
  padding: 22px 18px;
  border: 1px solid var(--dashboard-card-border, rgba(255, 255, 255, 0.06));
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.02) 46%, rgba(255, 255, 255, 0)),
    var(--dashboard-card-bg, #131d2b);
  box-shadow: var(--dashboard-card-shadow, 0 16px 34px rgba(3, 8, 18, 0.12));
  backdrop-filter: blur(24px) saturate(155%);
}

.stat-tile::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.02) 34%, transparent 58%);
  pointer-events: none;
}

.stat-tile::after {
  content: '';
  position: absolute;
  top: 16px;
  left: 18px;
  width: 28px;
  height: 2px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.78;
}

.stat-tile__value {
  margin-top: 10px;
  font-size: 34px;
  line-height: 0.95;
  font-weight: 650;
  font-family: 'DIN', 'Monaco', monospace;
  color: currentColor;
}

.stat-tile__value--compact {
  font-size: 24px;
  line-height: 1.2;
}

.stat-tile__label {
  margin-top: 14px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--dashboard-card-label, #d8e2ef);
}

.stat-tile__caption {
  margin-top: 8px;
  font-size: 11px;
  line-height: 1.6;
  color: var(--dashboard-card-caption, #8ea0bc);
}

.cyan { color: var(--dashboard-accent-cyan, #38bdf8); }
.green { color: var(--dashboard-accent-green, #22c55e); }
.red { color: var(--dashboard-accent-red, #ef4444); }
.purple { color: var(--dashboard-accent-purple, #a78bfa); }
.blue { color: var(--dashboard-accent-blue, #60a5fa); }
</style>
