<script setup lang="ts">
import type { ControlConsoleLogView } from '@/features/device-control/viewMapping'
import MonitorInlineAlert from '@/shared/components/MonitorInlineAlert.vue'
import MonitorSectionPanel from '@/shared/components/MonitorSectionPanel.vue'

defineProps<{
  logView: ControlConsoleLogView
}>()
</script>

<template>
  <MonitorSectionPanel
    shell="console"
    accent="neutral"
    title="操作日志"
    class="control-console-log-panel"
  >
    <div class="control-console-log-panel__scroll">
      <MonitorInlineAlert
        v-if="logView.latestTimeoutAlertText"
        title="检测到设备回执超时"
        :message="logView.latestTimeoutAlertText"
        tone="danger"
        class="log-alert"
      />
      <div
        v-if="!logView.entries.length"
        class="empty-box"
      >
        <strong>暂无写入日志</strong>
      </div>
      <div
        v-else
        class="log-timeline"
      >
        <div
          v-for="log in logView.entries"
          :key="log.id"
          class="log-entry"
        >
          <div class="log-entry__track">
            <span
              class="log-entry__dot"
              :class="`log-entry__dot--${log.statusTone}`"
            />
            <span class="log-entry__line" />
          </div>
          <div class="log-entry__content">
            <div class="log-entry__top">
              <strong>{{ log.title }}</strong>
              <el-tag
                :type="log.statusTone"
                effect="dark"
                size="small"
              >
                {{ log.statusText }}
              </el-tag>
            </div>
            <span>{{ log.createdAtText }} · {{ log.operatorText }}<em v-if="log.sourceText" class="log-entry__source">{{ log.sourceText }}</em></span>
            <small v-if="log.reason">{{ log.reason }}</small>
          </div>
        </div>
      </div>
    </div>
  </MonitorSectionPanel>
</template>

<style scoped>
.control-console-log-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.control-console-log-panel__scroll {
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-width: thin;
  scrollbar-color: rgba(96, 165, 250, 0.45) rgba(15, 26, 41, 0.5);
}

.control-console-log-panel__scroll::-webkit-scrollbar {
  width: 6px;
}

.control-console-log-panel__scroll::-webkit-scrollbar-track {
  background: rgba(15, 26, 41, 0.5);
  border-radius: 999px;
}

.control-console-log-panel__scroll::-webkit-scrollbar-thumb {
  background: rgba(96, 165, 250, 0.45);
  border-radius: 999px;
}

.log-alert {
  margin-bottom: 14px;
}

.empty-box {
  padding: 18px 16px;
  border-radius: 12px;
  border: 1px dashed rgba(71, 100, 135, 0.62);
  background: rgba(15, 26, 41, 0.58);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-box strong {
  font-size: 14px;
  color: #dbe6f7;
}

.empty-box span {
  font-size: 12px;
  color: #91a5c2;
  line-height: 1.6;
}

.log-timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-entry {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr);
  gap: 10px;
}

.log-entry__track {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.log-entry__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-top: 4px;
  box-shadow: 0 0 0 4px rgba(96, 165, 250, 0.08);
}

.log-entry__dot--success { background: #4ade80; }
.log-entry__dot--warning { background: #fbbf24; }
.log-entry__dot--danger { background: #f87171; }
.log-entry__dot--info { background: #60a5fa; }

.log-entry__line {
  flex: 1;
  width: 1px;
  margin-top: 6px;
  background: linear-gradient(180deg, rgba(96, 165, 250, 0.35), rgba(96, 165, 250, 0));
}

.log-entry:last-child .log-entry__line {
  display: none;
}

.log-entry__content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background:
    linear-gradient(180deg, rgba(31, 48, 70, 0.52), rgba(12, 24, 39, 0.78)),
    rgba(19, 34, 53, 0.74);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.log-entry__top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}

.log-entry__top strong {
  color: #f7fbff;
  font-size: 14px;
  line-height: 1.45;
}

.log-entry__content > span {
  color: #b7c6da;
  font-size: 12px;
  line-height: 1.5;
}

.log-entry__content > small {
  color: #8ea0bc;
  font-size: 12px;
  line-height: 1.5;
}

.log-entry__source {
  margin-left: 6px;
  color: #7fb2e5;
  font-size: 11px;
  font-style: normal;
  text-transform: uppercase;
  letter-spacing: 0;
}

@media (max-width: 800px) {
  .control-console-log-panel {
    height: auto;
    min-height: 0;
    overflow: visible;
  }

  .control-console-log-panel__scroll {
    overflow: visible;
    padding-right: 0;
  }

  .log-entry__top {
    flex-direction: column;
    gap: 6px;
  }
}
</style>
