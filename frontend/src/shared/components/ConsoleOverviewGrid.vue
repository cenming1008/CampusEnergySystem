<script setup lang="ts">
defineProps<{
  items: Array<{ label: string; value: string }>
}>()
</script>

<template>
  <div class="console-overview-grid">
    <div
      v-for="item in items"
      :key="item.label"
      class="console-overview-card"
    >
      <span>{{ item.label }}</span>
      <strong>{{ item.value }}</strong>
    </div>
  </div>
</template>

<style scoped>
.console-overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.console-overview-card {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background:
    linear-gradient(180deg, rgba(96, 165, 250, 0.045), rgba(12, 24, 39, 0.78)),
    rgba(19, 34, 53, 0.74);
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 76px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.console-overview-card span {
  color: #91a5c2;
  font-size: 12px;
}

.console-overview-card strong {
  color: #f7fbff;
  line-height: 1.5;
  font-size: 14px;
  overflow-wrap: anywhere;
}

@media (max-width: 800px) {
  .console-overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
