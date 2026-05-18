<script setup lang="ts">
import { computed } from 'vue'
import { Setting } from '@element-plus/icons-vue'
import type { ControlConsoleActionCard } from '@/features/device-control/viewMapping'
import MonitorSectionPanel from '@/shared/components/MonitorSectionPanel.vue'

const props = defineProps<{
  actionCards: ControlConsoleActionCard[]
  toggleSubmitting: boolean
  currentControlModeLabel: string
  canRunManualSwitch: boolean
  manualSwitchDisabledReason: string
  manualPhaseOptions: Array<{ label: string; value: 'A' | 'B' | 'C' | 'COMMON' }>
  manualSwitchActionOptions: Array<{ label: string; value: 'none' | 'on' | 'off' }>
  manualCommonGroupOptions: Array<{ label: string; value: 1 | 2 | 3 }>
  manualPhase: 'A' | 'B' | 'C' | 'COMMON'
  manualSwitchAction: 'none' | 'on' | 'off'
  manualCommonGroup: 1 | 2 | 3
}>()

const emit = defineEmits<{
  (e: 'actionCard', key: ControlConsoleActionCard['key']): void
  (e: 'update:manualPhase', value: 'A' | 'B' | 'C' | 'COMMON'): void
  (e: 'update:manualSwitchAction', value: 'none' | 'on' | 'off'): void
  (e: 'update:manualCommonGroup', value: 1 | 2 | 3): void
  (e: 'manualSwitch'): void
}>()

const modeSwitchCard = computed(() => props.actionCards.find((card) => card.key === 'switch_control_mode'))
</script>

<template>
  <MonitorSectionPanel
    shell="console"
    accent="amber"
    title="远程控制"
  >
    <div class="remote-control-compact">
      <div class="mode-switch-tile">
        <div class="mode-switch-tile__meta">
          <span class="mode-switch-tile__icon">
            <Setting />
          </span>
          <div>
            <strong>控制模式切换</strong>
            <small>当前模式：{{ currentControlModeLabel }}</small>
          </div>
        </div>
        <button
          v-if="modeSwitchCard"
          type="button"
          class="mode-switch-action"
          data-test="mode-switch-action"
          :disabled="!modeSwitchCard.enabled || toggleSubmitting"
          :title="modeSwitchCard.disabledReason"
          @click="emit('actionCard', modeSwitchCard.key)"
        >
          {{ toggleSubmitting ? '切换中...' : modeSwitchCard.actionLabel }}
        </button>
      </div>

      <div class="manual-switch-inline">
        <div class="manual-switch-title">
          <strong>手动投切控制</strong>
          <small>选择目标与动作后发送</small>
        </div>
        <div class="manual-switch-field">
          <label class="manual-switch-label">相位</label>
          <el-select
            :model-value="manualPhase"
            :disabled="!canRunManualSwitch || toggleSubmitting"
            class="manual-switch-select"
            @update:model-value="emit('update:manualPhase', $event)"
          >
            <el-option
              v-for="item in manualPhaseOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </div>
        <div v-if="manualPhase === 'COMMON'" class="manual-switch-field">
          <label class="manual-switch-label">组</label>
          <el-select
            :model-value="manualCommonGroup"
            :disabled="!canRunManualSwitch || toggleSubmitting"
            class="manual-switch-select"
            @update:model-value="emit('update:manualCommonGroup', $event)"
          >
            <el-option
              v-for="item in manualCommonGroupOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </div>
        <div class="manual-switch-field">
          <label class="manual-switch-label">动作</label>
          <el-select
            :model-value="manualSwitchAction"
            :disabled="!canRunManualSwitch || toggleSubmitting"
            class="manual-switch-select"
            :class="manualSwitchAction !== 'none' ? 'manual-switch-select--active' : ''"
            @update:model-value="emit('update:manualSwitchAction', $event)"
          >
            <el-option
              v-for="item in manualSwitchActionOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </div>
        <button
          type="button"
          class="manual-switch-submit"
          :class="{ 'is-loading': toggleSubmitting }"
          :disabled="!canRunManualSwitch || manualSwitchAction === 'none'"
          :title="manualSwitchDisabledReason"
          @click="emit('manualSwitch')"
        >
          {{ toggleSubmitting ? '发送中...' : '发送指令' }}
        </button>
      </div>
    </div>
  </MonitorSectionPanel>
</template>

<style scoped>
.remote-control-compact {
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background:
    linear-gradient(180deg, rgba(251, 191, 36, 0.035), rgba(12, 24, 39, 0.78)),
    rgba(16, 28, 44, 0.72);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
  display: grid;
  grid-template-columns: minmax(230px, 0.8fr) minmax(0, 2.2fr);
  gap: 10px;
  align-items: stretch;
}

.mode-switch-tile,
.manual-switch-inline {
  min-width: 0;
  border: 1px solid rgba(48, 70, 95, 0.58);
  border-radius: 8px;
  background: rgba(8, 17, 30, 0.34);
}

.mode-switch-tile {
  padding: 10px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.mode-switch-tile__meta {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.mode-switch-tile__icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid rgba(251, 191, 36, 0.22);
  background: rgba(251, 191, 36, 0.1);
  display: grid;
  place-items: center;
  color: #fbbf24;
  flex: 0 0 auto;
}

.mode-switch-tile__icon svg {
  width: 16px;
  height: 16px;
}

.mode-switch-tile strong,
.manual-switch-title strong {
  display: block;
  color: #f7fbff;
  font-size: 13px;
  line-height: 1.35;
}

.mode-switch-tile small,
.manual-switch-title small {
  display: block;
  margin-top: 2px;
  color: #8da2bf;
  font-size: 12px;
  line-height: 1.35;
}

.mode-switch-action {
  min-height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid rgba(245, 158, 11, 0.42);
  background: rgba(120, 53, 15, 0.18);
  color: #fde68a;
  font: inherit;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
}

.mode-switch-action:hover:not(:disabled),
.manual-switch-submit:hover:not(:disabled) {
  background: rgba(120, 53, 15, 0.3);
  border-color: rgba(245, 158, 11, 0.62);
}

.mode-switch-action:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.manual-switch-inline {
  padding: 10px;
  display: grid;
  grid-template-columns: minmax(128px, 0.8fr) repeat(2, minmax(120px, 1fr)) minmax(112px, 0.85fr);
  gap: 10px;
  align-items: end;
}

.manual-switch-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.manual-switch-label {
  font-size: 11px;
  color: #93a7c4;
}

.manual-switch-select { width: 100%; }

.manual-switch-submit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid rgba(245, 158, 11, 0.42);
  background: rgba(120, 53, 15, 0.18);
  color: #fde68a;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  width: 100%;
  transition: border-color 0.16s ease, background 0.16s ease;
}

.manual-switch-submit:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}


.remote-control-compact :deep(.el-select__wrapper),
.remote-control-compact :deep(.el-select .el-input__wrapper) {
  background: rgba(9, 18, 29, 0.84);
  border: 1px solid rgba(251, 191, 36, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  border-radius: 10px;
}

.remote-control-compact :deep(.el-select__wrapper.is-hovering),
.remote-control-compact :deep(.el-select .el-input__wrapper:hover) {
  border-color: rgba(251, 191, 36, 0.32);
  box-shadow: 0 0 0 1px rgba(251, 191, 36, 0.08);
}

.remote-control-compact :deep(.el-select__wrapper.is-focused),
.remote-control-compact :deep(.el-select .el-input__wrapper.is-focus) {
  border-color: rgba(251, 191, 36, 0.5);
  box-shadow: 0 0 0 1px rgba(251, 191, 36, 0.16);
}

.remote-control-compact :deep(.el-select__selected-item),
.remote-control-compact :deep(.el-select__placeholder),
.remote-control-compact :deep(.el-input__inner) {
  color: #eef4fd;
}

.remote-control-compact :deep(.el-select__caret) {
  color: #8ea0bc;
}

@media (max-width: 1200px) {
  .remote-control-compact {
    grid-template-columns: 1fr;
  }

  .manual-switch-inline {
    grid-template-columns: minmax(128px, 0.8fr) repeat(2, minmax(120px, 1fr)) minmax(112px, 0.85fr);
  }
}

@media (max-width: 768px) {
  .manual-switch-inline {
    grid-template-columns: 1fr;
  }

  .mode-switch-tile {
    align-items: flex-start;
    flex-direction: column;
  }

  .mode-switch-action,
  .manual-switch-submit {
    width: 100%;
  }
}
</style>
