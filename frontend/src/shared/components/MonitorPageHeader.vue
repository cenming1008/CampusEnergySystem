<script setup lang="ts">
withDefaults(defineProps<{
  title?: string
  subtitle?: string
  shell?: 'standard' | 'console'
}>(), {
  title: '',
  subtitle: '',
  shell: 'standard',
})
</script>

<template>
  <div
    class="monitor-page-header"
    :class="`monitor-page-header--${shell}`"
  >
    <div class="monitor-page-header__left">
      <slot name="leading" />
      <div class="monitor-page-header__content">
        <div class="monitor-page-header__title-row">
          <h2 v-if="title">{{ title }}</h2>
          <slot name="titleMeta" />
        </div>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>
    </div>
    <div
      v-if="$slots.actions"
      class="monitor-page-header__actions"
    >
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.monitor-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.monitor-page-header__left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.monitor-page-header__content {
  min-width: 0;
}

.monitor-page-header__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.monitor-page-header__title-row h2 {
  margin: 0;
  font-size: 22px;
}

.monitor-page-header__content p {
  margin: 4px 0 0;
}

.monitor-page-header__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.monitor-page-header--standard {
  padding: 18px 20px;
  background: #131d2b;
  border: 1px solid #243244;
  border-radius: 14px;
}

.monitor-page-header--standard .monitor-page-header__title-row h2 {
  color: #f8fafc;
}

.monitor-page-header--standard .monitor-page-header__content p {
  font-size: 12px;
  color: #8ea0bc;
}

.monitor-page-header--console {
  padding: 18px 24px;
  border-radius: 16px;
  border: 1px solid rgba(52, 72, 99, 0.88);
  background: linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
  gap: 20px;
}

.monitor-page-header--console .monitor-page-header__left {
  gap: 16px;
}

.monitor-page-header--console .monitor-page-header__title-row h2 {
  color: #f7fbff;
}

.monitor-page-header--console .monitor-page-header__content p {
  margin-top: 5px;
  color: #8ea5c1;
  font-size: 13px;
}

@media (max-width: 1100px) {
  .monitor-page-header,
  .monitor-page-header__actions {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 800px) {
  .monitor-page-header--console {
    padding: 16px 18px;
  }
}
</style>
