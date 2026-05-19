<script setup lang="ts">
import type { PropType } from 'vue'

interface ParamItem {
  label: string
  value: string
}

defineProps({
  items: { type: Array as PropType<ParamItem[]>, default: () => [] },
})

const emit = defineEmits<{ (e: 'edit'): void }>()
</script>

<template>
  <section class="param-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />控制参数</span>
      <button type="button" class="param-edit" data-test="param-edit" @click="emit('edit')">
        修改 →
      </button>
    </header>
    <div class="param-body">
      <div v-if="items.length === 0" class="param-empty">暂无控制参数</div>
      <div v-for="item in items" :key="item.label" class="param-row">
        <span class="param-k">{{ item.label }}</span>
        <span class="param-v">{{ item.value }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.param-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
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
.param-edit {
  background: transparent;
  border: none;
  color: #67e8f9;
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}
.param-body {
  padding: 9px 14px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.param-empty {
  font-size: 12px;
  color: #5e6c83;
  text-align: center;
  padding: 8px 0;
}
.param-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
}
.param-k {
  color: #5e6c83;
}
.param-v {
  color: #e5edf7;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}
</style>
