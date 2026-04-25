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

const archiveShortCode = computed(() => (archive.value?.sn || 'CAP').slice(0, 3).toUpperCase())
</script>

<template>
  <div
    v-loading="loading"
    class="console-page"
  >
    <header class="console-hero">
      <div class="console-hero__identity">
        <button
          type="button"
          class="console-hero__back"
          @click="router.push('/devices')"
        >
          <el-icon><ArrowLeft /></el-icon>
          <span>返回设备台账</span>
        </button>

        <div class="console-hero__main">
          <div class="console-hero__mark">{{ archiveShortCode }}</div>
          <div>
            <h2>{{ archive?.name || '补偿控制台' }}</h2>
            <p>
              <span>设备编号：{{ archive?.sn || '--' }}</span>
              <i />
              <span>安装位置：{{ archive?.location || '未配置安装位置' }}</span>
            </p>
          </div>
        </div>
      </div>

      <div class="console-hero__right">
        <div class="console-hero__status-row">
          <span
            class="console-status-chip"
            :class="runtimeStatus?.is_online ? 'console-status-chip--online' : 'console-status-chip--offline'"
          >
            <i />
            {{ runtimeStatus?.is_online ? '在线采集' : '离线' }}
          </span>
          <span class="console-status-chip console-status-chip--mode">
            {{ currentControlModeLabel }}
          </span>
        </div>

        <div class="console-hero__actions">
          <button
            type="button"
            class="console-action console-action--blue"
            @click="goMonitor"
          >
            <el-icon><Monitor /></el-icon>
            <span>前往监控页</span>
          </button>
          <button
            type="button"
            class="console-action console-action--neutral"
            @click="loadPage"
          >
            <el-icon><Refresh /></el-icon>
            <span>刷新</span>
          </button>
        </div>
      </div>
    </header>

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
  gap: 16px;
  color: #dbe5f4;
  width: min(100%, 1680px);
  margin: 0 auto;
  padding: 0 0 24px;
  box-sizing: border-box;
}

/* ─── Header ────────────────────────────────────────────────── */

.console-hero {
  display: grid;
  grid-template-columns: minmax(360px, 1fr) minmax(420px, auto);
  gap: 28px;
  align-items: center;
  padding: 20px 22px;
  border-radius: 12px;
  border: 1px solid rgba(58, 76, 102, 0.88);
  background:
    linear-gradient(135deg, rgba(13, 24, 38, 0.98), rgba(15, 29, 47, 0.96)),
    linear-gradient(90deg, rgba(96, 165, 250, 0.07), rgba(245, 158, 11, 0.06));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.console-hero__identity,
.console-hero__right {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.console-hero__right {
  align-items: flex-end;
}

.console-hero__back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: fit-content;
  padding: 0;
  border: 0;
  background: transparent;
  color: #7f93b2;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.console-hero__back:hover {
  color: #dbeafe;
}

.console-hero__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.console-hero__mark {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: rgba(245, 158, 11, 0.14);
  border: 1px solid rgba(245, 158, 11, 0.28);
  color: #fde68a;
  font-size: 12px;
  font-weight: 700;
}

.console-hero h2 {
  margin: 0;
  color: #f7fbff;
  font-size: 24px;
  line-height: 1.15;
  letter-spacing: 0;
}

.console-hero p {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin: 8px 0 0;
  color: #8ea5c1;
  font-size: 12px;
}

.console-hero p i {
  width: 1px;
  height: 10px;
  background: rgba(142, 160, 188, 0.42);
}

.console-hero__status-row,
.console-hero__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.console-status-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 7px;
  border: 1px solid rgba(72, 96, 130, 0.68);
  background: rgba(7, 15, 26, 0.58);
  color: #cbd5e1;
  font-size: 12px;
  font-weight: 600;
}

.console-status-chip i {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: currentColor;
}

.console-status-chip--online {
  color: #86efac;
  border-color: rgba(34, 197, 94, 0.35);
}

.console-status-chip--offline {
  color: #fca5a5;
  border-color: rgba(248, 113, 113, 0.35);
}

.console-status-chip--mode {
  color: #bfdbfe;
  border-color: rgba(96, 165, 250, 0.32);
}

.console-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 104px;
  height: 34px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid rgba(72, 96, 130, 0.76);
  background: rgba(7, 15, 26, 0.68);
  color: #dbeafe;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.16s ease, background 0.16s ease;
}

.console-action:hover {
  background: rgba(15, 29, 47, 0.95);
  border-color: rgba(96, 165, 250, 0.45);
}

.console-action--blue {
  color: #bfdbfe;
  border-color: rgba(96, 165, 250, 0.42);
  background: rgba(30, 64, 175, 0.16);
}

/* ─── Alert ──────────────────────────────────────────────────── */

/* ─── Two-column body ─────────────────────────────────────────── */

.console-body {
  display: grid;
  grid-template-columns: minmax(0, 1.95fr) 360px;
  gap: 16px;
  align-items: start;
}

.console-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.console-sidebar {
  min-width: 0;
}

.console-sidebar {
  position: sticky;
  top: 20px;
}

/* ─── Large screens ──────────────────────────────────────────── */

@media (min-width: 1920px) {
  .console-page {
    width: min(100%, 2100px);
    gap: 20px;
  }

  .console-body {
    grid-template-columns: minmax(0, 1.95fr) 440px;
    gap: 20px;
  }

  .console-main {
    gap: 20px;
  }
}

@media (min-width: 2400px) {
  .console-page {
    width: min(100%, 2560px);
    gap: 24px;
  }

  .console-body {
    grid-template-columns: minmax(0, 1.95fr) 520px;
    gap: 24px;
  }

  .console-main {
    gap: 24px;
  }
}

@media (max-width: 1360px) {
  .console-body {
    grid-template-columns: 1fr;
  }
}

/* ─── Responsive ─────────────────────────────────────────────── */

@media (max-width: 1100px) {
  .console-page {
    width: 100%;
    padding-inline: 0;
  }

  .console-hero {
    grid-template-columns: 1fr;
  }

  .console-hero__right {
    align-items: flex-start;
  }

  .console-hero__status-row,
  .console-hero__actions {
    justify-content: flex-start;
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
