<script setup lang="ts">
import type { PropType } from 'vue'
import type { CompensationProfileItem } from './types'

defineProps({
  items: {
    type: Array as PropType<CompensationProfileItem[]>,
    default: () => [],
  },
})
</script>

<template>
  <section class="side-panel side-panel--muted">
    <div class="side-panel__head">
      <h3>设备档案</h3>
      <span>基础信息与安装资料，仅作信息参考</span>
    </div>

    <div class="profile-list">
      <div
        v-for="item in items"
        :key="item.label"
        class="profile-row"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </div>
    </div>
  </section>
</template>

<style scoped>
.side-panel {
  padding: 16px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
}

.side-panel--muted {
  opacity: 0.92;
}

.side-panel__head {
  margin-bottom: 12px;
}

.side-panel__head h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.side-panel__head span {
  display: block;
  margin-top: 4px;
  color: #8ea0bc;
  font-size: 12px;
}

.profile-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.profile-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(41, 57, 77, 0.72);
}

.profile-row:last-child {
  border-bottom: none;
}

.profile-row span {
  color: #91a5c4;
  font-size: 12px;
}

.profile-row strong {
  color: #dfe8f5;
  font-size: 12px;
  text-align: right;
  max-width: 60%;
  line-height: 1.5;
  word-break: break-word;
}
</style>
