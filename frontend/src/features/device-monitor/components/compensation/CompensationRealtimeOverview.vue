<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'
import type { CompensationMetric, CompensationPowerFactorTrend, CompensationTone } from './types'
import { getFlagGroups, hasAnyActiveFlag } from './circuitStateUtils'

const props = defineProps({
  coreMetric: {
    type: Object as PropType<CompensationMetric>,
    required: true,
  },
  pfMetric: {
    type: Object as PropType<CompensationMetric>,
    required: true,
  },
  metrics: {
    type: Array as PropType<CompensationMetric[]>,
    default: () => [],
  },
  extendedHint: {
    type: String,
    default: '',
  },
  capacitorBankTelemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
  pfTrend: {
    type: Object as PropType<CompensationPowerFactorTrend>,
    default: () => ({ values: [], target: null }),
  },
  statusText: {
    type: String,
    default: '',
  },
  statusTone: {
    type: String as PropType<CompensationTone>,
    default: 'neutral',
  },
})

const SPARK_WIDTH = 100
const SPARK_HEIGHT = 36
const SPARK_PADDING = 6

const hasSparkline = computed(() => props.pfTrend.values.length >= 2)

const sparkGeometry = computed(() => {
  const values = props.pfTrend.values
  if (values.length < 2) return null
  const target = props.pfTrend.target
  const rangeSource = target != null ? [...values, target] : values
  const min = Math.min(...rangeSource)
  const max = Math.max(...rangeSource)
  const span = max - min || 1
  const innerHeight = SPARK_HEIGHT - SPARK_PADDING * 2
  const lastIndex = values.length - 1
  const toY = (value: number) => SPARK_PADDING + (1 - (value - min) / span) * innerHeight
  const line = values
    .map((value, index) => `${((index / lastIndex) * SPARK_WIDTH).toFixed(2)},${toY(value).toFixed(2)}`)
    .join(' ')
  return {
    line,
    area: `0,${SPARK_HEIGHT} ${line} ${SPARK_WIDTH},${SPARK_HEIGHT}`,
    targetY: target != null ? toY(target) : null,
    dotTopPct: (toY(values[lastIndex]) / SPARK_HEIGHT) * 100,
  }
})

const sparkTargetLabel = computed(() => {
  const target = props.pfTrend.target
  return target != null ? `目标 ${target.toFixed(2)}` : ''
})

const sparkRangeLabel = computed(() => {
  const values = props.pfTrend.values
  if (values.length === 0) return ''
  const min = Math.min(...values)
  const max = Math.max(...values)
  if (max - min < 0.005) return `稳定 ${min.toFixed(2)}`
  return `区间 ${min.toFixed(2)}–${max.toFixed(2)}`
})

const flagGroups = computed(() =>
  props.capacitorBankTelemetry ? getFlagGroups(props.capacitorBankTelemetry) : [],
)
const anyActiveFlag = computed(() => hasAnyActiveFlag(flagGroups.value))

function progressColor(value: string) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return '#e8eef7'
  if (numeric >= 0.96) return '#22c55e'
  if (numeric >= 0.9) return '#f59e0b'
  return '#ef4444'
}

function stateTagText(state: CompensationMetric['state']) {
  if (state === 'live') return '● 实时'
  if (state === 'mock') return '◑ 估算'
  if (state === 'missing') return '✕ 缺测'
  if (state === 'offline') return '⊘ 离线'
  if (state === 'unconfigured') return '○ 待配置'
  return ''
}

function stateTagType(state: CompensationMetric['state']) {
  if (state === 'live') return 'success'
  if (state === 'mock') return 'warning'
  if (state === 'missing' || state === 'offline') return 'danger'
  if (state === 'unconfigured') return 'info'
  return 'info'
}

function isUnavailableState(state: CompensationMetric['state']) {
  return state === 'missing' || state === 'offline'
}

function displayMetricValue(item: CompensationMetric) {
  if (isUnavailableState(item.state)) return '--'
  if (item.value === '暂无数据' || item.value === '通讯中断') return '--'
  return item.value
}

const isWaitingForTelemetry = computed(() => {
  const telemetryMetrics = [
    props.coreMetric,
    props.pfMetric,
    ...props.metrics.filter((item) => item.key !== 'controlMode'),
  ]
  return telemetryMetrics.length > 0 && telemetryMetrics.every((item) => item.state !== 'live')
})

const pfValueColor = computed(() =>
  isWaitingForTelemetry.value ? '#d8e4f4' : progressColor(props.pfMetric.value),
)

// capacityUsage（回路投入率）已并入「实时监测」面板，指标条不重复展示
const stripMetrics = computed(() =>
  props.metrics.filter((item) => item.key !== 'capacityUsage'),
)
</script>

<template>
  <section class="bento-overview">
    <div
      v-if="isWaitingForTelemetry"
      class="telemetry-waiting"
    >
      <strong>等待设备上报实时遥测</strong>
      <span>当前仅展示档案、模板诊断和可接入字段，收到首包数据后将自动显示补偿效果、三相快照、回路状态和趋势。</span>
    </div>

    <!-- TOP: 无功功率 小卡 | 功率因数 Hero + 趋势 -->
    <div class="bento-top">
      <div
        class="bento-reactive"
        :class="{ 'bento-reactive--waiting': isWaitingForTelemetry }"
      >
        <span
          v-if="statusText && !isWaitingForTelemetry"
          class="bento-reactive__status"
          :class="`status-${statusTone}`"
        >
          {{ statusText }}
        </span>
        <div class="metric-label-row">
          <el-tooltip :content="coreMetric.hint" placement="top" :disabled="!coreMetric.hint">
            <span class="bento-reactive__label">{{ coreMetric.label }}</span>
          </el-tooltip>
          <el-tag
            v-if="coreMetric.state && coreMetric.state !== 'live' && !isWaitingForTelemetry"
            size="small"
            effect="plain"
            :type="stateTagType(coreMetric.state)"
          >
            {{ stateTagText(coreMetric.state) }}
          </el-tag>
        </div>
        <div class="bento-reactive__value">
          <strong>{{ isWaitingForTelemetry ? '等待采集' : displayMetricValue(coreMetric) }}</strong>
          <small v-if="!isWaitingForTelemetry">{{ coreMetric.unit }}</small>
        </div>
      </div>

      <div
        class="bento-hero"
        :class="{ 'bento-hero--waiting': isWaitingForTelemetry }"
      >
        <div class="bento-hero__top">
          <div class="metric-label-row">
            <el-tooltip :content="pfMetric.hint" placement="top" :disabled="!pfMetric.hint">
              <span class="bento-hero__label">{{ pfMetric.label }}</span>
            </el-tooltip>
            <el-tag
              v-if="pfMetric.state && pfMetric.state !== 'live' && !isWaitingForTelemetry"
              size="small"
              effect="plain"
              :type="stateTagType(pfMetric.state)"
            >
              {{ stateTagText(pfMetric.state) }}
            </el-tag>
          </div>
        </div>
        <div class="bento-hero__main">
          <div class="bento-hero__value">
            <strong :style="{ color: pfValueColor }">{{ isWaitingForTelemetry ? '等待采集' : displayMetricValue(pfMetric) }}</strong>
            <small v-if="!isWaitingForTelemetry">PF</small>
          </div>
          <div
            v-if="hasSparkline && sparkGeometry"
            class="bento-hero__spark"
          >
            <div class="bento-hero__spark-caption">
              <span>近期功率因数趋势</span>
              <span class="bento-hero__spark-meta">
                <span v-if="sparkRangeLabel">{{ sparkRangeLabel }}</span>
                <span
                  v-if="sparkTargetLabel"
                  class="bento-hero__spark-target-label"
                >{{ sparkTargetLabel }}</span>
              </span>
            </div>
            <div class="bento-hero__spark-chart">
              <svg
                class="bento-hero__spark-svg"
                :viewBox="`0 0 ${SPARK_WIDTH} ${SPARK_HEIGHT}`"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <defs>
                  <linearGradient
                    id="pfSparkFill"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="0"
                      :stop-color="pfValueColor"
                      stop-opacity="0.24"
                    />
                    <stop
                      offset="1"
                      :stop-color="pfValueColor"
                      stop-opacity="0"
                    />
                  </linearGradient>
                </defs>
                <polygon
                  class="bento-hero__spark-area"
                  fill="url(#pfSparkFill)"
                  :points="sparkGeometry.area"
                />
                <line
                  v-if="sparkGeometry.targetY != null"
                  class="bento-hero__spark-target"
                  x1="0"
                  :y1="sparkGeometry.targetY"
                  :x2="SPARK_WIDTH"
                  :y2="sparkGeometry.targetY"
                />
                <polyline
                  class="bento-hero__spark-line"
                  :style="{ stroke: pfValueColor }"
                  :points="sparkGeometry.line"
                />
              </svg>
              <span
                class="bento-hero__spark-dot"
                :style="{ top: `${sparkGeometry.dotTopPct}%`, background: pfValueColor }"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- BOTTOM STRIP: 6 指标 -->
    <div class="bento-strip">
      <div
        v-for="item in stripMetrics"
        :key="item.key"
        class="strip-cell"
        :class="{ 'strip-cell--waiting': isUnavailableState(item.state) }"
      >
        <div class="metric-label-row metric-label-row--compact">
          <el-tooltip :content="item.hint" placement="top" :disabled="!item.hint">
            <span class="strip-cell__label">{{ item.label }}</span>
          </el-tooltip>
          <el-tag
            v-if="item.state && item.state !== 'live' && !isWaitingForTelemetry"
            size="small"
            effect="plain"
            :type="stateTagType(item.state)"
          >
            {{ stateTagText(item.state) }}
          </el-tag>
        </div>
        <div
          class="strip-cell__value"
          :class="item.tone ? `tone-${item.tone}` : ''"
        >
          <strong>{{ displayMetricValue(item) }}</strong>
          <small v-if="item.unit && !isUnavailableState(item.state)">{{ item.unit }}</small>
        </div>
      </div>
    </div>
  </section>

  <div
    v-if="capacitorBankTelemetry"
    class="alarm-flags"
  >
    <div
      v-for="group in flagGroups"
      :key="group.label"
      class="flag-group"
      :title="group.title"
    >
      <span
        class="flag-group__label"
        :class="{ 'flag-group__label--active': group.flags.some(f => f.active) }"
      >{{ group.label }}</span>
      <div class="flag-group__chips">
        <span
          v-for="flag in group.flags"
          :key="flag.key || group.label"
          class="flag-chip"
          :class="flag.active ? 'flag-chip--active' : 'flag-chip--ok'"
        >
          {{ flag.key || '！' }}
        </span>
      </div>
    </div>
    <div
      v-if="!anyActiveFlag"
      class="flags-all-ok"
    >
      所有标志正常
    </div>
  </div>

  <div
    v-if="extendedHint"
    class="extended-hint"
  >
    {{ extendedHint }}
  </div>
</template>

<style scoped>
/* ── Bento container ─────────────────────────────────────────── */
.bento-overview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.telemetry-waiting {
  display: grid;
  gap: 4px;
  padding: 14px 16px;
  color: #c8d7ec;
  background: rgba(30, 48, 70, 0.46);
  border: 1px solid rgba(72, 96, 130, 0.58);
  border-radius: 12px;
}

.telemetry-waiting strong {
  color: #e5eefb;
  font-size: 14px;
}

.telemetry-waiting span {
  color: #8ea0bc;
  font-size: 12px;
  line-height: 1.55;
}

/* ── Top zone: 无功功率 小卡 | PF Hero ───────────────────────── */
.bento-top {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 12px;
  min-height: 200px;
}

.bento-reactive,
.bento-hero {
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

/* 无功功率 小卡 */
.bento-reactive {
  position: relative;
  padding: 22px 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14px;
}

.bento-reactive__label {
  font-size: 13px;
  color: #c5d2e7;
}

.metric-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}

.metric-label-row--compact {
  align-items: flex-start;
}

.bento-reactive__value {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.bento-reactive__value strong {
  font-size: 56px;
  line-height: 1;
  color: #3dd5f3;
  letter-spacing: 0.02em;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
}

.bento-reactive__value small {
  font-size: 16px;
  color: #8ea0bc;
}

.bento-reactive--waiting .bento-reactive__value strong {
  color: #d8e4f4;
  font-size: 34px;
  letter-spacing: 0;
}

.bento-reactive__status {
  position: absolute;
  top: 14px;
  right: 16px;
  padding: 3px 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid transparent;
}

.status-success {
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.status-warning {
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.32);
  color: #fbbf24;
}

.status-danger {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.32);
  color: #fb7185;
}

.status-info,
.status-neutral {
  background: rgba(76, 97, 126, 0.2);
  border-color: rgba(76, 97, 126, 0.4);
  color: #9fb1cc;
}

/* PF Hero panel */
.bento-hero {
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
}

.bento-hero__top {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bento-hero__label {
  font-size: 13px;
  color: #c5d2e7;
}

.bento-hero__main {
  display: flex;
  align-items: center;
  gap: 26px;
}

.bento-hero__value {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-shrink: 0;
}

.bento-hero__value strong {
  font-size: 56px;
  line-height: 1;
  letter-spacing: 0.02em;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
}

.bento-hero__value small {
  font-size: 16px;
  color: #8ea0bc;
}

.bento-hero--waiting .bento-hero__value strong {
  font-size: 34px;
  letter-spacing: 0;
}

/* PF 趋势 sparkline */
.bento-hero__spark {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bento-hero__spark-caption {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
  color: #7f93b2;
}

.bento-hero__spark-meta {
  display: flex;
  align-items: baseline;
  gap: 10px;
  white-space: nowrap;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
}

.bento-hero__spark-target-label {
  color: #9fb1cc;
}

.bento-hero__spark-chart {
  position: relative;
  overflow: visible;
}

.bento-hero__spark-svg {
  width: 100%;
  height: 48px;
  display: block;
  overflow: visible;
}

.bento-hero__spark-line {
  fill: none;
  stroke-width: 1.8;
  stroke-linejoin: round;
  stroke-linecap: round;
  vector-effect: non-scaling-stroke;
}

.bento-hero__spark-area {
  stroke: none;
}

.bento-hero__spark-target {
  stroke: rgba(148, 163, 184, 0.55);
  stroke-width: 1;
  stroke-dasharray: 3 3;
  vector-effect: non-scaling-stroke;
}

.bento-hero__spark-dot {
  position: absolute;
  right: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  transform: translate(50%, -50%);
  box-shadow: 0 0 0 2.5px rgba(13, 22, 35, 0.9);
}

/* ── Bottom strip: 6 metric cards ────────────────────────────── */
.bento-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
}

.strip-cell {
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-top: 3px solid rgba(59, 130, 246, 0.25);
  border-radius: 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 6px;
  min-height: 88px;
}

.strip-cell--waiting {
  border-top-color: rgba(100, 116, 139, 0.22);
}

.strip-cell__label {
  font-size: 11px;
  color: #8ea0bc;
  line-height: 1.3;
}

.strip-cell__value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.strip-cell__value strong {
  font-size: 20px;
  line-height: 1;
  color: #f5f7fb;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
}

.strip-cell__value small {
  font-size: 10px;
  color: #7f93b2;
}

.strip-cell--waiting .strip-cell__value strong {
  color: #a8b6ca;
}


/* Tone modifiers */
.tone-success .strip-cell__value strong { color: #4ade80; }
.tone-warning .strip-cell__value strong { color: #fbbf24; }
.tone-danger  .strip-cell__value strong { color: #fb7185; }
.tone-info    .strip-cell__value strong { color: #60a5fa; }

/* Alarm flags bar */
.alarm-flags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(72, 96, 130, 0.58);
  background: rgba(13, 21, 34, 0.72);
}

.flag-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.flag-group__label {
  font-size: var(--font-caption);
  color: var(--text-label);
  font-weight: 600;
  white-space: nowrap;
}

.flag-group__label--active {
  color: #fbbf24;
}

.flag-group__chips {
  display: flex;
  gap: 4px;
}

.flag-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--touch-target);
  height: var(--touch-target);
  padding: 0 6px;
  border-radius: 4px;
  font-size: var(--font-caption);
  font-weight: 600;
}

.flag-chip--active {
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.45);
  color: #fcd34d;
}

.flag-chip--ok {
  background: rgba(30, 48, 70, 0.35);
  border: 1px solid rgba(74, 96, 128, 0.4);
  color: var(--text-label);
}

.flags-all-ok {
  margin-left: auto;
  font-size: var(--font-caption);
  color: #6ee7a4;
}

/* Extended hint */
.extended-hint {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px dashed rgba(90, 109, 138, 0.58);
  background: rgba(13, 21, 34, 0.72);
  color: #8ea0bc;
  font-size: 12px;
}

/* ── Responsive ──────────────────────────────────────────────── */
@media (max-width: 1380px) {
  .bento-top {
    grid-template-columns: 1fr;
  }

  .bento-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .bento-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
