<script setup lang="ts">
import { ArrowDownBold, ArrowUpBold } from '@element-plus/icons-vue'

defineProps<{ collapsed: boolean }>()
defineEmits<{ (e: 'toggle'): void }>()
</script>

<template>
  <button
    type="button"
    class="panel-collapse-toggle"
    :aria-expanded="collapsed ? 'false' : 'true'"
    :title="collapsed ? '展开' : '收起'"
    @click="$emit('toggle')"
  >
    <el-icon>
      <component :is="collapsed ? ArrowDownBold : ArrowUpBold" />
    </el-icon>
  </button>
</template>

<style scoped>
.panel-collapse-toggle {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  padding: 0;
  border: 1px solid rgba(72, 96, 130, 0.6);
  border-radius: 7px;
  background: rgba(7, 15, 26, 0.6);
  color: #9fb1ca;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}

.panel-collapse-toggle:hover {
  color: #dbeafe;
  border-color: rgba(96, 165, 250, 0.55);
  background: rgba(96, 165, 250, 0.12);
}
</style>
