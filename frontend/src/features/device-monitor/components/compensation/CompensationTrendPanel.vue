<script setup lang="ts">
import { computed, watch } from 'vue'
import { useECharts } from '@/shared/composables/useECharts'
import type { PropType } from 'vue'
import type {
  CompensationTrendModel,
  CompensationTrendOption,
  CompensationTrendTab,
} from './types'

const props = defineProps({
  tabs: {
    type: Array as PropType<CompensationTrendOption[]>,
    default: () => [],
  },
  activeTab: {
    type: String as PropType<CompensationTrendTab>,
    required: true,
  },
  model: {
    type: Object as PropType<CompensationTrendModel>,
    required: true,
  },
  timeRange: {
    type: Array as unknown as PropType<[Date, Date] | null>,
    default: null,
  },
  shortcuts: {
    type: Array as PropType<Array<{ text: string; value: () => [Date, Date] }>>,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits<{
  'update:activeTab': [value: CompensationTrendTab]
  'update:timeRange': [value: [Date, Date] | null]
  'range-change': []
}>()

const chart = useECharts()

const segmentedOptions = computed(() =>
  props.tabs.map((tab) => ({ label: tab.label, value: tab.value })),
)

async function renderChart() {
  if (props.model.empty) {
    await chart.setOptions({
      title: {
        text: '',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#7f93b2',
          fontSize: 15,
          fontWeight: 400,
        },
      },
      xAxis: { show: false, type: 'category', data: [] },
      yAxis: { show: false, type: 'value' },
      series: [],
    }, { notMerge: true })
    return
  }

  await chart.setOptions({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(11, 19, 30, 0.96)',
      borderColor: '#314055',
      textStyle: { color: '#dfe8f5' },
    },
    legend: {
      show: false,
    },
    grid: { left: 56, right: 56, top: 30, bottom: 30 },
    xAxis: {
      type: props.model.xAxisType || 'category',
      data: props.model.xAxisType === 'time' ? undefined : props.model.labels,
      min: props.model.xAxisType === 'time' ? props.model.xAxisMin : undefined,
      max: props.model.xAxisType === 'time' ? props.model.xAxisMax : undefined,
      axisLine: { lineStyle: { color: '#314055' } },
      axisLabel: {
        color: '#8ea0bc',
        fontSize: 11,
        formatter: props.model.xAxisType === 'time'
          ? (value: number) => formatTimeAxisLabel(value, props.model.xAxisMin, props.model.xAxisMax)
          : undefined,
      },
    } as any,
    yAxis: props.model.axes.map((axis, index) => ({
      type: 'value',
      name: axis.name,
      position: axis.position || (index === 1 ? 'right' : 'left'),
      min: axis.min,
      max: axis.max,
      nameGap: 10,
      nameTextStyle: {
        color: '#8ea0bc',
        padding: (axis.position || (index === 1 ? 'right' : 'left')) === 'right' ? [0, 0, 0, 0] : [0, 0, 0, 6],
      },
      axisLabel: { color: '#8ea0bc', fontSize: 11 },
      splitLine: {
        lineStyle: {
          color: index === 0 ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0)',
        },
      },
    })),
    series: props.model.series.map((series) => ({
      name: series.name,
      type: 'line',
      smooth: true,
      showSymbol: false,
      yAxisIndex: series.yAxisIndex || 0,
      data: series.data,
      lineStyle: { color: series.color, width: 2.6 },
      itemStyle: { color: series.color },
      areaStyle: series.area
        ? {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: `${series.color}55` },
                { offset: 1, color: `${series.color}00` },
              ],
            },
          }
        : undefined,
    })),
  }, { notMerge: true })
}

function formatTimeAxisLabel(value: number, min?: string, max?: string) {
  const date = new Date(value)
  const start = min ? new Date(min) : null
  const end = max ? new Date(max) : null
  const crossesDay = start && end
    ? start.getFullYear() !== end.getFullYear()
      || start.getMonth() !== end.getMonth()
      || start.getDate() !== end.getDate()
    : false

  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  const hours = `${date.getHours()}`.padStart(2, '0')
  const minutes = `${date.getMinutes()}`.padStart(2, '0')
  return crossesDay ? `${month}/${day} ${hours}:${minutes}` : `${hours}:${minutes}`
}

watch(() => props.model, () => {
  void renderChart()
})

watch(() => props.activeTab, () => {
  void renderChart()
})

watch(() => chart.chartRef.value, async () => {
  if (!chart.chartRef.value) return
  await chart.initChart()
  await renderChart()
})
</script>

<template>
  <section class="trend-panel">
    <div class="trend-panel__head">
      <div class="trend-panel__intro">
        <h3>历史趋势</h3>
        <span v-if="model.hint">{{ model.hint }}</span>
      </div>
      <div class="trend-panel__toolbar">
        <div class="trend-panel__tab-wrapper">
          <div class="trend-panel__tab-switcher">
            <el-segmented
              :model-value="activeTab"
              :options="segmentedOptions"
              size="small"
              @change="$emit('update:activeTab', $event as CompensationTrendTab)"
            />
          </div>
        </div>
        <div class="trend-panel__range-picker">
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

    <div class="trend-panel__summary">
      <span
        v-for="item in model.summary"
        :key="item.label"
      >
        {{ item.label }} {{ item.value }}
      </span>
      <el-tag
        v-if="model.isMock"
        size="small"
        type="warning"
        effect="plain"
      >
        演示占位
      </el-tag>
    </div>

    <div
      v-if="model.legend.length"
      class="trend-panel__legend"
    >
      <span
        v-for="(item, index) in model.legend"
        :key="item"
        class="trend-panel__legend-item"
      >
        <i :style="{ background: model.series[index]?.color || '#8ea0bc' }" />
        {{ item }}
      </span>
    </div>

    <div
      :ref="chart.chartRef"
      v-loading="loading"
      class="trend-panel__chart"
    />
  </section>
</template>

<style scoped>
.trend-panel {
  padding: 18px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.trend-panel__head {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.trend-panel__intro {
  min-width: 0;
}

.trend-panel__head h3 {
  margin: 0;
  font-size: 16px;
  color: #f5f7fb;
}

.trend-panel__head span {
  display: block;
  margin-top: 5px;
  font-size: 12px;
  color: #8ea0bc;
}

.trend-panel__toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  width: 100%;
  min-width: 0;
}

.trend-panel__tab-wrapper {
  flex: 0 1 auto;
  min-width: 0;
  position: relative;
}

.trend-panel__tab-switcher {
  overflow-x: auto;
  padding-bottom: 2px;
  scrollbar-width: none;
}

.trend-panel__tab-switcher::-webkit-scrollbar {
  display: none;
}

.trend-panel__tab-switcher :deep(.el-segmented) {
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

.trend-panel__tab-switcher :deep(.el-segmented__group) {
  flex-wrap: nowrap;
}

.trend-panel__tab-switcher :deep(.el-segmented__item) {
  color: #9fb1ca;
  border-radius: 6px;
}

.trend-panel__tab-switcher :deep(.el-segmented__item-selected) {
  box-shadow: 0 0 0 1px rgba(96, 165, 250, 0.35);
}

.trend-panel__range-picker {
  flex: 0 1 420px;
  min-width: min(100%, 320px);
}

.trend-panel__range-picker :deep(.el-date-editor) {
  width: 100%;
}

.trend-panel__range-picker :deep(.el-input__wrapper),
.trend-panel__range-picker :deep(.el-date-editor.el-input__wrapper) {
  background: rgba(7, 15, 26, 0.72);
  border: 1px solid rgba(72, 96, 130, 0.72);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.trend-panel__range-picker :deep(.el-range-input),
.trend-panel__range-picker :deep(.el-range-separator) {
  color: #dbeafe;
}

.trend-panel__range-picker :deep(.el-range__icon) {
  color: #7f93b2;
}

.trend-panel__summary {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 14px 0 8px;
  color: #cad6eb;
  font-size: 12px;
}

.trend-panel__legend {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 6px;
  color: #9fb1ca;
  font-size: 12px;
}

.trend-panel__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  line-height: 1;
}

.trend-panel__legend-item i {
  width: 18px;
  height: 3px;
  border-radius: 999px;
  box-shadow: 0 0 8px currentColor;
}

.trend-panel__chart {
  width: 100%;
  height: 360px;
}

@media (max-width: 1360px) {
  .trend-panel__toolbar {
    justify-content: flex-start;
  }

  .trend-panel__tab-switcher,
  .trend-panel__range-picker {
    flex-basis: 100%;
  }

  .trend-panel__range-picker {
    min-width: 0;
  }
}

@media (max-width: 900px) {
  .trend-panel {
    padding: 16px;
  }

  .trend-panel__chart {
    height: 320px;
  }
}
</style>
