<script setup lang="ts">
import type { PropType } from 'vue'

const props = defineProps({
  mode: {
    type: String as PropType<'auto' | 'manual' | 'unknown'>,
    default: 'unknown',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  disabledReason: {
    type: String,
    default: '',
  },
  submitting: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits<{ (e: 'switch'): void }>()

function pick(target: 'auto' | 'manual') {
  if (props.disabled || props.submitting) return
  if (props.mode === target) return
  emit('switch')
}
</script>

<template>
  <div class="mode-toggle" :title="disabled ? disabledReason : undefined">
    <span class="mode-label">控制模式</span>
    <div class="mode-segs">
      <button
        type="button"
        class="mode-seg"
        :class="{ 'is-active': mode === 'auto' }"
        :disabled="disabled || submitting"
        data-test="mode-auto"
        @click="pick('auto')"
      >自动</button>
      <button
        type="button"
        class="mode-seg"
        :class="{ 'is-active': mode === 'manual' }"
        :disabled="disabled || submitting"
        data-test="mode-manual"
        @click="pick('manual')"
      >手动</button>
    </div>
  </div>
</template>

<style scoped>
.mode-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.mode-label {
  font-size: 10px;
  color: #5e6c83;
  white-space: nowrap;
}
.mode-segs {
  display: inline-flex;
  border: 1px solid #1f2c41;
  border-radius: 5px;
  overflow: hidden;
}
.mode-seg {
  padding: 0 10px;
  height: 22px;
  font-size: 11px;
  background: #0b1623;
  border: none;
  border-right: 1px solid #1f2c41;
  color: #9aa7bd;
  cursor: pointer;
  line-height: 22px;
}
.mode-seg:last-child {
  border-right: none;
}
.mode-seg:hover:not(:disabled):not(.is-active) {
  color: #e5edf7;
}
.mode-seg.is-active {
  background: #182538;
  color: #67e8f9;
  box-shadow: inset 0 0 0 1px rgba(34, 211, 238, 0.3);
}
.mode-seg:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
