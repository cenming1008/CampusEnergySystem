<script setup lang="ts">
import { Lock, Refresh, Setting, SwitchButton } from '@element-plus/icons-vue'
import type { ControlConsoleActionCard } from '@/features/device-control/viewMapping'
import MonitorSectionPanel from '@/shared/components/MonitorSectionPanel.vue'

defineProps<{
  actionCards: ControlConsoleActionCard[]
  toggleSubmitting: boolean
  currentControlModeLabel: string
  canRunManualSwitch: boolean
  manualSwitchDisabledReason: string
  manualPhaseOptions: Array<{ label: string; value: 'A' | 'B' | 'C' | 'COMMON' }>
  manualSwitchActionOptions: Array<{ label: string; value: 'none' | 'on' | 'off' }>
  manualPhase: 'A' | 'B' | 'C' | 'COMMON'
  manualSwitchAction: 'none' | 'on' | 'off'
  remoteControlEnabled: boolean
}>()

const emit = defineEmits<{
  (e: 'actionCard', key: ControlConsoleActionCard['key']): void
  (e: 'update:manualPhase', value: 'A' | 'B' | 'C' | 'COMMON'): void
  (e: 'update:manualSwitchAction', value: 'none' | 'on' | 'off'): void
  (e: 'manualSwitch'): void
}>()

function resolveActionIcon(iconKey: ControlConsoleActionCard['iconKey']) {
  if (iconKey === 'switch') return SwitchButton
  if (iconKey === 'refresh') return Refresh
  return Setting
}
</script>

<template>
  <MonitorSectionPanel
    shell="console"
    accent="amber"
    title="远程控制"
  >
    <template #headerExtra>
      <el-tag
        :type="remoteControlEnabled ? 'success' : 'info'"
        effect="dark"
        size="small"
      >
        {{ remoteControlEnabled ? '已开通' : '未开通' }}
      </el-tag>
    </template>
    <div class="remote-actions">
      <button
        v-for="card in actionCards"
        :key="card.title"
        class="remote-card"
        :class="card.enabled ? 'remote-card--enabled' : 'remote-card--locked'"
        type="button"
        :disabled="!card.enabled || toggleSubmitting"
        @click="emit('actionCard', card.key)"
      >
        <div class="remote-card__top">
          <span class="remote-card__icon-wrap">
            <component
              :is="resolveActionIcon(card.iconKey)"
              class="remote-card__icon"
            />
          </span>
          <component
            :is="Lock"
            v-if="!card.enabled"
            class="remote-card__lock-icon"
          />
        </div>
        <strong>{{ card.title }}</strong>
        <em v-if="card.enabled">{{ card.actionLabel }}</em>
        <em v-else-if="card.disabledReason" class="remote-card__reason">{{ card.disabledReason }}</em>
      </button>
    </div>
    <div class="manual-switch-box">
      <div class="manual-switch-box__head">
        <el-tooltip content="先切到手动模式，再执行投切指令" placement="top">
          <strong>手动投切控制</strong>
        </el-tooltip>
      </div>
      <div class="manual-switch-row">
        <div class="manual-switch-field">
          <label class="manual-switch-label">当前模式</label>
          <div class="manual-switch-mode-indicator">
            <el-tag
              :type="currentControlModeLabel === '手动' ? 'warning' : 'info'"
              effect="dark"
            >
              {{ currentControlModeLabel }}模式
            </el-tag>
          </div>
        </div>
        <div class="manual-switch-field">
          <label class="manual-switch-label">目标相位</label>
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
        <div class="manual-switch-field">
          <label class="manual-switch-label">投切动作</label>
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
        <el-button
          type="warning"
          :loading="toggleSubmitting"
          :disabled="!canRunManualSwitch || manualSwitchAction === 'none'"
          :title="manualSwitchDisabledReason"
          @click="emit('manualSwitch')"
        >
          发送手动投切指令
        </el-button>
      </div>
    </div>
  </MonitorSectionPanel>
</template>

<style scoped>
.remote-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.remote-card {
  min-height: 150px;
  padding: 18px 20px;
  border-radius: 12px;
  border: 1px solid rgba(48, 70, 95, 0.6);
  background: rgba(19, 34, 53, 0.7);
  text-align: left;
  color: #a7b7cb;
  display: flex;
  flex-direction: column;
  gap: 0;
  transition: border-color 0.18s ease;
}

.remote-card--locked {
  cursor: not-allowed;
  opacity: 0.45;
  filter: grayscale(0.3);
}

.remote-card--enabled {
  cursor: pointer;
  opacity: 1;
  border-color: rgba(251, 191, 36, 0.4);
  background: rgba(19, 34, 53, 0.7);
}

.remote-card--enabled:hover { border-color: rgba(251, 191, 36, 0.65); }
.remote-card--enabled:active { transform: translateY(1px); }

.remote-card__top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 36px;
}

.remote-card__icon-wrap {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: rgba(251, 191, 36, 0.08);
  display: grid;
  place-items: center;
}

.remote-card__icon {
  width: 18px;
  height: 18px;
  color: #fbbf24;
}

.remote-card__lock-icon {
  width: 16px;
  height: 16px;
  color: #fca5a5;
}

.remote-card strong {
  display: block;
  margin: 18px 0 6px;
  font-size: 15px;
  color: #f7fbff;
}

.remote-card em {
  margin-top: auto;
  display: inline-block;
  font-size: 13px;
  color: #fcd34d;
  font-style: normal;
}

.remote-card__reason {
  color: #7a90ab;
  font-size: 11px;
}

.manual-switch-box {
  margin-top: 14px;
  padding: 18px;
  border-radius: 14px;
  border: 1px solid rgba(251, 191, 36, 0.18);
  background: rgba(19, 34, 53, 0.74);
}

.manual-switch-box__head {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 14px;
}

.manual-switch-box__head strong {
  font-size: 14px;
  letter-spacing: 0.2px;
  color: #fef3c7;
}

.manual-switch-box__head span {
  color: #b7c6da;
  font-size: 12px;
}

.manual-switch-row {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr auto;
  gap: 12px;
  align-items: end;
}

.manual-switch-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.manual-switch-label {
  font-size: 12px;
  color: #e7eef8;
}

.manual-switch-mode-indicator {
  min-height: 32px;
  display: flex;
  align-items: center;
}

.manual-switch-select { width: 100%; }


.manual-switch-box :deep(.el-select .el-input__wrapper) {
  background: rgba(9, 18, 29, 0.84);
  box-shadow: inset 0 0 0 1px rgba(251, 191, 36, 0.12);
  border-radius: 10px;
}

.manual-switch-box :deep(.el-select .el-input__wrapper:hover) {
  box-shadow: inset 0 0 0 1px rgba(251, 191, 36, 0.28);
}

.manual-switch-box :deep(.el-select .el-input__wrapper.is-focus) {
  box-shadow: inset 0 0 0 1px rgba(251, 191, 36, 0.45);
}

.manual-switch-box :deep(.el-input__inner) {
  color: #eef4fd;
}

@media (max-width: 1200px) {
  .remote-actions {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  }

  .manual-switch-row {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .manual-switch-box__head,
  .capability-note {
    flex-direction: column;
    align-items: flex-start;
  }

  .capability-note__text,
  .capability-note__row {
    text-align: left;
    justify-content: flex-start;
  }

  .manual-switch-row,
  .remote-actions {
    grid-template-columns: 1fr;
  }
}
</style>
