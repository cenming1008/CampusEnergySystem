<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { toggleDeviceStatus } from '@/api/device'
import { usePermissions } from '@/shared/composables/usePermissions'
import ControlConsoleRemotePanel from '@/features/device-control/components/ControlConsoleRemotePanel.vue'
import ControlConsoleLogPanel from '@/features/device-control/components/ControlConsoleLogPanel.vue'
import ControlConsoleParametersPanel from '@/features/device-control/components/ControlConsoleParametersPanel.vue'
import ControlConsoleWriteDialog from '@/features/device-control/components/ControlConsoleWriteDialog.vue'
import { useCapacitorBankControlConsole } from '@/features/device-control/useCapacitorBankControlConsole'
import CompensationHeader from '@/features/device-monitor/components/compensation/CompensationHeader.vue'
import type { CompensationHeaderModel } from '@/features/device-monitor/components/compensation/types'
import MonitorInlineAlert from '@/shared/components/MonitorInlineAlert.vue'
import MonitorSectionPanel from '@/shared/components/MonitorSectionPanel.vue'

const route = useRoute()
const router = useRouter()
const { canManageDevices, canControlDevices, currentRole, isAdmin } = usePermissions()

const deviceId = computed(() => Number(route.params.id))
const {
  loading,
  toggleSubmitting,
  writeSubmitting,
  writeDialogVisible,
  controlProfile,
  loadError,
  profileWarning,
  writeForm,
  manualSwitchForm,
  archive,
  runtimeStatus,
  isCapacitorBankController,
  controlCapabilities,
  currentControlModeLabel,
  canRunManualSwitch,
  manualSwitchDisabledReason,
  canWriteParameters,
  selectedWriteMeta,
  editableParameterCards,
  manualPhaseOptions,
  manualSwitchActionOptions,
  manualCommonGroupOptions,
  actionCards,
  readonlySectionView,
  readonlySummaryView,
  writeSectionView,
  logView,
  loadPage,
  handleManualSwitchCommand,
  openWriteDialog,
  submitParameterWrite,
  handleActionCard,
} = useCapacitorBankControlConsole({
  deviceId,
  canManageDevices,
  canControlDevices,
  currentRole,
  isAdmin,
})

function goMonitor() {
  router.push(`/devices/${deviceId.value}/monitor`)
}

const consoleHeaderModel = computed<CompensationHeaderModel>(() => ({
  title: archive.value?.name || '补偿控制台',
  serial: archive.value?.sn || '--',
  location: archive.value?.location || '未配置安装位置',
  deviceStatus: runtimeStatus.value?.is_online ? '在线采集' : '离线',
  deviceStatusTone: runtimeStatus.value?.is_online ? 'info' : 'neutral',
  tags: [
    {
      label: currentControlModeLabel.value,
      tone: currentControlModeLabel.value === '自动' ? 'info' : 'warning',
    },
  ],
}))

const toggleActionLabel = computed(() => actionCards.value[0]?.actionLabel || '停用设备')
const toggleButtonType = computed(() => runtimeStatus.value?.is_active ? 'danger' : 'success')

async function handleHeaderToggleDevice() {
  if (!deviceId.value || !canControlDevices.value) return
  const nextActive = !(runtimeStatus.value?.is_active ?? true)
  try {
    const { value } = await ElMessageBox.prompt(
      `${nextActive ? '将设备管理状态切换为启用' : '将设备管理状态切换为停用'}，可填写本次操作备注。`,
      nextActive ? '启用设备' : '停用设备',
      {
        confirmButtonText: nextActive ? '确认启用' : '确认停用',
        cancelButtonText: '取消',
        inputPlaceholder: '例如：例行巡检后恢复采集管理',
      },
    )
    toggleSubmitting.value = true
    await toggleDeviceStatus(deviceId.value, nextActive, value)
    ElMessage.success(nextActive ? '设备已启用' : '设备已停用')
    await loadPage()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(nextActive ? '设备启用失败' : '设备停用失败')
  } finally {
    toggleSubmitting.value = false
  }
}
</script>

<template>
  <div
    v-loading="loading"
    class="console-page"
  >
    <CompensationHeader
      :model="consoleHeaderModel"
      :toggle-action-label="toggleActionLabel"
      :toggle-button-type="toggleButtonType"
      :toggle-submitting="toggleSubmitting"
      :can-control-devices="canControlDevices"
      show-console-entry
      console-entry-label="监控页"
      @back="router.push('/devices')"
      @open-console="goMonitor"
      @refresh="loadPage"
      @toggle="handleHeaderToggleDevice"
    />

    <MonitorInlineAlert
      v-if="loadError"
      title="控制台暂不可用"
      :message="loadError"
      tone="danger"
    />

    <template v-else-if="isCapacitorBankController">
      <div class="console-monitor-layout console-monitor-layout--equal-height">
        <div class="console-monitor-layout__main">
          <MonitorInlineAlert
            v-if="profileWarning"
            title="参数档案暂时不可用"
            :message="profileWarning"
            tone="warning"
          />

          <ControlConsoleRemotePanel
            :action-cards="actionCards"
            :toggle-submitting="toggleSubmitting"
            :current-control-mode-label="currentControlModeLabel"
            :can-run-manual-switch="canRunManualSwitch"
            :manual-switch-disabled-reason="manualSwitchDisabledReason"
            :manual-phase-options="manualPhaseOptions"
            :manual-switch-action-options="manualSwitchActionOptions"
            :manual-common-group-options="manualCommonGroupOptions"
            :manual-phase="manualSwitchForm.phase"
            :manual-switch-action="manualSwitchForm.switch_action"
            :manual-common-group="manualSwitchForm.group"
            @action-card="handleActionCard"
            @update:manual-phase="manualSwitchForm.phase = $event"
            @update:manual-switch-action="manualSwitchForm.switch_action = $event"
            @update:manual-common-group="manualSwitchForm.group = $event"
            @manual-switch="handleManualSwitchCommand"
          />

          <MonitorSectionPanel
            shell="console"
            accent="teal"
            title="参数设置"
          >
            <ControlConsoleParametersPanel
              :section-view="readonlySectionView"
              :readonly-summary-view="readonlySummaryView"
              :write-section-view="writeSectionView"
              :can-write-parameters="canWriteParameters"
              :editable-parameter-cards="editableParameterCards"
              @open-write-dialog="openWriteDialog"
            />
          </MonitorSectionPanel>
        </div>

        <aside class="console-monitor-layout__side">
          <ControlConsoleLogPanel :log-view="logView" />
        </aside>
      </div>
    </template>

    <ControlConsoleWriteDialog
      v-model="writeDialogVisible"
      :selected-write-meta="selectedWriteMeta"
      :control-profile="controlProfile"
      :target-value="writeForm.target_value"
      :reason="writeForm.reason"
      :write-submitting="writeSubmitting"
      @update:target-value="writeForm.target_value = $event"
      @update:reason="writeForm.reason = $event"
      @submit="submitParameterWrite"
    />
  </div>
</template>

<style scoped>
/* ─── Base ─────────────────────────────────────────────────── */

.console-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: #dbe5f4;
  width: min(100%, 1680px);
  margin: 0 auto;
  padding: 0 0 24px;
  box-sizing: border-box;
}

.console-monitor-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.9fr) 380px;
  gap: 16px;
  align-items: stretch;
}

.console-monitor-layout__main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.console-monitor-layout__side {
  display: flex;
  min-width: 0;
  min-height: 0;
}

/* ─── Large screens ──────────────────────────────────────────── */

@media (min-width: 1920px) {
  .console-page {
    width: min(100%, 2100px);
    gap: 20px;
  }

  .console-monitor-layout {
    grid-template-columns: minmax(0, 1.9fr) 440px;
    gap: 20px;
  }

  .console-monitor-layout__main {
    gap: 20px;
  }
}

@media (min-width: 2400px) {
  .console-page {
    width: min(100%, 2560px);
    gap: 24px;
  }

  .console-monitor-layout {
    grid-template-columns: minmax(0, 1.9fr) 520px;
    gap: 24px;
  }

  .console-monitor-layout__main {
    gap: 24px;
  }
}

@media (max-width: 1360px) {
  .console-monitor-layout {
    grid-template-columns: 1fr;
  }
}

/* ─── Responsive ─────────────────────────────────────────────── */

@media (max-width: 1100px) {
  .console-page {
    width: 100%;
    padding-inline: 0;
  }

  .console-monitor-layout {
    grid-template-columns: 1fr;
  }

  .console-monitor-layout__side {
    min-height: auto;
  }
}

@media (max-width: 800px) {
  .console-page {
    gap: 16px;
  }
}
</style>
