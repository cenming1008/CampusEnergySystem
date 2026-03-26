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
  border-radius: 12px;
  padding: 16px 14px;
  border: 1px solid #243244;
  background: #131d2b;
}

.stat-tile::after {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  border-radius: 12px 0 0 12px;
  background: currentColor;
  opacity: 0.75;
}

.stat-tile__value {
  font-size: 30px;
  line-height: 1;
  font-weight: 700;
  font-family: 'DIN', 'Monaco', monospace;
  color: currentColor;
}

.stat-tile__value--compact {
  font-size: 24px;
  line-height: 1.2;
}

.stat-tile__label {
  margin-top: 8px;
  font-size: 13px;
  color: #d8e2ef;
}

.stat-tile__caption {
  margin-top: 6px;
  font-size: 11px;
  line-height: 1.4;
  color: #8ea0bc;
}

.cyan { color: #38bdf8; }
.green { color: #22c55e; }
.red { color: #ef4444; }
.purple { color: #a78bfa; }
.blue { color: #60a5fa; }
</style>
