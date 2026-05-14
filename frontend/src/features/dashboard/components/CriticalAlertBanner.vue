<script setup lang="ts">
interface Props {
  title: string
  detail?: string
  location?: string
  startedAt?: string
}
defineProps<Props>()
const emit = defineEmits<{ (e: 'dismiss'): void; (e: 'handle'): void; (e: 'mute'): void }>()
</script>

<template>
  <div class="banner a-glow-err">
    <span class="dot a-pulse-ring" />
    <span class="sev-label mono">严重告警</span>
    <span class="body">
      <slot>{{ title }}</slot>
    </span>
    <span v-if="location || startedAt" class="loc mono">
      <template v-if="location">· {{ location }}</template>
      <template v-if="startedAt"> · {{ startedAt }} 起</template>
    </span>
    <span class="spacer" />
    <button type="button" class="primary" @click="emit('handle')">立即处理</button>
    <button type="button" class="ghost" @click="emit('mute')">暂时静音</button>
    <button type="button" class="close" @click="emit('dismiss')" aria-label="关闭">×</button>
  </div>
</template>

<style scoped>
.banner {
  background: linear-gradient(90deg, rgba(239,90,90,0.15), rgba(239,90,90,0.05) 40%, transparent);
  border: 1px solid rgba(239,90,90,0.33);
  border-left: 4px solid var(--err);
  border-radius: 10px;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  color: var(--text);
}
.dot {
  position: relative;
  width: 10px;
  height: 10px;
  border-radius: 5px;
  background: var(--err);
  color: var(--err);
  flex: 0 0 auto;
}
.sev-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--err);
}
.body { font-size: 13px; color: var(--text); font-weight: 500; }
.loc { font-size: 11px; color: var(--text-dim); }
.spacer { flex: 1; }
button { font-family: inherit; cursor: pointer; }
.primary {
  padding: 5px 12px;
  font-size: 11px;
  border-radius: 4px;
  background: var(--err);
  color: #fff;
  border: none;
  font-weight: 500;
}
.ghost {
  padding: 5px 10px;
  font-size: 11px;
  border-radius: 4px;
  background: transparent;
  color: var(--text-mid);
  border: 1px solid var(--border);
}
.close {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  padding: 0;
  background: transparent;
  color: var(--text-dim);
  border: none;
  font-size: 16px;
}
</style>
