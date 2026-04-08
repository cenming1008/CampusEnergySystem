<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  getAnalysisOverview,
  type AnalysisAnomalyItem,
  type AnalysisDeviceRankingItem,
  type AnalysisEnergyCategoryComparisonItem,
  type AnalysisInsightItem,
  type AnalysisLocationRankingItem,
  type AnalysisOverview,
  type AnalysisSubItemComparisonItem,
  type AnalysisTrendItem,
} from '@/api/analysis'

interface MetricCard {
  label: string
  value: string
  hint: string
}

interface ScopeCountItem {
  label: string
  value: number
}

const router = useRouter()
const loading = ref(false)
const loadError = ref('')
const overview = ref<AnalysisOverview | null>(null)

const energyLabels: Record<string, string> = {
  electric: '电力',
  electricity: '电力',
  water: '水务',
  gas: '燃气',
  cooling: '冷量',
  heating: '热力',
  steam: '蒸汽'
}

const locationTypeLabels: Record<string, string> = {
  park: '园区',
  campus: '园区',
  site: '园区',
  area: '区域',
  zone: '区域',
  building: '楼栋'
}

const severityLabels: Record<string, string> = {
  critical: '严重',
  warning: '提示',
  info: '信息'
}

const anomalyKindLabels: Record<string, string> = {
  data_gap: '接入断档',
  ingestion_failure: '连续失败',
  active_alarm: '未恢复告警'
}

function formatNumber(value: number | null | undefined, digits: number = 1) {
  if (value == null || Number.isNaN(value)) return '-'
  return Number(value).toFixed(digits)
}

function formatPercent(value: number | null | undefined, digits: number = 1) {
  if (value == null || Number.isNaN(value)) return '-'
  return `${(value * 100).toFixed(digits)}%`
}

function formatSignedPercent(value: number | null | undefined, digits: number = 1) {
  if (value == null || Number.isNaN(value)) return '暂无环比'
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${(value * 100).toFixed(digits)}%`
}

function formatTimestamp(value: string | null | undefined, granularity: string = 'day') {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return granularity === 'hour'
    ? date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
    : date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

function getEnergyLabel(value: string | null | undefined) {
  if (!value) return '未标记'
  return energyLabels[value] || value
}

function getLocationTypeLabel(value: string | null | undefined) {
  if (!value) return '全园区'
  return locationTypeLabels[value] || value
}

function getSeverityType(value: string) {
  if (value === 'critical') return 'danger'
  if (value === 'warning') return 'warning'
  return 'info'
}

function getAnomalyKindLabel(value: string) {
  return anomalyKindLabels[value] || value
}

function buildSparkline(values: number[]) {
  if (!values.length) return ''
  if (values.length === 1) return '0,32 100,32'

  const max = Math.max(...values)
  const min = Math.min(...values)
  const range = max - min || 1

  return values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * 100
      const y = 32 - ((value - min) / range) * 28
      return `${x},${y}`
    })
    .join(' ')
}

function extractErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message) return error.message
  return fallback
}

async function loadOverview() {
  loading.value = true
  loadError.value = ''
  try {
    overview.value = await getAnalysisOverview({ top_n: 5 })
  } catch (error) {
    overview.value = null
    loadError.value = extractErrorMessage(error, '能耗分析主页面数据加载失败')
  } finally {
    loading.value = false
  }
}

const timeWindow = computed(() => overview.value?.time_window ?? null)
const scope = computed(() => overview.value?.scope ?? null)
const summary = computed(() => overview.value?.summary ?? null)
const trend = computed(() => overview.value?.trend ?? null)
const comparison = computed(() => overview.value?.comparison ?? null)
const ranking = computed(() => overview.value?.ranking ?? null)
const anomaly = computed(() => overview.value?.anomaly ?? null)
const insights = computed(() => overview.value?.insights ?? [])

const onlineRate = computed(() => {
  if (!summary.value?.device_count) return null
  return summary.value.active_device_count / summary.value.device_count
})

const focusEnergy = computed<AnalysisEnergyCategoryComparisonItem | null>(() => {
  return comparison.value?.energy_categories?.[0] ?? null
})

const summaryCards = computed<MetricCard[]>(() => {
  if (!summary.value) return []
  return [
    {
      label: '周期能耗',
      value: formatNumber(summary.value.total_consumption, 1),
      hint: '按累计读数差值统计本周期总消耗'
    },
    {
      label: '平均负荷',
      value: formatNumber(summary.value.avg_load, 1),
      hint: '聚合窗口内的平均负荷水平'
    },
    {
      label: '接入设备',
      value: String(summary.value.device_count),
      hint: `${summary.value.active_device_count} 台在线，在线率 ${formatPercent(onlineRate.value)}`
    },
    {
      label: '覆盖介质',
      value: String(summary.value.covered_energy_type_count),
      hint: '已纳入电、水、气、冷、热等多能源视角'
    },
    {
      label: '分项覆盖',
      value: String(summary.value.covered_sub_item_count),
      hint: '当前可参与运营对比的分项对象数量'
    },
    {
      label: '运营信号',
      value: String(summary.value.anomaly_count),
      hint: '第一批异常边界：接入断档、连续失败、未恢复告警'
    }
  ]
})

const scopeCountItems = computed<ScopeCountItem[]>(() => {
  const counts = scope.value?.location_counts || {}
  return [
    { label: '园区节点', value: (counts.park || 0) + (counts.campus || 0) + (counts.site || 0) },
    { label: '区域节点', value: (counts.area || 0) + (counts.zone || 0) },
    { label: '楼栋节点', value: counts.building || 0 }
  ]
})

const periodComparison = computed(() => comparison.value?.period_over_period ?? null)
const trendItems = computed<AnalysisTrendItem[]>(() => trend.value?.items ?? [])
const trendConsumptionPolyline = computed(() => buildSparkline(trendItems.value.map((item) => item.total_consumption)))
const trendLoadPolyline = computed(() => buildSparkline(trendItems.value.map((item) => item.total_load)))
const areaRanking = computed<AnalysisLocationRankingItem[]>(() => ranking.value?.areas ?? [])
const buildingRanking = computed<AnalysisLocationRankingItem[]>(() => ranking.value?.buildings ?? [])
const deviceRanking = computed<AnalysisDeviceRankingItem[]>(() => ranking.value?.devices ?? [])
const anomalyItems = computed<AnalysisAnomalyItem[]>(() => anomaly.value?.items ?? [])
const subItemComparison = computed<AnalysisSubItemComparisonItem[]>(() => comparison.value?.sub_items ?? [])

const statBasisText = computed(() => {
  const basis = summary.value?.consumption_stat_basis || trend.value?.consumption_stat_basis || periodComparison.value?.consumption_stat_basis
  if (!basis) return '统计口径待确认'
  if (basis === 'period_delta_from_cumulative_reading') {
    return '周期能耗按累计读数差值统计（period_delta_from_cumulative_reading）'
  }
  return basis
})

const focusInsight = computed(() => {
  if (!focusEnergy.value) return '当前暂无主导能源'
  return `${focusEnergy.value.label} 占比 ${formatPercent(focusEnergy.value.ratio)}，当前是园区运营分析的主导能源。`
})

onMounted(() => {
  loadOverview()
})
</script>

<template>
  <div class="analysis-page">
    <section class="hero-section">
      <div class="hero-copy">
        <span class="hero-eyebrow">Campus Energy Analysis Center</span>
        <h1>能耗分析中心</h1>
        <p>
          面向园区运营侧统一查看趋势、对比、排行、异常与洞察。当前主页面已正式接入
          <code>/analysis/overview</code>，不再使用占位式样例数据。
        </p>
        <div class="hero-meta">
          <span>统计窗口：{{ formatTimestamp(timeWindow?.start_time, 'day') }} 至 {{ formatTimestamp(timeWindow?.end_time, 'day') }}</span>
          <span>粒度：{{ timeWindow?.granularity === 'hour' ? '小时' : '天' }}</span>
          <span>范围：{{ getLocationTypeLabel(scope?.location_type) }}</span>
        </div>
        <div class="hero-actions">
          <el-button
            type="primary"
            @click="router.push('/energy')"
          >
            查看区域 / 楼栋能耗
          </el-button>
          <el-button @click="router.push('/forecast-tools')">
            进入预测 / 模型工具
          </el-button>
        </div>
      </div>

      <div class="hero-focus">
        <div class="focus-label">
          当前能源焦点
        </div>
        <div class="focus-value">
          {{ focusEnergy?.label || '暂无主导项' }}
        </div>
        <div class="focus-meta">
          {{ focusInsight }}
        </div>

        <div class="focus-divider" />

        <div class="focus-snapshot">
          <span>周期能耗</span>
          <strong>{{ formatNumber(summary?.total_consumption, 1) }}</strong>
        </div>
        <div class="focus-snapshot">
          <span>环比变化</span>
          <strong>{{ formatSignedPercent(periodComparison?.change_rate) }}</strong>
        </div>
        <div class="focus-snapshot">
          <span>运营信号</span>
          <strong>{{ anomaly?.summary.total_count ?? 0 }} 项</strong>
        </div>
      </div>
    </section>

    <section
      v-if="summaryCards.length"
      class="metric-grid"
    >
      <article
        v-for="card in summaryCards"
        :key="card.label"
        class="metric-card"
      >
        <span class="metric-label">{{ card.label }}</span>
        <strong class="metric-value">{{ card.value }}</strong>
        <span class="metric-hint">{{ card.hint }}</span>
      </article>
    </section>

    <section class="content-grid">
      <div class="analysis-board">
        <article class="board-card board-card--hero">
          <div class="board-header">
            <div>
              <h3>趋势</h3>
              <p>主趋势位已切换到真实时序聚合，累计量展示遵循 {{ statBasisText }}。</p>
            </div>
            <el-tag
              type="info"
              effect="plain"
            >
              {{ timeWindow?.granularity === 'hour' ? '小时粒度' : '天粒度' }}
            </el-tag>
          </div>

          <div
            v-if="trendItems.length"
            class="trend-stage"
          >
            <div class="trend-chart-card">
              <div class="trend-chart-header">
                <span>周期能耗走势</span>
                <strong>{{ formatNumber(summary?.total_consumption, 1) }}</strong>
              </div>
              <svg
                viewBox="0 0 100 36"
                preserveAspectRatio="none"
                class="trend-chart"
              >
                <polyline
                  :points="trendConsumptionPolyline"
                  class="trend-line trend-line--consumption"
                />
              </svg>
              <div class="trend-footer">
                <span>峰值时点</span>
                <strong>{{ formatTimestamp(trend?.peak_consumption?.timestamp, timeWindow?.granularity) }}</strong>
              </div>
            </div>

            <div class="trend-chart-card">
              <div class="trend-chart-header">
                <span>负荷走势</span>
                <strong>{{ formatNumber(summary?.avg_load, 1) }}</strong>
              </div>
              <svg
                viewBox="0 0 100 36"
                preserveAspectRatio="none"
                class="trend-chart"
              >
                <polyline
                  :points="trendLoadPolyline"
                  class="trend-line trend-line--load"
                />
              </svg>
              <div class="trend-footer">
                <span>峰值负荷</span>
                <strong>{{ formatNumber(trend?.peak_load?.total_load, 1) }}</strong>
              </div>
            </div>
          </div>
          <el-empty
            v-else
            description="当前统计窗口暂无趋势数据"
          />
        </article>

        <article class="board-card">
          <div class="board-header">
            <div>
              <h3>对比</h3>
              <p>对比位已切到真实聚合结果，不直接把累计读数求和误展示成周期能耗。</p>
            </div>
          </div>

          <div
            v-if="periodComparison"
            class="period-comparison"
          >
            <div class="period-card">
              <span>当前周期</span>
              <strong>{{ formatNumber(periodComparison.current_total_consumption, 1) }}</strong>
            </div>
            <div class="period-card">
              <span>上一周期</span>
              <strong>{{ formatNumber(periodComparison.previous_total_consumption, 1) }}</strong>
            </div>
            <div class="period-card">
              <span>环比</span>
              <strong :class="['trend-change', { 'trend-change--up': (periodComparison.change_rate || 0) > 0 }]">
                {{ formatSignedPercent(periodComparison.change_rate) }}
              </strong>
            </div>
          </div>

          <div
            v-if="comparison?.energy_categories.length"
            class="comparison-list"
          >
            <div
              v-for="item in comparison.energy_categories"
              :key="item.energy_category"
              class="comparison-item"
            >
              <div class="comparison-row">
                <span>{{ item.label }}</span>
                <strong>{{ formatPercent(item.ratio) }}</strong>
              </div>
              <div class="comparison-meta">
                <span>{{ formatNumber(item.total_consumption, 1) }} 周期能耗</span>
                <span>{{ formatNumber(item.avg_load, 1) }} 平均负荷</span>
              </div>
              <div class="comparison-bar">
                <span :style="{ width: `${Math.max(item.ratio * 100, 4)}%` }" />
              </div>
            </div>
          </div>
          <el-empty
            v-else
            description="暂无能源介质对比数据"
          />
        </article>

        <article class="board-card board-card--wide">
          <div class="board-header">
            <div>
              <h3>排行</h3>
              <p>覆盖区域、楼栋和设备三层排行，当前优先以周期能耗和平均负荷组织运营焦点。</p>
            </div>
          </div>

          <div class="ranking-grid">
            <div class="ranking-block">
              <div class="ranking-title">区域排行</div>
              <div
                v-if="areaRanking.length"
                class="rank-list"
              >
                <div
                  v-for="(item, index) in areaRanking"
                  :key="`area-${item.location_id}`"
                  class="rank-item"
                >
                  <span class="rank-index">{{ index + 1 }}</span>
                  <div class="rank-main">
                    <strong>{{ item.name }}</strong>
                    <span>{{ formatNumber(item.total_consumption, 1) }} 周期能耗</span>
                  </div>
                  <span class="rank-side">{{ formatNumber(item.avg_load, 1) }}</span>
                </div>
              </div>
              <el-empty
                v-else
                description="暂无区域排行"
              />
            </div>

            <div class="ranking-block">
              <div class="ranking-title">楼栋排行</div>
              <div
                v-if="buildingRanking.length"
                class="rank-list"
              >
                <div
                  v-for="(item, index) in buildingRanking"
                  :key="`building-${item.location_id}`"
                  class="rank-item"
                >
                  <span class="rank-index">{{ index + 1 }}</span>
                  <div class="rank-main">
                    <strong>{{ item.name }}</strong>
                    <span>{{ formatNumber(item.total_consumption, 1) }} 周期能耗</span>
                  </div>
                  <span class="rank-side">{{ formatNumber(item.avg_load, 1) }}</span>
                </div>
              </div>
              <el-empty
                v-else
                description="暂无楼栋排行"
              />
            </div>

            <div class="ranking-block">
              <div class="ranking-title">设备排行</div>
              <div
                v-if="deviceRanking.length"
                class="rank-list"
              >
                <div
                  v-for="(item, index) in deviceRanking"
                  :key="`device-${item.device_id}`"
                  class="rank-item"
                >
                  <span class="rank-index">{{ index + 1 }}</span>
                  <div class="rank-main">
                    <strong>{{ item.name }}</strong>
                    <span>{{ getEnergyLabel(item.energy_type) }} · {{ item.location || '未分配位置' }}</span>
                  </div>
                  <span class="rank-side">{{ formatNumber(item.total_consumption, 1) }}</span>
                </div>
              </div>
              <el-empty
                v-else
                description="暂无设备排行"
              />
            </div>
          </div>
        </article>

        <article class="board-card">
          <div class="board-header">
            <div>
              <h3>异常</h3>
              <p>当前仅展示第一批运营信号，不包装成完整异常分析引擎。</p>
            </div>
            <el-tag
              :type="anomaly?.boundary === 'operational_signal_first_batch' ? 'warning' : 'info'"
              effect="plain"
            >
              {{ anomaly?.boundary === 'operational_signal_first_batch' ? '第一批运营信号' : anomaly?.boundary }}
            </el-tag>
          </div>

          <div
            v-if="anomaly"
            class="anomaly-summary"
          >
            <div class="anomaly-pill">
              <span>总数</span>
              <strong>{{ anomaly.summary.total_count }}</strong>
            </div>
            <div class="anomaly-pill">
              <span>断档</span>
              <strong>{{ anomaly.summary.data_gap_count }}</strong>
            </div>
            <div class="anomaly-pill">
              <span>失败</span>
              <strong>{{ anomaly.summary.ingestion_failure_count }}</strong>
            </div>
            <div class="anomaly-pill">
              <span>告警</span>
              <strong>{{ anomaly.summary.active_alarm_count }}</strong>
            </div>
          </div>

          <div
            v-if="anomalyItems.length"
            class="alert-list"
          >
            <div
              v-for="item in anomalyItems"
              :key="`${item.kind}-${item.device_id}-${item.detected_at}`"
              class="alert-item"
            >
              <div class="alert-main">
                <div class="alert-title-row">
                  <strong>{{ item.device_name }}</strong>
                  <el-tag
                    :type="getSeverityType(item.severity)"
                    effect="plain"
                    size="small"
                  >
                    {{ severityLabels[item.severity] || item.severity }}
                  </el-tag>
                </div>
                <span>{{ getAnomalyKindLabel(item.kind) }} · {{ getEnergyLabel(item.energy_type) }} · {{ item.location || '未分配位置' }}</span>
                <p>{{ item.message }}</p>
              </div>
              <span class="alert-time">{{ formatTimestamp(item.detected_at, 'hour') }}</span>
            </div>
          </div>
          <el-empty
            v-else
            description="当前统计窗口无运营异常信号"
          />
        </article>

        <article class="board-card">
          <div class="board-header">
            <div>
              <h3>洞察</h3>
              <p>直接消费后端摘要结论，为运营侧保留高层判断入口。</p>
            </div>
          </div>

          <div
            v-if="insights.length"
            class="insight-list"
          >
            <div
              v-for="item in insights"
              :key="item.title"
              class="insight-item"
            >
              <div class="insight-top">
                <strong>{{ item.title }}</strong>
                <el-tag
                  :type="getSeverityType(item.severity)"
                  effect="plain"
                  size="small"
                >
                  {{ severityLabels[item.severity] || item.severity }}
                </el-tag>
              </div>
              <p>{{ item.detail }}</p>
              <span>{{ item.dimension }}</span>
            </div>
          </div>
          <el-empty
            v-else
            description="当前暂无洞察摘要"
          />
        </article>
      </div>

      <aside class="side-rail">
        <article class="side-card">
          <div class="side-title">
            范围与口径
          </div>
          <div class="scope-window">
            <span>统计窗口</span>
            <strong>{{ formatTimestamp(timeWindow?.start_time, 'day') }} - {{ formatTimestamp(timeWindow?.end_time, 'day') }}</strong>
          </div>
          <div class="scope-window">
            <span>统计范围</span>
            <strong>{{ getLocationTypeLabel(scope?.location_type) }}</strong>
          </div>
          <div class="basis-note">
            {{ statBasisText }}
          </div>
          <div class="scope-counts">
            <div
              v-for="item in scopeCountItems"
              :key="item.label"
              class="scope-count-item"
            >
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </article>

        <article class="side-card">
          <div class="side-title">
            分项与介质
          </div>
          <div class="tag-list">
            <el-tag
              v-for="item in scope?.energy_categories || []"
              :key="item"
              type="info"
              effect="plain"
            >
              {{ getEnergyLabel(item) }}
            </el-tag>
          </div>
          <div
            v-if="subItemComparison.length"
            class="subitem-list"
          >
            <div
              v-for="item in subItemComparison"
              :key="item.sub_item"
              class="subitem-item"
            >
              <div class="subitem-row">
                <strong>{{ item.label }}</strong>
                <span>{{ formatNumber(item.total_consumption, 1) }}</span>
              </div>
              <span>{{ item.device_count }} 台设备 · {{ item.energy_categories.map(getEnergyLabel).join(' / ') }}</span>
            </div>
          </div>
          <el-empty
            v-else
            description="暂无分项对比"
          />
        </article>

        <article class="side-card">
          <div class="side-title">
            次级设备入口
          </div>
          <div class="entry-actions">
            <el-button
              type="primary"
              plain
              @click="router.push('/devices')"
            >
              设备与表计
            </el-button>
            <el-button
              plain
              @click="router.push('/energy')"
            >
              区域 / 楼栋能耗
            </el-button>
            <el-button
              plain
              @click="router.push('/forecast-tools')"
            >
              预测 / 模型工具
            </el-button>
          </div>
        </article>
      </aside>
    </section>

    <el-empty
      v-if="!loading && loadError"
      :description="loadError"
    >
      <el-button
        type="primary"
        @click="loadOverview"
      >
        重新加载
      </el-button>
    </el-empty>

    <el-skeleton
      v-if="loading"
      :rows="6"
      animated
      class="loading-overlay"
    />
  </div>
</template>

<style scoped>
.analysis-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100%;
  padding: 10px;
  color: var(--text-primary);
}

.hero-section {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(320px, 0.9fr);
  gap: 20px;
}

.hero-copy,
.hero-focus,
.metric-card,
.board-card,
.side-card {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: linear-gradient(180deg, rgba(18, 31, 52, 0.96) 0%, rgba(9, 17, 32, 0.96) 100%);
  box-shadow: 0 20px 60px rgba(3, 10, 24, 0.22);
}

.hero-copy {
  padding: 28px;
  border-radius: 28px;
}

.hero-eyebrow {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(73, 145, 255, 0.14);
  color: #8cb8ff;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-copy h1 {
  margin: 16px 0 12px;
  font-size: 34px;
  line-height: 1.1;
}

.hero-copy p {
  max-width: 720px;
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
  color: var(--text-secondary);
  font-size: 13px;
}

.hero-meta span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
}

.hero-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.hero-focus {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 28px;
  border-radius: 28px;
}

.focus-label,
.metric-label,
.side-title,
.ranking-title {
  color: var(--text-secondary);
  font-size: 13px;
}

.focus-value {
  margin-top: 10px;
  font-size: 32px;
  font-weight: 700;
}

.focus-meta {
  margin-top: 10px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.focus-divider {
  height: 1px;
  margin: 18px 0;
  background: rgba(255, 255, 255, 0.08);
}

.focus-snapshot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

.focus-snapshot strong {
  font-size: 18px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 22px;
  border-radius: 22px;
}

.metric-value {
  font-size: 28px;
  line-height: 1;
}

.metric-hint,
.board-header p,
.basis-note,
.rank-main span,
.subitem-item span,
.insight-item p,
.insight-item span {
  color: var(--text-secondary);
  line-height: 1.6;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(280px, 0.8fr);
  gap: 20px;
  align-items: start;
}

.analysis-board {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.board-card {
  padding: 22px;
  border-radius: 24px;
}

.board-card--hero,
.board-card--wide {
  grid-column: span 2;
}

.board-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.board-header h3 {
  margin: 0 0 8px;
  font-size: 22px;
}

.board-header p {
  margin: 0;
}

.trend-stage {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.trend-chart-card,
.period-card,
.anomaly-pill,
.scope-count-item,
.subitem-item,
.insight-item,
.rank-item,
.comparison-item,
.alert-item {
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
}

.trend-chart-card {
  padding: 18px;
}

.trend-chart-header,
.trend-footer,
.comparison-row,
.comparison-meta,
.scope-window,
.subitem-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.trend-chart {
  width: 100%;
  height: 120px;
  margin: 14px 0 10px;
  overflow: visible;
}

.trend-line {
  fill: none;
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.trend-line--consumption {
  stroke: #63d6ff;
}

.trend-line--load {
  stroke: #78f0b8;
}

.period-comparison {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.period-card,
.anomaly-pill,
.scope-count-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
}

.period-card strong,
.anomaly-pill strong,
.scope-count-item strong {
  font-size: 20px;
}

.trend-change--up {
  color: #ff9c7a;
}

.comparison-list,
.rank-list,
.alert-list,
.insight-list,
.subitem-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comparison-item,
.rank-item,
.subitem-item,
.insight-item {
  padding: 14px 16px;
}

.comparison-meta {
  margin-top: 8px;
  font-size: 13px;
}

.comparison-bar {
  height: 8px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}

.comparison-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #4a90ff 0%, #63d6ff 100%);
}

.ranking-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.ranking-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rank-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(73, 145, 255, 0.16);
  color: #a4c4ff;
  font-weight: 700;
  flex: none;
}

.rank-main {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.rank-side {
  font-weight: 600;
}

.anomaly-summary,
.scope-counts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
}

.alert-main {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 6px;
}

.alert-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.alert-main span,
.alert-time {
  color: var(--text-secondary);
  font-size: 13px;
}

.alert-main p {
  margin: 0;
  line-height: 1.6;
}

.insight-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.insight-item p {
  margin: 10px 0 0;
}

.side-rail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.side-card {
  padding: 20px;
  border-radius: 24px;
}

.scope-window {
  margin-top: 12px;
}

.basis-note {
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  margin-bottom: 12px;
}

.entry-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.loading-overlay {
  margin-top: -8px;
}

@media (max-width: 1400px) {
  .metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .ranking-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1200px) {
  .hero-section,
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .metric-grid,
  .analysis-board,
  .trend-stage,
  .period-comparison {
    grid-template-columns: 1fr;
  }

  .board-card--hero,
  .board-card--wide {
    grid-column: auto;
  }
}

@media (max-width: 640px) {
  .analysis-page {
    padding: 0;
  }

  .hero-copy,
  .hero-focus,
  .metric-card,
  .board-card,
  .side-card {
    border-radius: 20px;
  }

  .hero-copy {
    padding: 22px;
  }

  .hero-copy h1 {
    font-size: 28px;
  }

  .hero-actions,
  .hero-meta {
    flex-direction: column;
  }

  .anomaly-summary,
  .scope-counts {
    grid-template-columns: 1fr;
  }

  .alert-item {
    flex-direction: column;
  }
}
</style>
