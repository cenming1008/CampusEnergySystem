<script setup lang="ts">
import { ArrowLeft, Refresh, SwitchButton } from '@element-plus/icons-vue'
import CompensationAlarmTable from '@/features/device-monitor/components/compensation/CompensationAlarmTable.vue'
import CompensationDeviceProfile from '@/features/device-monitor/components/compensation/CompensationDeviceProfile.vue'
import CompensationEventTimeline from '@/features/device-monitor/components/compensation/CompensationEventTimeline.vue'
import DeviceDiagnosticsSummary from '@/features/device-monitor/components/common/DeviceDiagnosticsSummary.vue'
import DeviceMetricGrid from '@/features/device-monitor/components/common/DeviceMetricGrid.vue'
import DeviceTemplateDiagnosticsPanel from '@/features/device-monitor/components/common/DeviceTemplateDiagnosticsPanel.vue'
import DeviceTrendPanel from '@/features/device-monitor/components/common/DeviceTrendPanel.vue'
import MonitorPageHeader from '@/shared/components/MonitorPageHeader.vue'
import MonitorSectionPanel from '@/shared/components/MonitorSectionPanel.vue'
import MonitorViewShell from './MonitorViewShell.vue'
import type { DeviceMonitorPageModel } from '@/features/device-monitor/composables/useDeviceMonitorPage'

defineProps<{
  page: DeviceMonitorPageModel
}>()
</script>

<template>
  <MonitorViewShell>
    <template #header>
      <MonitorPageHeader
        :title="page.archive?.name || '设备监控'"
        :subtitle="`${page.archive?.sn || '--'} · ${page.archive?.location || '未设置位置'}`"
      >
        <template #leading>
          <el-button
            :icon="ArrowLeft"
            text
            @click="page.router.push('/devices')"
          >
            返回设备台账
          </el-button>
        </template>
        <template #actions>
          <el-tag
            :type="page.statusTagType(page.runtimeStatus?.code)"
            size="large"
          >
            {{ page.runtimeStatus?.label || '状态未知' }}
          </el-tag>
          <el-button
            :type="page.toggleButtonType"
            plain
            :icon="SwitchButton"
            :loading="page.toggleSubmitting"
            :disabled="!page.canControlDevices || page.isPendingArchiveDevice"
            @click="page.handleToggleDevice"
          >
            {{ page.toggleActionLabel }}
          </el-button>
          <el-button
            :icon="Refresh"
            @click="page.loadPage(true)"
          >
            刷新
          </el-button>
        </template>
      </MonitorPageHeader>
    </template>

    <template #main>
      <DeviceMetricGrid :metrics="page.metricCards" />

      <div
        v-if="page.isRealtimeStale"
        class="stale-data-notice"
      >
        <strong>数据已过期</strong>
        <span>通讯状态：离线，当前指标为最后一次成功入库值。</span>
        <span>最近成功入库：{{ page.formatDateTime(page.realtimeStaleTime) }}</span>
      </div>

      <DeviceTrendPanel
        v-model="page.chartMetric"
        v-model:time-range="page.timeRange"
        :fields="page.trendFields"
        :summary="page.trendSummary"
        :unit="page.chartUnit(page.chartMetric)"
        :loading="page.chartLoading"
        :shortcuts="page.timeShortcuts"
        :chart-ref="page.chart.chartRef"
        @range-change="page.handleRangeChange"
      />

      <CompensationAlarmTable
        :rows="page.alarms"
        :action-id="page.alarmActionId"
        @resolve="page.handleResolveAlarm"
      />

      <MonitorSectionPanel
        title="启停记录"
        subtitle="设备启停与控制操作留痕"
      >
        <el-table
          :data="page.controlLogs"
          class="dark-table"
          empty-text="暂无启停记录"
        >
          <el-table-column
            prop="created_at"
            label="时间"
            min-width="170"
          >
            <template #default="{ row }">
              {{ page.formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="action"
            label="动作"
            width="100"
          />
          <el-table-column
            prop="result"
            label="结果"
            width="100"
          >
            <template #default="{ row }">
              <el-tag :type="row.result === 'success' ? 'success' : 'danger'">
                {{ row.result || '--' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="operator"
            label="操作人"
            width="120"
          />
          <el-table-column
            prop="reason"
            label="备注"
            min-width="220"
          />
        </el-table>
      </MonitorSectionPanel>
    </template>

    <template #side>
      <DeviceTemplateDiagnosticsPanel
        v-if="page.templateDiagnostics"
        :diagnostics="page.templateDiagnostics"
      />
      <DeviceDiagnosticsSummary
        :runtime-status="page.runtimeStatus"
        :diagnostics-summary="page.diagnosticsSummary"
      />
      <CompensationEventTimeline :events="page.compensationEvents" />
      <CompensationDeviceProfile :items="page.compensationProfileItems" />
    </template>
  </MonitorViewShell>
</template>

<style scoped>
.stale-data-notice {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(248, 113, 113, 0.28);
  background: rgba(248, 113, 113, 0.1);
  color: #f8c7c7;
}

.stale-data-notice strong {
  color: #fecaca;
}

.stale-data-notice span {
  font-size: 13px;
}

:deep(.dark-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(14, 24, 37, 0.92);
  --el-table-border-color: #243244;
  --el-table-row-hover-bg-color: rgba(22, 33, 48, 0.92);
  --el-table-text-color: #dbe6f5;
  --el-table-header-text-color: #8ea0bc;
}
</style>
