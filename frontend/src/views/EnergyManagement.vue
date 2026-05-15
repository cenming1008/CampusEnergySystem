<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getCarbonEmissions,
  getEnergyTypes,
  getEnergyData,
  getEnergyOverview,
  getCarbonFactors,
  calculateCarbon,
  saveEnergyData,
  type AnalysisAnomalyItem,
  type AnalysisDeviceRankingItem,
  type AnalysisEnergyCategoryComparisonItem,
  type AnalysisInsightItem,
  type AnalysisLocationRankingItem,
  type AnalysisSubItemComparisonItem,
  type AnalysisTrendItem,
  type CarbonEmission,
  type EnergyData,
  type EnergyTypeInfo,
  type EnergyStatistics,
  type CarbonSummary,
  type CarbonFactor,
  type EnergyOverview
} from '@/api/energy'
import { getDevices, type Device } from '@/api/device'
import { isDemoSuppressed } from '@/shared/demoMode'
import { useAuthStore } from '@/stores/useAuthStore'
import { usePermissions } from '@/shared/composables/usePermissions'
import EnergyDataEntryTab from '@/features/energy-management/components/EnergyDataEntryTab.vue'
import EnergyEntryDialog from '@/features/energy-management/components/EnergyEntryDialog.vue'
import EnergyHeaderControls from '@/features/energy-management/components/EnergyHeaderControls.vue'
import EnergyOverviewTab from '@/features/energy-management/components/EnergyOverviewTab.vue'
import EnergyRankingAnomalyTab from '@/features/energy-management/components/EnergyRankingAnomalyTab.vue'
import EnergyTrendComparisonTab from '@/features/energy-management/components/EnergyTrendComparisonTab.vue'
import '@/features/energy-management/energyManagement.css'
import { formatBooleanRule, formatMetricValue } from '@/features/energy-management/formatters'
import {
  buildEnergyMixItems,
  normalizeEnergyCategoryComparison,
  normalizeInsightItems,
  normalizeTrendItems,
  typeColor,
  hasSteamRuntimePresence as resolveSteamRuntimePresence,
} from '@/features/energy-management/energyDisplay'
import {
  FALLBACK_CARBON_FACTORS,
  FALLBACK_ENERGY_DEVICES,
  FALLBACK_ENERGY_OVERVIEW,
  FALLBACK_ENERGY_TYPES,
} from '@/features/energy-management/mockFallback'

// ==================== 状态定义 ====================

const trendGranularity = ref<'hour' | 'day'>('day')
const rankingTopN = ref(5)

const energyTypes = ref<EnergyTypeInfo[]>([])
const selectedEnergyType = ref<string>('electricity')
const deviceList = ref<Device[]>([])
const dateRange = ref<[Date, Date]>([
  new Date(new Date().getTime() - 7 * 24 * 3600 * 1000),
  new Date()
])

const statistics = ref<{ [key: string]: EnergyStatistics }>({})
const overviewMeta = ref<EnergyOverview | null>(null)
const carbonSummary = ref<CarbonSummary | null>(null)
const carbonFactors = ref<Record<string, CarbonFactor>>({})
const loading = ref(false)
const demoMode = ref(false)
const hasRealOverview = ref(false)
const hasRealDevices = ref(false)
const detailLoading = ref(false)
const detailDeviceId = ref<number | undefined>(undefined)
const energyDetails = ref<EnergyData[]>([])
const carbonDetails = ref<CarbonEmission[]>([])
const entryDialogVisible = ref(false)
const authStore = useAuthStore()
const { hasScopedAccess } = usePermissions()

interface CarbonCalculationResult {
  energy_type: string
  consumption: number
  consumption_unit: string
  carbon_factor: number
  carbon_emission: number
  emission_unit: string
}

let refreshTimer: ReturnType<typeof setTimeout> | null = null
const secondaryPanelActive = ref<string[]>([])

const carbonCalculator = ref({
  energy_type: 'electricity',
  consumption: 0,
  result: null as CarbonCalculationResult | null
})

const entryForm = ref({
  device_id: undefined as number | undefined,
  energy_type: 'electricity',
  consumption: 0,
  flow_rate: 0,
  timestamp: '',
})

// ==================== 计算属性 ====================

const formatDateRange = computed(() => {
  if (!dateRange.value) return ['', '']

  const formatLocalDateTime = (date: Date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
  }

  const startDate = new Date(dateRange.value[0])
  startDate.setHours(0, 0, 0, 0)

  const endDate = new Date(dateRange.value[1])
  endDate.setHours(23, 59, 59, 999)

  return [formatLocalDateTime(startDate), formatLocalDateTime(endDate)]
})

const currentStats = computed(() => {
  return statistics.value[selectedEnergyType.value] || {
    total_consumption: 0,
    avg_consumption: 0,
    avg_flow_rate: 0,
    peak_flow_rate: 0,
    data_count: 0
  }
})

const currentEnergyInfo = computed(() => {
  return energyTypes.value.find(t => t.value === selectedEnergyType.value) || {
    value: '',
    label: '',
    unit: ''
  }
})

const hasSteamRuntimePresence = computed(() => {
  return resolveSteamRuntimePresence(statistics.value, deviceList.value, carbonSummary.value)
})

const visibleEnergyTypes = computed(() => {
  return energyTypes.value.filter((type) => type.value !== 'steam' || hasSteamRuntimePresence.value)
})

const visibleDeviceCount = computed(() => deviceList.value.length)
const detailDeviceName = computed(() => {
  if (!detailDeviceId.value) return '全部设备'
  return deviceList.value.find((item) => item.id === detailDeviceId.value)?.name || `设备 ${detailDeviceId.value}`
})

const activeEnergyCount = computed(() => {
  return visibleEnergyTypes.value.filter((type) => {
    const stats = statistics.value[type.value]
    const carbon = carbonSummary.value?.by_energy_type?.[type.value]
    return Boolean(
      stats && (
        stats.data_count > 0 ||
        stats.total_consumption > 0 ||
        stats.avg_flow_rate > 0 ||
        stats.peak_flow_rate > 0
      )
    ) || Boolean(carbon && (carbon.energy_consumption > 0 || carbon.carbon_emission > 0))
  }).length
})

const currentRangeLabel = computed(() => {
  if (!dateRange.value?.length) return '最近 7 天'
  const [start, end] = dateRange.value
  const format = (date: Date) => `${date.getMonth() + 1}/${date.getDate()}`
  return `${format(start)} – ${format(end)}`
})

const locationScopeHint = computed(() => {
  return authStore.locationScope ? `当前账号范围：${authStore.locationScope}` : ''
})

const totalEnergyConsumption = computed(() => {
  return visibleEnergyTypes.value.reduce((sum, type) => {
    return sum + (statistics.value[type.value]?.total_consumption || 0)
  }, 0)
})

const energyMixItems = computed(() => {
  return buildEnergyMixItems(visibleEnergyTypes.value, statistics.value)
})

const selectedEnergyShare = computed(() => {
  if (totalEnergyConsumption.value <= 0) return 0
  return (currentStats.value.total_consumption / totalEnergyConsumption.value) * 100
})

const overviewMetrics = computed(() => [
  {
    label: '活跃能源',
    value: String(activeEnergyCount.value),
    unit: '类',
    accent: 'kpi-tile--energy',
  },
  {
    label: '总能耗汇总',
    value: formatMetricValue(totalEnergyConsumption.value, 2),
    unit: currentEnergyInfo.value.unit || 'kWh',
    accent: 'kpi-tile--load',
  },
  {
    label: '总碳排',
    value: formatMetricValue(carbonSummary.value?.total_carbon || 0, 2),
    unit: 'kg CO₂',
    accent: 'kpi-tile--carbon',
  },
  {
    label: '设备入口',
    value: String(visibleDeviceCount.value),
    unit: '台',
    accent: 'kpi-tile--device',
  },
  {
    label: '焦点占比',
    value: `${selectedEnergyShare.value.toFixed(1)}%`,
    unit: '',
    accent: 'kpi-tile--focus',
  },
])

const focusHighlights = computed(() => [
  {
    label: '焦点占比',
    value: `${selectedEnergyShare.value.toFixed(1)}%`,
  },
  {
    label: '峰值流量',
    value: `${formatMetricValue(currentStats.value.peak_flow_rate, 2)} ${currentEnergyInfo.value.flow_unit || currentEnergyInfo.value.unit || ''}`.trim(),
  },
  {
    label: '采样条数',
    value: `${currentStats.value.data_count} 条`,
  },
])

const carbonMetaItems = computed(() => {
  if (!carbonSummary.value) return []
  return [
    { label: '碳汇总边界', value: carbonSummary.value.boundary || '未声明' },
    { label: '计算方法', value: carbonSummary.value.calculation_method || '未声明' },
    { label: '汇总依据', value: carbonSummary.value.summary_basis || '未声明' },
    { label: '核算等级', value: carbonSummary.value.is_accounting_grade ? '正式核算' : '展示估算' },
    { label: '说明', value: carbonSummary.value.note || '未声明' },
  ]
})

const secondaryOverviewItems = computed(() => {
  const meta = overviewMeta.value
  if (!meta) return []
  return [
    { label: '总览边界', value: meta.overview_boundary || '未声明' },
    { label: '统计口径', value: meta.unit_rule || '未声明' },
    { label: '跨能源混算', value: formatBooleanRule(meta.cross_energy_mix_allowed) },
    { label: '字段边界', value: meta.field_boundary_rule || '未声明' },
    { label: '累计量语义', value: currentStats.value.consumption_semantics || currentEnergyInfo.value.consumption_semantics || '未声明' },
    { label: '瞬时量语义', value: currentStats.value.flow_semantics || currentEnergyInfo.value.flow_semantics || '未声明' },
  ]
})

// ==================== 分析字段（趋势/对比/排行/异常/洞察） ====================

const analysisTimeWindow = computed(() => overviewMeta.value?.time_window ?? null)
const analysisSummary = computed(() => overviewMeta.value?.summary ?? null)
const analysisTrend = computed(() => overviewMeta.value?.trend ?? null)
const analysisComparison = computed(() => overviewMeta.value?.comparison ?? null)
const analysisRanking = computed(() => overviewMeta.value?.ranking ?? null)
const analysisAnomaly = computed(() => overviewMeta.value?.anomaly ?? null)

const trendItems = computed<AnalysisTrendItem[]>(() => normalizeTrendItems(overviewMeta.value))
const periodComparison = computed(() => {
  const comparison = analysisComparison.value
  if (!comparison) return null
  return comparison.period_over_period ?? {
    current_total_consumption: comparison.current ?? 0,
    previous_total_consumption: comparison.previous ?? 0,
    delta_consumption: (comparison.current ?? 0) - (comparison.previous ?? 0),
    change_rate: comparison.ratio ?? null,
    consumption_stat_basis: 'period_delta_from_cumulative_reading',
  }
})
const energyCategoryComparison = computed<AnalysisEnergyCategoryComparisonItem[]>(() => {
  return normalizeEnergyCategoryComparison(overviewMeta.value, energyTypes.value)
})
const subItemComparison = computed<AnalysisSubItemComparisonItem[]>(() => analysisComparison.value?.sub_items ?? [])
const areaRanking = computed<AnalysisLocationRankingItem[]>(() => analysisRanking.value?.regions ?? analysisRanking.value?.areas ?? [])
const buildingRanking = computed<AnalysisLocationRankingItem[]>(() => analysisRanking.value?.buildings ?? [])
const deviceRanking = computed<AnalysisDeviceRankingItem[]>(() => analysisRanking.value?.devices ?? [])
const anomalyItems = computed<AnalysisAnomalyItem[]>(() => analysisAnomaly.value?.items ?? [])
const insightItems = computed<AnalysisInsightItem[]>(() => normalizeInsightItems(overviewMeta.value))

const statBasisText = computed(() => {
  const basis =
    analysisSummary.value?.consumption_stat_basis ||
    analysisTrend.value?.consumption_stat_basis ||
    periodComparison.value?.consumption_stat_basis
  if (!basis) return '统计口径待确认'
  if (basis === 'period_delta_from_cumulative_reading') {
    return '周期能耗按累计读数差值统计'
  }
  return basis
})

// ==================== 数据加载 ====================

const loadEnergyTypes = async () => {
  try {
    const res = await getEnergyTypes({ silent: true })
    energyTypes.value = res.energy_types
    if (energyTypes.value.length > 0 && !selectedEnergyType.value) {
      selectedEnergyType.value = energyTypes.value[0].value
    }
  } catch {
    energyTypes.value = isDemoSuppressed() ? [] : FALLBACK_ENERGY_TYPES
    if (!selectedEnergyType.value) selectedEnergyType.value = energyTypes.value[0]?.value || 'electricity'
  }
}

const loadDevices = async () => {
  try {
    const devices = await getDevices({ silent: true })
    deviceList.value = devices
    hasRealDevices.value = devices.length > 0
  } catch {
    deviceList.value = []
    hasRealDevices.value = false
  }
}

const loadCarbonFactors = async () => {
  try {
    const res = await getCarbonFactors({ silent: true })
    carbonFactors.value = res.carbon_factors
  } catch {
    carbonFactors.value = isDemoSuppressed() ? {} : FALLBACK_CARBON_FACTORS
  }
}

function applyEnergyDemoFallback() {
  if (isDemoSuppressed()) {
    demoMode.value = false
    return
  }
  demoMode.value = true
  energyTypes.value = FALLBACK_ENERGY_TYPES
  deviceList.value = FALLBACK_ENERGY_DEVICES
  overviewMeta.value = FALLBACK_ENERGY_OVERVIEW
  statistics.value = FALLBACK_ENERGY_OVERVIEW.statistics
  carbonSummary.value = FALLBACK_ENERGY_OVERVIEW.carbon_summary
  carbonFactors.value = FALLBACK_CARBON_FACTORS
  if (!FALLBACK_ENERGY_TYPES.some((type) => type.value === selectedEnergyType.value)) {
    selectedEnergyType.value = FALLBACK_ENERGY_TYPES[0]?.value || 'electricity'
  }
}

const loadOverview = async () => {
  loading.value = true
  try {
    const [startTime, endTime] = formatDateRange.value
    if (!startTime || !endTime) {
      ElMessage.error('时间参数无效')
      return
    }
    const overview = await getEnergyOverview({
      start_time: startTime,
      end_time: endTime,
      device_id: detailDeviceId.value,
      energy_type: selectedEnergyType.value,
      top_n: rankingTopN.value,
      granularity: trendGranularity.value,
      include_analysis: true,
    }, { silent: true })
    overviewMeta.value = overview
    statistics.value = overview.statistics
    carbonSummary.value = overview.carbon_summary
    hasRealOverview.value = Object.values(overview.statistics || {}).some((item) => (
      item.total_consumption > 0 || item.avg_flow_rate > 0 || item.data_count > 0
    ))
    if (hasRealOverview.value) demoMode.value = false
  } catch {
    hasRealOverview.value = false
    if (!demoMode.value) {
      overviewMeta.value = null
      statistics.value = {}
      carbonSummary.value = null
    }
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  try {
    await Promise.all([loadOverview(), loadDetailData()])
  } catch {
    // 刷新时部分失败由各子函数处理
  }
}

const loadDetailData = async () => {
  const [startTime, endTime] = formatDateRange.value
  if (!startTime || !endTime) return

  if (!detailDeviceId.value) {
    energyDetails.value = []
    carbonDetails.value = []
    return
  }

  detailLoading.value = true
  try {
    energyDetails.value = await getEnergyData({
      device_id: detailDeviceId.value,
      energy_type: selectedEnergyType.value,
      start_time: startTime,
      end_time: endTime,
      limit: 50
    }, { silent: true })
    carbonDetails.value = await getCarbonEmissions({
      device_id: detailDeviceId.value,
      energy_type: selectedEnergyType.value,
      start_time: startTime,
      end_time: endTime,
      limit: 100
    }, { silent: true })
  } catch {
    energyDetails.value = []
    carbonDetails.value = []
  } finally {
    detailLoading.value = false
  }
}

// ==================== 碳排放计算器 ====================

const handleCalculateCarbon = async () => {
  try {
    const res = await calculateCarbon({
      energy_type: carbonCalculator.value.energy_type,
      consumption: carbonCalculator.value.consumption
    })
    carbonCalculator.value.result = res
    ElMessage.success('计算完成')
  } catch {
    ElMessage.error('计算失败')
  }
}

const openEntryDialog = () => {
  entryForm.value = {
    device_id: detailDeviceId.value,
    energy_type: selectedEnergyType.value,
    consumption: 0,
    flow_rate: 0,
    timestamp: new Date().toISOString().slice(0, 19),
  }
  entryDialogVisible.value = true
}

const handleSaveEntry = async () => {
  if (entryForm.value.device_id == null) {
    ElMessage.warning('请选择要补录的设备')
    return
  }
  try {
    await saveEnergyData({
      device_id: entryForm.value.device_id,
      energy_type: entryForm.value.energy_type,
      consumption: entryForm.value.consumption,
      flow_rate: entryForm.value.flow_rate,
      timestamp: entryForm.value.timestamp
    })
    ElMessage.success('补录成功')
    entryDialogVisible.value = false
    await refreshData()
  } catch {
    ElMessage.error('补录失败')
  }
}

// ==================== 生命周期 ====================

onMounted(async () => {
  await loadEnergyTypes()
  await loadDevices()
  await loadCarbonFactors()
  await refreshData()
  if (!isDemoSuppressed() && !hasRealOverview.value && !hasRealDevices.value) {
    applyEnergyDemoFallback()
  }
})

watch(selectedEnergyType, () => { refreshData() })

watch(visibleEnergyTypes, (types) => {
  if (!types.length) return
  if (!types.some((item) => item.value === selectedEnergyType.value)) {
    selectedEnergyType.value = types[0].value
  }
  if (!types.some((item) => item.value === carbonCalculator.value.energy_type)) {
    carbonCalculator.value.energy_type = types[0].value
  }
  if (!types.some((item) => item.value === entryForm.value.energy_type)) {
    entryForm.value.energy_type = types[0].value
  }
}, { immediate: true })

watch(dateRange, () => {
  if (refreshTimer) clearTimeout(refreshTimer)
  refreshTimer = setTimeout(() => { refreshData() }, 250)
})

watch(detailDeviceId, () => { refreshData() })

watch([rankingTopN, trendGranularity], () => { loadOverview() })

</script>

<template>
  <div class="em-page">
    <div class="em-noise" />

    <header class="em-header glass-card">
      <div class="em-brand-block">
        <div class="em-brand-mark">
          <span class="em-brand-mark__dot" />
        </div>
        <div class="em-header__brand">
          <p class="eyebrow">Campus Energy Center</p>
          <h1>能源管理中心</h1>
          <p class="em-header__subtitle">按能源介质、设备和统计窗口查看能耗、碳排与运营信号。</p>
          <div class="em-header__tags">
            <span class="hdr-tag">{{ currentRangeLabel }}</span>
            <span class="hdr-tag hdr-tag--cyan">{{ activeEnergyCount }} 类活跃</span>
            <span v-if="hasScopedAccess" class="hdr-tag hdr-tag--amber">{{ locationScopeHint || '范围受限' }}</span>
          </div>
        </div>
      </div>
      <EnergyHeaderControls
        v-model:detail-device-id="detailDeviceId"
        v-model:date-range="dateRange"
        v-model:trend-granularity="trendGranularity"
        :device-list="deviceList"
        :loading="loading"
        @refresh="refreshData"
      />
    </header>

    <div class="energy-rail">
      <button
        v-for="type in visibleEnergyTypes"
        :key="type.value"
        class="energy-chip"
        :class="{ active: selectedEnergyType === type.value }"
        :style="{
          '--chip-color': typeColor(type.value),
          ...(selectedEnergyType === type.value ? {
            borderColor: typeColor(type.value) + '55',
            background: typeColor(type.value) + '18',
            color: typeColor(type.value)
          } : {})
        }"
        @click="selectedEnergyType = type.value"
      >
        <span
          class="chip-dot"
          :style="{
            background: typeColor(type.value),
            boxShadow: selectedEnergyType === type.value ? `0 0 8px ${typeColor(type.value)}88` : 'none'
          }"
        />
        <span class="chip-label">{{ type.label }}</span>
        <span class="chip-val">
          {{ (statistics[type.value]?.total_consumption || 0).toFixed(1) }}<em> {{ type.unit }}</em>
        </span>
      </button>
    </div>

    <EnergyOverviewTab
      :overview-metrics="overviewMetrics"
      :total-energy-consumption="totalEnergyConsumption"
      :energy-mix-items="energyMixItems"
      :visible-energy-types="visibleEnergyTypes"
      :statistics="statistics"
      :carbon-summary="carbonSummary"
      :has-steam-runtime-presence="hasSteamRuntimePresence"
      :current-energy-info="currentEnergyInfo"
      :current-stats="currentStats"
      :focus-highlights="focusHighlights"
      :detail-device-id="detailDeviceId"
      :detail-device-name="detailDeviceName"
      @refresh-detail="loadDetailData"
      @clear-device="detailDeviceId = undefined"
    >
      <template #center>
        <EnergyTrendComparisonTab
          :granularity="analysisTimeWindow?.granularity || trendGranularity"
          :trend-items="trendItems"
          :period-comparison="periodComparison"
          :energy-category-comparison="energyCategoryComparison"
          :sub-item-comparison="subItemComparison"
          :stat-basis-text="statBasisText"
        />
      </template>
    </EnergyOverviewTab>

    <el-collapse v-model="secondaryPanelActive" class="em-collapse em-secondary-accordion">
      <el-collapse-item name="ranking" title="排行与异常">
        <EnergyRankingAnomalyTab
          v-model:ranking-top-n="rankingTopN"
          :area-ranking="areaRanking"
          :building-ranking="buildingRanking"
          :device-ranking="deviceRanking"
          :analysis-anomaly="analysisAnomaly"
          :anomaly-items="anomalyItems"
          :insight-items="insightItems"
        />
      </el-collapse-item>

      <el-collapse-item name="entry" title="数据录入">
        <EnergyDataEntryTab
          :visible-energy-types="visibleEnergyTypes"
          :carbon-factors="carbonFactors"
          :carbon-calculator="carbonCalculator"
          :detail-device-id="detailDeviceId"
          :detail-loading="detailLoading"
          :detail-device-name="detailDeviceName"
          :energy-details="energyDetails"
          :carbon-details="carbonDetails"
          @open-entry="openEntryDialog"
          @calculate-carbon="handleCalculateCarbon"
        />
      </el-collapse-item>

      <el-collapse-item name="summary-rules" title="统计口径与边界">
        <div class="glass-card collapse-panel">
          <div class="info-list">
            <div v-for="item in secondaryOverviewItems" :key="item.label" class="info-item">
              <span class="info-label">{{ item.label }}</span>
              <span class="info-value">{{ item.value }}</span>
            </div>
          </div>
        </div>
      </el-collapse-item>

      <el-collapse-item name="carbon-rules" title="碳排放说明">
        <div class="glass-card collapse-panel">
          <div class="info-list">
            <div v-for="item in carbonMetaItems" :key="item.label" class="info-item">
              <span class="info-label">{{ item.label }}</span>
              <span class="info-value">{{ item.value }}</span>
            </div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>

    <EnergyEntryDialog
      v-model:visible="entryDialogVisible"
      :form="entryForm"
      :device-list="deviceList"
      :visible-energy-types="visibleEnergyTypes"
      @submit="handleSaveEntry"
    />
  </div>
</template>
