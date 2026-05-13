<script setup lang="ts">
import { computed } from 'vue'
import type { VNodeRef } from 'vue'
import MonitorSectionPanel from '@/shared/components/MonitorSectionPanel.vue'
import type { MonitorTrendField } from '@/api/deviceMonitor'

type SupportedTrendMetric = 'flow_rate' | 'voltage' | 'current' | 'reactive_power' | 'power_factor' | 'consumption'

const supportedTrendMetrics = new Set<SupportedTrendMetric>([
  'flow_rate',
  'voltage',
  'current',
  'reactive_power',
  'power_factor',
  'consumption',
])

const props = defineProps<{
  modelValue: SupportedTrendMetric
  timeRange: [Date, Date] | null
  fields: MonitorTrendField[]
  summary: {
    latest: number | null
    peak: number | null
    average: number | null
    valley: number | null
  }
  unit: string
  loading: boolean
  shortcuts?: Array<{ text: string; value: () => [Date, Date] }>
  chartRef?: VNodeRef
}>()

defineEmits<{
  'update:modelValue': [value: SupportedTrendMetric]
  'update:timeRange': [value: [Date, Date] | null]
  'range-change': []
}>()

const options = computed(() =>
  props.fields
    .filter((item): item is MonitorTrendField & { key: SupportedTrendMetric } =>
      supportedTrendMetrics.has(item.key as SupportedTrendMetric),
    )
    .map((item) => ({
      label: item.label,
      value: item.key,
      unit: item.unit ?? null,
    })),
)

const segmentedOptions = computed(() =>
  options.value.map((item) => ({ label: item.label, value: item.value })),
)

function displayNumber(value?: number | null) {
  if (value === null || value === undefined) return '--'
  return Number(value).toFixed(1)
}
</script>

<template>
  <section class="device-trend-panel">
    <div class="device-trend-panel__head">
      <div class="device-trend-panel__intro">
        <h3>历史趋势</h3>
        <span>按时间范围查看设备实时曲线</span>
      </div>
      <div
        v-if="options.length > 0"
        class="device-trend-panel__toolbar"
      >
        <div class="device-trend-panel__tab-wrapper">
          <div class="device-trend-panel__tab-switcher">
            <el-segmented
              :model-value="modelValue"
              :options="segmentedOptions"
              size="small"
              @change="$emit('update:modelValue', $event as SupportedTrendMetric)"
            />
          </div>
        </div>
        <div class="device-trend-panel__range-picker">
          <el-date-picker
            :model-value="timeRange"
            type="datetimerange"
            unlink-panels
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            range-separator="至"
            :shortcuts="shortcuts"
            @update:model-value="$emit('update:timeRange', $event)"
            @change="$emit('range-change')"
          />
        </div>
      </div>
    </div>
    <div
      v-if="options.length === 0"
      class="device-trend-panel__empty"
    >
      暂无可用趋势字段
    </div>
    <template v-else>
      <div class="device-trend-panel__summary">
        <span>当前 {{ displayNumber(summary.latest) }} {{ unit }}</span>
        <span>峰值 {{ displayNumber(summary.peak) }} {{ unit }}</span>
        <span>均值 {{ displayNumber(summary.average) }} {{ unit }}</span>
        <span>谷值 {{ displayNumber(summary.valley) }} {{ unit }}</span>
      </div>
      <div
        :ref="chartRef"
        v-loading="loading"
        class="device-trend-panel__chart"
      />
    </template>
  </section>
</template>

<style scoped>
.device-trend-panel {
  padding: 18px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.device-trend-panel__head {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.device-trend-panel__intro {
  min-width: 0;
}

.device-trend-panel__head h3 {
  margin: 0;
  font-size: 16px;
  color: #f5f7fb;
}

.device-trend-panel__head span {
  display: block;
  margin-top: 5px;
  font-size: 12px;
  color: #8ea0bc;
}

.device-trend-panel__toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  width: 100%;
  min-width: 0;
}

.device-trend-panel__tab-wrapper {
  flex: 0 1 auto;
  min-width: 0;
  position: relative;
}

.device-trend-panel__tab-switcher {
  overflow-x: auto;
  padding-bottom: 2px;
  scrollbar-width: none;
}

.device-trend-panel__tab-switcher::-webkit-scrollbar {
  display: none;
}

.device-trend-panel__tab-switcher :deep(.el-segmented) {
  white-space: nowrap;
  min-width: max-content;
  --el-segmented-bg-color: rgba(7, 15, 26, 0.7);
  --el-segmented-item-selected-bg-color: rgba(59, 130, 246, 0.28);
  --el-segmented-item-selected-color: #eaf4ff;
  --el-segmented-item-hover-bg-color: rgba(96, 165, 250, 0.16);
  --el-segmented-item-hover-color: #dbeafe;
  border: 1px solid rgba(72, 96, 130, 0.72);
  border-radius: 8px;
  padding: 2px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.device-trend-panel__tab-switcher :deep(.el-segmented__group) {
  flex-wrap: nowrap;
}

.device-trend-panel__tab-switcher :deep(.el-segmented__item) {
  color: #9fb1ca;
  border-radius: 6px;
}

.device-trend-panel__tab-switcher :deep(.el-segmented__item-selected) {
  box-shadow: 0 0 0 1px rgba(96, 165, 250, 0.35);
}

.device-trend-panel__range-picker {
  flex: 0 1 420px;
  min-width: min(100%, 320px);
}

.device-trend-panel__range-picker :deep(.el-date-editor) {
  width: 100%;
}

.device-trend-panel__range-picker :deep(.el-input__wrapper),
.device-trend-panel__range-picker :deep(.el-date-editor.el-input__wrapper) {
  background: rgba(7, 15, 26, 0.72);
  border: 1px solid rgba(72, 96, 130, 0.72);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.device-trend-panel__range-picker :deep(.el-range-input),
.device-trend-panel__range-picker :deep(.el-range-separator) {
  color: #dbeafe;
}

.device-trend-panel__range-picker :deep(.el-range__icon) {
  color: #7f93b2;
}

.device-trend-panel__summary {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin: 14px 0 8px;
  color: #cad6eb;
  font-size: 13px;
}

.device-trend-panel__empty {
  padding: 32px 16px;
  color: #8ea0bc;
  text-align: center;
  border: 1px dashed #2f3d52;
  border-radius: 8px;
}

.device-trend-panel__chart {
  height: 300px;
  min-width: 0;
}

@media (max-width: 1360px) {
  .device-trend-panel__toolbar {
    justify-content: flex-start;
  }

  .device-trend-panel__tab-switcher,
  .device-trend-panel__range-picker {
    flex-basis: 100%;
  }

  .device-trend-panel__range-picker {
    min-width: 0;
  }
}

@media (max-width: 900px) {
  .device-trend-panel {
    padding: 16px;
  }

  .device-trend-panel__chart {
    height: 280px;
  }
}
</style>
