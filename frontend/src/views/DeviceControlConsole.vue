<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Monitor, Refresh } from '@element-plus/icons-vue'
import { usePermissions } from '@/shared/composables/usePermissions'
import ControlConsoleRemotePanel from '@/features/device-control/components/ControlConsoleRemotePanel.vue'
import ControlConsoleLogPanel from '@/features/device-control/components/ControlConsoleLogPanel.vue'
import ControlConsoleReadonlyParamsPanel from '@/features/device-control/components/ControlConsoleReadonlyParamsPanel.vue'
import ControlConsoleWritableParamsPanel from '@/features/device-control/components/ControlConsoleWritableParamsPanel.vue'
import ControlConsoleWriteDialog from '@/features/device-control/components/ControlConsoleWriteDialog.vue'
import { useCapacitorBankControlConsole } from '@/features/device-control/useCapacitorBankControlConsole'
import ConsoleOverviewGrid from '@/shared/components/ConsoleOverviewGrid.vue'
import MonitorInlineAlert from '@/shared/components/MonitorInlineAlert.vue'
import MonitorSectionPanel from '@/shared/components/MonitorSectionPanel.vue'
import MonitorPageHeader from '@/shared/components/MonitorPageHeader.vue'

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
  overviewItems,
  editableParameterCards,
  manualPhaseOptions,
  manualSwitchActionOptions,
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
</script>

<template>
  <div
    v-loading="loading"
    class="console-page"
  >
    <!-- Header -->
    <MonitorPageHeader
      shell="console"
      :title="archive?.name || '补偿控制台'"
      :subtitle="`${archive?.sn || '--'} · ${archive?.location || '未配置安装位置'}`"
    >
      <template #leading>
        <el-button
          :icon="ArrowLeft"
          text
          @click="router.push('/devices')"
        >
          返回设备台账
        </el-button>
      </template>
      <template #titleMeta>
        <span
          class="status-dot"
          :class="{ 'status-dot--online': runtimeStatus?.is_online }"
        />
        <span class="status-dot-label">{{ runtimeStatus?.is_online ? '在线' : '离线' }}</span>
      </template>
      <template #actions>
        <el-button
          :icon="Monitor"
          @click="goMonitor"
        >
          前往监控页
        </el-button>
        <el-button
          :icon="Refresh"
          @click="loadPage"
        >
          刷新
        </el-button>
      </template>
    </MonitorPageHeader>

    <MonitorInlineAlert
      v-if="loadError"
      title="控制台暂不可用"
      :message="loadError"
      tone="danger"
    />

    <template v-else-if="isCapacitorBankController">
      <div class="console-body">
        <!-- Left: main panels -->
        <div class="console-main">
          <MonitorInlineAlert
            v-if="profileWarning"
            title="参数档案暂时不可用"
            :message="profileWarning"
            tone="warning"
          />

          <!-- Section 1: 设备概览 -->
          <MonitorSectionPanel
            shell="console"
            accent="blue"
            title="设备概览"
          >
            <ConsoleOverviewGrid :items="overviewItems" />
          </MonitorSectionPanel>

          <ControlConsoleRemotePanel
            :action-cards="actionCards"
            :toggle-submitting="toggleSubmitting"
            :current-control-mode-label="currentControlModeLabel"
            :can-run-manual-switch="canRunManualSwitch"
            :manual-switch-disabled-reason="manualSwitchDisabledReason"
            :manual-phase-options="manualPhaseOptions"
            :manual-switch-action-options="manualSwitchActionOptions"
            :manual-phase="manualSwitchForm.phase"
            :manual-switch-action="manualSwitchForm.switch_action"
            :remote-control-enabled="controlCapabilities?.supports_remote_control === true"
            @action-card="handleActionCard"
            @update:manual-phase="manualSwitchForm.phase = $event"
            @update:manual-switch-action="manualSwitchForm.switch_action = $event"
            @manual-switch="handleManualSwitchCommand"
          />

          <!-- Section 3: 参数管理 -->
          <MonitorSectionPanel
            shell="console"
            accent="teal"
            title="参数管理"
            :subtitle="controlCapabilities?.write_status_message || ''"
          >

            <ControlConsoleReadonlyParamsPanel
              :section-view="readonlySectionView"
              :readonly-summary-view="readonlySummaryView"
            />

            <ControlConsoleWritableParamsPanel
              :write-section-view="writeSectionView"
              :can-write-parameters="canWriteParameters"
              :editable-parameter-cards="editableParameterCards"
              @open-write-dialog="openWriteDialog"
            />
          </MonitorSectionPanel>
        </div>

        <aside class="console-sidebar">
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
  gap: 20px;
  color: #dbe5f4;
  width: min(100%, 1680px);
  margin: 0 auto;
  padding: 0 12px 24px;
  box-sizing: border-box;
}

/* ─── Header ────────────────────────────────────────────────── */

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4b5563;
  flex-shrink: 0;
}

.status-dot--online {
  background: #4ade80;
  box-shadow: 0 0 7px rgba(74, 222, 128, 0.55);
}

.status-dot-label {
  font-size: 12px;
  color: #8ea0bc;
}

/* ─── Alert ──────────────────────────────────────────────────── */

/* ─── Two-column body ─────────────────────────────────────────── */

.console-body {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(320px, 360px);
  gap: 20px;
  align-items: start;
}

.console-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.console-sidebar {
  position: sticky;
  top: 20px;
}

/* ─── Large screens ──────────────────────────────────────────── */

@media (min-width: 1920px) {
  .console-page {
    width: min(100%, 2100px);
    padding-inline: 20px;
  }

  .console-body {
    grid-template-columns: minmax(0, 1.6fr) minmax(400px, 480px);
    gap: 24px;
  }

  .console-main {
    gap: 24px;
  }
}

@media (min-width: 2400px) {
  .console-page {
    width: min(100%, 2560px);
    padding-inline: 28px;
  }

  .console-body {
    grid-template-columns: minmax(0, 1.6fr) minmax(480px, 560px);
    gap: 28px;
  }

  .console-main {
    gap: 28px;
  }
}

/* ─── Medium screens (MacBook 14") ───────────────────────────── */

@media (max-width: 1600px) and (min-width: 1401px) {
  .console-page {
    width: min(100%, 1560px);
  }

  .console-body {
    grid-template-columns: minmax(0, 1.6fr) minmax(320px, 380px);
  }
}

@media (max-width: 1400px) {
  .console-page {
    width: min(100%, 1360px);
    padding-inline: 8px;
  }

  .console-body {
    grid-template-columns: minmax(0, 1fr) minmax(300px, 340px);
    gap: 16px;
  }
}

/* ─── Responsive ─────────────────────────────────────────────── */

@media (max-width: 1100px) {
  .console-page {
    width: 100%;
    padding-inline: 0;
  }

  .console-body {
    grid-template-columns: 1fr;
  }

  .console-sidebar {
    position: static;
  }
}

@media (max-width: 800px) {
  .console-page {
    gap: 16px;
  }
}
</style>
