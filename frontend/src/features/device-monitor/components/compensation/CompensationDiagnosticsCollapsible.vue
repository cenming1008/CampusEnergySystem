<script setup lang="ts">
import { computed } from 'vue'
import type { MonitorTemplateDiagnostics } from '@/api/deviceMonitor'
import DeviceTemplateDiagnosticsPanel from '@/features/device-monitor/components/common/DeviceTemplateDiagnosticsPanel.vue'
import PanelCollapseToggle from '@/shared/components/PanelCollapseToggle.vue'
import { usePanelCollapse } from '@/shared/composables/usePanelCollapse'

const props = defineProps<{
  diagnostics: MonitorTemplateDiagnostics
}>()

const { collapsed, toggle } = usePanelCollapse('compensation-monitor:collapse:diagnostics', true)

const statusLabel = computed(() => {
  // 与 DeviceTemplateDiagnosticsPanel 的 statusMeta 映射保持一致，新增状态需同步
  const map: Record<string, string> = {
    passed: '接入完整',
    partial: '部分接入',
    missing: '指标缺失',
    offline: '采集离线',
  }
  return map[props.diagnostics.overall_status] || '部分接入'
})

const summaryText = computed(() => {
  const coverage = props.diagnostics.metric_coverage
  return `${statusLabel.value} · ${coverage.live}/${coverage.total} 指标覆盖`
})
</script>

<template>
  <section class="diagnostics-collapsible">
    <div class="diagnostics-collapsible__head">
      <div class="diagnostics-collapsible__title">
        <h3>接入诊断</h3>
        <span>{{ summaryText }}</span>
      </div>
      <PanelCollapseToggle
        :collapsed="collapsed"
        @toggle="toggle"
      />
    </div>

    <div
      v-if="!collapsed"
      class="diagnostics-collapsible__body"
    >
      <DeviceTemplateDiagnosticsPanel :diagnostics="diagnostics" />
    </div>
  </section>
</template>

<style scoped>
.diagnostics-collapsible {
  padding: 16px;
  background: #131d2b;
  border: 1px solid #243244;
  border-radius: 14px;
}

.diagnostics-collapsible__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.diagnostics-collapsible__title {
  min-width: 0;
}

.diagnostics-collapsible__title h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.diagnostics-collapsible__title span {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #8ea0bc;
}

.diagnostics-collapsible__body {
  margin-top: 14px;
}

/* 内嵌完整诊断面板时抹掉其自带卡片外框与重复头部 */
.diagnostics-collapsible__body :deep(.template-diagnostics) {
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
}

.diagnostics-collapsible__body :deep(.template-diagnostics__header) {
  display: none;
}
</style>
