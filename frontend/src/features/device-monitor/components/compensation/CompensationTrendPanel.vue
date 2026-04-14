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
        text: props.model.emptyText,
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
      top: 6,
      right: 16,
      textStyle: { color: '#8ea0bc' },
      data: props.model.legend,
    },
    grid: { left: 56, right: 48, top: 48, bottom: 30 },
    xAxis: {
      type: 'category',
      data: props.model.labels,
      axisLine: { lineStyle: { color: '#314055' } },
      axisLabel: { color: '#8ea0bc', fontSize: 11 },
    },
    yAxis: props.model.axes.map((axis, index) => ({
      type: 'value',
      name: axis.name,
      position: axis.position || (index === 1 ? 'right' : 'left'),
      min: axis.min,
      max: axis.max,
      nameTextStyle: { color: '#8ea0bc', padding: [0, 0, 0, 6] },
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

watch(() => props.model, () => {
  void renderChart()
}, { deep: true })

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
      <div>
        <h3>历史趋势</h3>
        <span>{{ model.hint || '默认围绕补偿效果展示，支持时间范围切换' }}</span>
      </div>
      <div class="trend-panel__toolbar">
        <el-segmented
          :model-value="activeTab"
          :options="segmentedOptions"
          size="small"
          @change="$emit('update:activeTab', $event as CompensationTrendTab)"
        />
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
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
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
  justify-content: flex-end;
  gap: 10px;
}

.trend-panel__summary {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 14px 0 12px;
  color: #cad6eb;
  font-size: 12px;
}

.trend-panel__chart {
  width: 100%;
  height: 360px;
}

@media (max-width: 1360px) {
  .trend-panel__head {
    flex-direction: column;
  }

  .trend-panel__toolbar {
    justify-content: flex-start;
  }
}
</style>
