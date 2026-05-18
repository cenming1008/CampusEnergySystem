<script setup lang="ts">
import { computed } from 'vue'
import { ArrowLeft, Refresh, SwitchButton } from '@element-plus/icons-vue'
import DeviceDiagnosticsSummary from '@/features/device-monitor/components/common/DeviceDiagnosticsSummary.vue'
import DeviceMetricGrid from '@/features/device-monitor/components/common/DeviceMetricGrid.vue'
import DeviceTemplateDiagnosticsPanel from '@/features/device-monitor/components/common/DeviceTemplateDiagnosticsPanel.vue'
import DeviceTrendPanel from '@/features/device-monitor/components/common/DeviceTrendPanel.vue'
import MonitorSectionPanel from '@/shared/components/MonitorSectionPanel.vue'
import MonitorViewShell from './MonitorViewShell.vue'
import type { DeviceMonitorPageModel } from '@/features/device-monitor/composables/useDeviceMonitorPage'

const props = defineProps<{
  page: DeviceMonitorPageModel
}>()

const GENERIC_EVENT_LIMIT = 20

/** 通用设备档案信息（不使用补偿设备专属的 profileItems） */
const genericProfileItems = computed(() => {
  const archive = props.page.archive
  if (!archive) return []
  return [
    { label: '设备名称', value: archive.name || '--' },
    { label: '序列号', value: archive.sn || '--' },
    { label: '设备类型', value: archive.device_type || '--' },
    { label: '能源类型', value: archive.energy_type || '--' },
    { label: '安装位置', value: archive.location || '未设置位置' },
    ...(archive.rated_capacity != null && archive.rated_capacity > 0
      ? [{ label: '额定容量', value: `${archive.rated_capacity} ${archive.unit || 'kW'}` }]
      : []),
    ...(archive.description ? [{ label: '描述', value: archive.description }] : []),
  ]
})

/** 通用设备运行事件（复用 statusHistory，但使用通用文案） */
const genericEvents = computed(() => {
  const history = props.page.statusHistory
  if (!history || !history.length) return []
  return history.slice(0, GENERIC_EVENT_LIMIT).map((item) => ({
    time: item.timestamp,
    title: item.title,
    detail: item.detail || '',
    status: item.status,
    event_type: item.event_type,
  }))
})
</script>

<template>
  <MonitorViewShell>
    <template #header>
      <div class="generic-header">
        <div class="generic-header__identity">
          <button
            type="button"
            class="generic-header__back"
            @click="page.router.push('/devices')"
          >
            <el-icon><ArrowLeft /></el-icon>
            <span>返回设备台账</span>
          </button>
          <div class="generic-header__title">
            <h2>{{ page.archive?.name || '设备监控' }}</h2>
            <p>
              <span>{{ page.archive?.sn || '--' }}</span>
              <i />
              <span>{{ page.archive?.location || '未设置位置' }}</span>
            </p>
          </div>
        </div>
        <div class="generic-header__actions">
          <span
            class="generic-header__chip"
            :class="{
              'generic-header__chip--success': page.statusTagType(page.runtimeStatus?.code) === 'success',
              'generic-header__chip--danger': page.statusTagType(page.runtimeStatus?.code) === 'danger',
              'generic-header__chip--warning': page.statusTagType(page.runtimeStatus?.code) === 'warning',
              'generic-header__chip--neutral': page.statusTagType(page.runtimeStatus?.code) === 'info',
            }"
          >
            <i />
            {{ page.runtimeStatus?.label || '状态未知' }}
          </span>
          <button
            type="button"
            class="generic-header__action"
            :class="[
              page.toggleButtonType === 'success' ? 'generic-header__action--success' : 'generic-header__action--danger',
              { 'is-loading': page.toggleSubmitting },
            ]"
            :disabled="!page.canControlDevices || page.isPendingArchiveDevice || page.toggleSubmitting"
            @click="page.handleToggleDevice"
          >
            <el-icon
              v-if="!page.toggleSubmitting"
              :size="14"
            >
              <SwitchButton />
            </el-icon>
            <span>{{ page.toggleSubmitting ? '处理中...' : page.toggleActionLabel }}</span>
          </button>
          <button
            type="button"
            class="generic-header__action generic-header__action--neutral"
            @click="page.loadPage(true)"
          >
            <el-icon :size="14">
              <Refresh />
            </el-icon>
            <span>刷新</span>
          </button>
        </div>
      </div>
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

      <MonitorSectionPanel
        title="告警记录"
        subtitle="设备告警与异常事件"
      >
        <el-table
          :data="page.alarms"
          class="dark-table"
          empty-text="当前暂无告警记录"
        >
          <el-table-column
            prop="timestamp"
            label="时间"
            min-width="170"
          >
            <template #default="{ row }">
              {{ page.formatDateTime(row.timestamp) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="message"
            label="告警内容"
            min-width="280"
          />
          <el-table-column
            prop="severity"
            label="级别"
            width="100"
          >
            <template #default="{ row }">
              <el-tag :type="row.severity === 'critical' ? 'danger' : row.severity === 'warning' ? 'warning' : 'info'">
                {{ row.severity || 'info' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="110"
            fixed="right"
          >
            <template #default="{ row }">
              <el-button
                v-if="!row.is_resolved"
                type="warning"
                link
                :loading="page.alarmActionId === row.id"
                @click="page.handleResolveAlarm(row)"
              >
                标记处理
              </el-button>
              <span
                v-else
                class="muted-text"
              >已关闭</span>
            </template>
          </el-table-column>
        </el-table>
      </MonitorSectionPanel>

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

      <!-- 运行事件（通用） -->
      <section
        v-if="genericEvents.length"
        class="generic-event-timeline"
      >
        <div class="generic-event-timeline__head">
          <h3>运行事件</h3>
          <span>共 {{ genericEvents.length }} 条</span>
        </div>
        <el-timeline>
          <el-timeline-item
            v-for="item in genericEvents"
            :key="`${item.time}-${item.title}`"
            :timestamp="page.formatDateTime(item.time)"
            :type="item.status === 'success' || item.status === 'resolved' ? 'success' : item.status === 'active' || item.status === 'failed' ? 'danger' : 'warning'"
            hollow
          >
            <div class="timeline-card">
              <strong>{{ item.title }}</strong>
              <p v-if="item.detail">{{ item.detail }}</p>
            </div>
          </el-timeline-item>
        </el-timeline>
      </section>

      <!-- 设备档案（通用） -->
      <section class="generic-device-profile">
        <div class="generic-device-profile__head">
          <h3>设备档案</h3>
        </div>
        <div class="profile-list">
          <div
            v-for="item in genericProfileItems"
            :key="item.label"
            class="profile-row"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </section>
    </template>
  </MonitorViewShell>
</template>

<style scoped>
/* ─── Header (dark theme, matching compensation style) ─── */
.generic-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 20px 22px;
  background:
    linear-gradient(135deg, rgba(13, 24, 38, 0.98), rgba(15, 29, 47, 0.96));
  border: 1px solid rgba(58, 76, 102, 0.88);
  border-radius: 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.generic-header__identity {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.generic-header__back {
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

.generic-header__back:hover {
  color: #dbeafe;
}

.generic-header__title h2 {
  margin: 0;
  font-size: 22px;
  color: #f5f7fb;
  line-height: 1.2;
}

.generic-header__title p {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin: 6px 0 0;
  font-size: 12px;
  color: #8ea0bc;
}

.generic-header__title i {
  width: 1px;
  height: 10px;
  background: rgba(142, 160, 188, 0.42);
}

.generic-header__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.generic-header__chip {
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
  line-height: 1;
}

.generic-header__chip i {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: currentColor;
  flex: 0 0 auto;
}

.generic-header__chip--success { color: #86efac; border-color: rgba(34, 197, 94, 0.35); }
.generic-header__chip--warning { color: #fde68a; border-color: rgba(245, 158, 11, 0.38); }
.generic-header__chip--danger { color: #fca5a5; border-color: rgba(248, 113, 113, 0.35); }
.generic-header__chip--neutral { color: #cbd5e1; border-color: rgba(72, 96, 130, 0.68); }

.generic-header__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 92px;
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
  transition: border-color 0.16s ease, background 0.16s ease, color 0.16s ease;
}

.generic-header__action:hover:not(:disabled) {
  background: rgba(15, 29, 47, 0.95);
  border-color: rgba(96, 165, 250, 0.45);
}

.generic-header__action:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.generic-header__action--danger {
  color: #fecaca;
  border-color: rgba(248, 113, 113, 0.42);
  background: rgba(127, 29, 29, 0.18);
}

.generic-header__action--success {
  color: #bbf7d0;
  border-color: rgba(34, 197, 94, 0.42);
  background: rgba(20, 83, 45, 0.18);
}

.generic-header__action--neutral {
  color: #dbeafe;
}

@media (max-width: 1100px) {
  .generic-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .generic-header__actions {
    justify-content: flex-start;
    width: 100%;
  }
}

/* ─── Stale data notice ─── */
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

/* ─── Misc ─── */
.muted-text {
  color: #8ea0bc;
  font-size: 12px;
}

/* ─── Side panels ─── */
.generic-event-timeline,
.generic-device-profile {
  padding: 16px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
}

.generic-event-timeline__head,
.generic-device-profile__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.generic-event-timeline__head h3,
.generic-device-profile__head h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.generic-event-timeline__head span {
  font-size: 12px;
  color: #5d7699;
}

.timeline-card {
  padding: 8px 10px;
  background: rgba(16, 27, 42, 0.9);
  border: 1px solid rgba(48, 67, 91, 0.78);
  border-radius: 10px;
}

.timeline-card strong {
  color: #f3f6fb;
  font-size: 13px;
}

.timeline-card p {
  margin: 4px 0 0;
  color: #8ea0bc;
  font-size: 12px;
  line-height: 1.5;
}

.profile-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.profile-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(41, 57, 77, 0.72);
}

.profile-row:last-child {
  border-bottom: none;
}

.profile-row span {
  color: #91a5c4;
  font-size: 12px;
}

.profile-row strong {
  color: #dfe8f5;
  font-size: 12px;
  text-align: right;
  max-width: 60%;
  line-height: 1.5;
  word-break: break-word;
}

/* ─── Tables ─── */
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
