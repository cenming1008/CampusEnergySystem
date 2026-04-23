<script setup lang="ts">
withDefaults(defineProps<{
  title?: string
  message?: string
  tone?: 'warning' | 'danger'
  subtle?: boolean
}>(), {
  title: '',
  message: '',
  tone: 'warning',
  subtle: false,
})
</script>

<template>
  <div
    class="monitor-inline-alert"
    :class="[
      `monitor-inline-alert--${tone}`,
      { 'monitor-inline-alert--subtle': subtle },
    ]"
  >
    <strong v-if="title">{{ title }}</strong>
    <span v-if="message">{{ message }}</span>
  </div>
</template>

<style scoped>
.monitor-inline-alert {
  padding: 12px 14px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.monitor-inline-alert strong {
  font-size: 13px;
}

.monitor-inline-alert span {
  font-size: 12px;
  line-height: 1.6;
}

.monitor-inline-alert--warning {
  border: 1px solid rgba(170, 122, 36, 0.4);
  background: rgba(73, 48, 14, 0.22);
}

.monitor-inline-alert--warning strong {
  color: #fcd34d;
}

.monitor-inline-alert--warning span {
  color: #d8c08a;
}

.monitor-inline-alert--danger {
  border: 1px solid rgba(248, 113, 113, 0.28);
  background: rgba(120, 32, 32, 0.14);
}

.monitor-inline-alert--danger strong,
.monitor-inline-alert--danger span {
  color: #fecaca;
}

.monitor-inline-alert--subtle {
  margin: 0;
}
</style>
