<script setup lang="ts">
import { ArrowLeft, Refresh, SwitchButton } from '@element-plus/icons-vue'
import type { PropType } from 'vue'
import type { CompensationHeaderModel, CompensationWorkbenchTab, CompensationWorkbenchTabOption } from './types'

defineProps({
  model: {
    type: Object as PropType<CompensationHeaderModel>,
    required: true,
  },
  toggleActionLabel: {
    type: String,
    required: true,
  },
  toggleButtonType: {
    type: String,
    required: true,
  },
  toggleSubmitting: {
    type: Boolean,
    default: false,
  },
  canControlDevices: {
    type: Boolean,
    default: false,
  },
  tabs: {
    type: Array as PropType<CompensationWorkbenchTabOption[]>,
    default: () => [],
  },
  activeTab: {
    type: String as PropType<CompensationWorkbenchTab>,
    default: 'runtime',
  },
})

defineEmits<{
  back: []
  refresh: []
  toggle: []
  'tab-change': [value: CompensationWorkbenchTab]
}>()
</script>

<template>
  <div class="comp-header">
    <div class="comp-header__bar">
      <div class="comp-header__device-pill">
        <button
          type="button"
          class="comp-header__back comp-header__identity-field"
          @click="$emit('back')"
          aria-label="返回监视列表"
        >
          <span class="comp-header__identity-value comp-header__identity-value--link">
            <el-icon><ArrowLeft /></el-icon>
            监视
          </span>
        </button>
        <span class="comp-header__identity-divider" />
        <span class="comp-header__identity-field comp-header__identity-field--primary">
          <span class="comp-header__identity-label">设备名称</span>
          <span class="comp-header__identity-value">{{ model.title }}</span>
        </span>
        <span class="comp-header__identity-divider" />
        <span class="comp-header__identity-field">
          <span class="comp-header__identity-label">位置</span>
          <span class="comp-header__identity-value">{{ model.location }}</span>
        </span>
      </div>

      <div
        v-if="tabs.length"
        class="comp-header__tabs"
        role="tablist"
        aria-label="补偿控制器工作台"
      >
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          class="comp-header__tab"
          :class="[
            `comp-header__tab--${tab.tone || 'normal'}`,
            { 'is-active': activeTab === tab.value },
          ]"
          role="tab"
          :aria-selected="activeTab === tab.value"
          @click="$emit('tab-change', tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="comp-header__actions">
        <button
          type="button"
          class="comp-header__action"
          :class="[
            toggleButtonType === 'success' ? 'comp-header__action--success' : 'comp-header__action--danger',
            { 'is-loading': toggleSubmitting },
          ]"
          :disabled="!canControlDevices || toggleSubmitting"
          :aria-label="toggleSubmitting ? '处理中' : toggleActionLabel"
          :title="toggleSubmitting ? '处理中' : toggleActionLabel"
          @click="$emit('toggle')"
        >
          <el-icon
            v-if="!toggleSubmitting"
            :size="14"
          >
            <SwitchButton />
          </el-icon>
          <span>{{ toggleSubmitting ? '处理中...' : toggleActionLabel }}</span>
        </button>
        <button
          type="button"
          class="comp-header__action comp-header__action--neutral"
          aria-label="刷新"
          title="刷新"
          @click="$emit('refresh')"
        >
          <el-icon :size="14">
            <Refresh />
          </el-icon>
          <span>刷新</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comp-header {
  padding: 10px 14px;
  background:
    linear-gradient(180deg, rgba(16, 31, 52, 0.96), rgba(9, 20, 34, 0.98)),
    rgba(13, 24, 38, 0.98);
  border: 1px solid rgba(66, 89, 124, 0.82);
  border-radius: 14px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 16px 34px rgba(0, 0, 0, 0.18);
}

.comp-header__bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.comp-header__back {
  display: inline-flex;
  align-items: center;
  padding: 0;
  border: 0;
  background: transparent;
  font: inherit;
  cursor: pointer;
}

.comp-header__back:hover {
  color: #dbeafe;
}

.comp-header__device-pill {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 372px;
  min-height: 38px;
  padding: 7px 14px;
  border: 1px solid rgba(59, 130, 246, 0.34);
  border-radius: 18px;
  background:
    linear-gradient(90deg, rgba(34, 211, 238, 0.18), transparent 18%),
    linear-gradient(135deg, rgba(13, 27, 47, 0.96), rgba(10, 22, 39, 0.68));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.07),
    0 0 0 1px rgba(15, 23, 42, 0.22);
  flex: 0 0 auto;
}

.comp-header__identity-divider {
  width: 1px;
  height: 24px;
  background: linear-gradient(180deg, transparent, rgba(95, 123, 165, 0.64), transparent);
  flex: 0 0 auto;
}

.comp-header__identity-field {
  display: inline-flex;
  flex-direction: column;
  justify-content: center;
  min-width: 58px;
  gap: 2px;
  white-space: nowrap;
}

.comp-header__identity-field--primary {
  min-width: 118px;
}

.comp-header__identity-label {
  color: #6f86a6;
  font-size: 10px;
  font-weight: 600;
  line-height: 1;
}

.comp-header__identity-value {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #d8e7ff;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.2;
}

.comp-header__identity-value--link {
  color: #b7cced;
}

.comp-header__back .comp-header__identity-value {
  min-height: 22px;
  padding: 0 7px 0 2px;
}

.comp-header__tabs {
  display: grid;
  grid-template-columns: repeat(var(--comp-header-tab-count, 4), minmax(0, 1fr));
  flex: 1 1 auto;
  min-width: 0;
  padding: 2px;
  border: 1px solid rgba(74, 95, 128, 0.62);
  border-radius: 13px;
  background: rgba(5, 12, 22, 0.34);
}

.comp-header__tab {
  min-height: 36px;
  padding: 0 18px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: #879bb8;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.16s ease, color 0.16s ease, box-shadow 0.16s ease;
}

.comp-header__tab:hover {
  color: #dbeafe;
}

.comp-header__tab.is-active {
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.66), rgba(30, 64, 175, 0.6));
  color: #eff6ff;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.14),
    0 8px 18px rgba(20, 45, 96, 0.22);
}

.comp-header__tab--warning.is-active {
  background: rgba(245, 158, 11, 0.18);
  color: #fef3c7;
}

.comp-header__tab--danger.is-active {
  background: rgba(220, 38, 38, 0.18);
  color: #fee2e2;
}

.comp-header__actions {
  display: flex;
  justify-content: flex-end;
  gap: 9px;
}

.comp-header__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 104px;
  flex: 0 0 104px;
  height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid rgba(72, 96, 130, 0.76);
  background: rgba(5, 12, 22, 0.42);
  color: #dbeafe;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.16s ease, background 0.16s ease, color 0.16s ease;
}

.comp-header__action:hover:not(:disabled) {
  background: rgba(15, 29, 47, 0.95);
  border-color: rgba(96, 165, 250, 0.45);
}

.comp-header__action:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.comp-header__action--danger {
  color: #fecaca;
  border-color: rgba(248, 113, 113, 0.42);
  background: rgba(127, 29, 29, 0.18);
}

.comp-header__action--success {
  color: #bbf7d0;
  border-color: rgba(34, 197, 94, 0.42);
  background: rgba(20, 83, 45, 0.18);
}

.comp-header__action--warning {
  color: #fde68a;
  border-color: rgba(245, 158, 11, 0.42);
  background: rgba(120, 53, 15, 0.18);
}

.comp-header__action--neutral {
  color: #dbeafe;
}

@media (max-width: 900px) {
  .comp-header__bar {
    flex-wrap: wrap;
  }

  .comp-header__tabs {
    order: 3;
    flex-basis: 100%;
  }

  .comp-header__action {
    width: var(--touch-target);
    flex-basis: var(--touch-target);
    min-height: var(--touch-target);
    padding: 0 10px;
  }

  .comp-header__action span {
    display: none;
  }

  /* 提交中保留文字提示，避免空按钮 */
  .comp-header__action.is-loading span {
    display: inline;
  }
}

@media (max-width: 900px) {
  .comp-header__device-pill {
    min-width: 0;
  }
}

@media (max-width: 720px) {
  .comp-header__bar {
    flex-direction: column;
    align-items: stretch;
  }

  .comp-header__tabs {
    overflow-x: auto;
  }

  .comp-header__device-pill {
    flex-wrap: wrap;
  }
}
</style>
