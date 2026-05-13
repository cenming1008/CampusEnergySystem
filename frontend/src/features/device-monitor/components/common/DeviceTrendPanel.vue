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

function displayNumber(value?: number | null) {
  if (value === null || value === undefined) return '--'
  return Number(value).toFixed(1)
}
</script>

<template>
  <MonitorSectionPanel
    title="历史趋势"
    subtitle="按时间范围查看设备实时曲线"
  >
    <template #headerExtra>
      <div
        v-if="options.length > 0"
        class="device-trend-panel__toolbar"
      >
        <el-radio-group
          :model-value="modelValue"
          size="small"
          @update:model-value="$emit('update:modelValue', $event)"
        >
          <el-radio-button
            v-for="item in options"
            :key="item.value"
            :value="item.value"
          >
            {{ item.label }}
          </el-radio-button>
        </el-radio-group>
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
    </template>
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
  </MonitorSectionPanel>
</template>

<style scoped>
.device-trend-panel__toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.device-trend-panel__summary {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  color: #9fb1ca;
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
</style>
