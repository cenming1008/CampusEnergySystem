<script setup lang="ts">
const props = withDefaults(defineProps<{
  title?: string
  subtitle?: string
  shell?: 'standard' | 'console'
  accent?: 'none' | 'blue' | 'amber' | 'teal' | 'neutral'
}>(), {
  title: '',
  subtitle: '',
  shell: 'standard',
  accent: 'none',
})
</script>

<template>
  <section
    class="monitor-section-panel"
    :class="[
      `monitor-section-panel--${shell}`,
      `monitor-section-panel--${accent}`,
    ]"
  >
    <div
      v-if="title || subtitle || $slots.headerExtra"
      class="monitor-section-panel__head"
    >
      <div v-if="title || subtitle">
        <h3 v-if="title">{{ title }}</h3>
        <span v-if="subtitle">{{ subtitle }}</span>
      </div>
      <div
        v-if="$slots.headerExtra"
        class="monitor-section-panel__extra"
      >
        <slot name="headerExtra" />
      </div>
    </div>
    <slot />
  </section>
</template>

<style scoped>
.monitor-section-panel--standard {
  padding: 16px;
  background: #131d2b;
  border: 1px solid #243244;
  border-radius: 14px;
  box-sizing: border-box;
}

.monitor-section-panel--console {
  padding: 20px 24px;
  border-radius: 16px;
  border: 1px solid rgba(52, 72, 99, 0.88);
  background: linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
  position: relative;
}

.monitor-section-panel--console::before {
  content: '';
  position: absolute;
  top: 16px;
  bottom: 16px;
  left: 0;
  width: 3px;
  border-radius: 0 2px 2px 0;
  background: transparent;
}

.monitor-section-panel--console.monitor-section-panel--blue {
  background-image:
    linear-gradient(180deg, rgba(96, 165, 250, 0.04) 0%, transparent 70%),
    linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
}

.monitor-section-panel--console.monitor-section-panel--blue::before { background: #60a5fa; }

.monitor-section-panel--console.monitor-section-panel--amber {
  background-image:
    linear-gradient(180deg, rgba(251, 191, 36, 0.05) 0%, transparent 70%),
    linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
}

.monitor-section-panel--console.monitor-section-panel--amber::before { background: #fbbf24; }

.monitor-section-panel--console.monitor-section-panel--teal {
  background-image:
    linear-gradient(180deg, rgba(45, 212, 191, 0.04) 0%, transparent 70%),
    linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
}

.monitor-section-panel--console.monitor-section-panel--teal::before { background: #2dd4bf; }
.monitor-section-panel--console.monitor-section-panel--neutral::before { background: rgba(110, 130, 160, 0.45); }

.monitor-section-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.monitor-section-panel__head h3 {
  margin: 0;
}

.monitor-section-panel__head span {
  display: block;
  margin-top: 4px;
  font-size: 12px;
}

.monitor-section-panel__extra {
  display: flex;
  justify-content: flex-end;
  flex: 1;
  min-width: 0;
}

.monitor-section-panel--standard .monitor-section-panel__head h3 {
  font-size: 16px;
  color: #f8fafc;
}

.monitor-section-panel--standard .monitor-section-panel__head span {
  color: #8ea0bc;
}

.monitor-section-panel--console .monitor-section-panel__head {
  gap: 20px;
  margin-bottom: 16px;
}

.monitor-section-panel--console .monitor-section-panel__head h3 {
  font-size: 15px;
  font-weight: 600;
}

.monitor-section-panel--console .monitor-section-panel__head span {
  color: #8ca0ba;
  line-height: 1.5;
}

.monitor-section-panel--console.monitor-section-panel--blue .monitor-section-panel__head h3 { color: #93c5fd; }
.monitor-section-panel--console.monitor-section-panel--amber .monitor-section-panel__head h3 { color: #fde68a; }
.monitor-section-panel--console.monitor-section-panel--teal .monitor-section-panel__head h3 { color: #5eead4; }
.monitor-section-panel--console.monitor-section-panel--neutral .monitor-section-panel__head h3 { color: #cbd5e1; }

@media (max-width: 1100px) {
  .monitor-section-panel--console {
    padding: 18px 20px;
  }

  .monitor-section-panel--console .monitor-section-panel__head {
    flex-direction: column;
    align-items: flex-start;
  }

  .monitor-section-panel__extra {
    justify-content: flex-start;
  }
}

@media (max-width: 800px) {
  .monitor-section-panel--console {
    padding: 16px 18px;
  }
}
</style>
