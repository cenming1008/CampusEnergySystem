<script setup lang="ts">
defineProps<{
  tone?: 'cyan' | 'green' | 'red' | 'purple' | 'blue'
  label: string
  value: string | number
  caption?: string
}>()
</script>

<template>
  <div class="stat-tile" :class="tone || 'cyan'">
    <div class="stat-tile__value">{{ value }}</div>
    <div class="stat-tile__label">{{ label }}</div>
    <div v-if="caption" class="stat-tile__caption">{{ caption }}</div>
  </div>
</template>

<style scoped>
.stat-tile {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  padding: 18px 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02)),
    rgba(8, 17, 34, 0.88);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}

.stat-tile::after {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  border-radius: 16px 0 0 16px;
  background: currentColor;
  opacity: 0.85;
}

.stat-tile__value {
  font-size: 32px;
  line-height: 1;
  font-weight: 700;
  font-family: 'DIN', 'Monaco', monospace;
  color: currentColor;
}

.stat-tile__label {
  margin-top: 10px;
  font-size: 13px;
  color: rgba(226, 232, 240, 0.92);
}

.stat-tile__caption {
  margin-top: 6px;
  font-size: 11px;
  color: #7f8ea7;
}

.cyan { color: #00f2fe; }
.green { color: #10b981; }
.red { color: #ef4444; }
.purple { color: #a78bfa; }
.blue { color: #4facfe; }
</style>
