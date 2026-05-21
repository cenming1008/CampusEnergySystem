<script setup lang="ts">
import { computed } from 'vue'
import type {
  CompensationCapacitorBankControlProfile,
  CompensationCapacitorBankTelemetry,
  CompensationHarmonicSpectrumPoint,
} from '@/api/compensation'
import type { DeviceAlarmRecord } from '@/api/deviceMonitor'
import type { CompensationEventItem } from '@/features/device-monitor/components/compensation/types'

type Tone = 'success' | 'warning' | 'danger' | 'neutral'
type Phase = 'a' | 'b' | 'c'

const props = defineProps<{
  telemetry: CompensationCapacitorBankTelemetry | null | undefined
  history: CompensationCapacitorBankTelemetry[]
  controlProfile: CompensationCapacitorBankControlProfile | null | undefined
  alarms: DeviceAlarmRecord[]
  events: CompensationEventItem[]
  timeRange: [Date, Date] | null
}>()

const phaseLabels: Record<Phase, string> = { a: 'A 相', b: 'B 相', c: 'C 相' }

function finite(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

function avg(values: Array<number | null | undefined>): number | null {
  const nums = values.filter(finite)
  return nums.length ? nums.reduce((sum, value) => sum + value, 0) / nums.length : null
}

function sum(values: Array<number | null | undefined>): number | null {
  const nums = values.filter(finite)
  return nums.length ? nums.reduce((total, value) => total + value, 0) : null
}

function fmt(value: number | null | undefined, digits = 1): string {
  return finite(value) ? value.toFixed(digits) : '暂无数据'
}

function fmtPercent(value: number | null | undefined, digits = 1): string {
  return finite(value) ? `${value.toFixed(digits)}%` : '暂无数据'
}

function normalizePowerFactorTarget(value: number | null | undefined, fallback: number): number {
  if (!finite(value)) return fallback
  return value > 1 ? value / 100 : value
}

function normalizePercentThreshold(value: number | null | undefined, fallback: number): number {
  if (!finite(value)) return fallback
  if (value > 20 && value <= 100) return value / 10
  if (value > 100) return value / 100
  return value
}

function fmtDateTime(value: string | Date | null | undefined): string {
  if (!value) return '暂无数据'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return '暂无数据'
  return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function isWithinRange(value: string | null | undefined): boolean {
  if (!props.timeRange || !value) return true
  const time = new Date(value).getTime()
  if (Number.isNaN(time)) return false
  return time >= props.timeRange[0].getTime() && time <= props.timeRange[1].getTime()
}

function phasePf(row: CompensationCapacitorBankTelemetry | null | undefined): number | null {
  if (!row) return null
  return avg([row.power_factor_a, row.power_factor_b, row.power_factor_c])
}

function reactivePower(row: CompensationCapacitorBankTelemetry | null | undefined): number | null {
  if (!row) return null
  return sum([row.reactive_power_a, row.reactive_power_b, row.reactive_power_c])
}

function harmonicPoints(phase: Phase): CompensationHarmonicSpectrumPoint[] {
  const telemetry = props.telemetry
  if (!telemetry) return []
  if (phase === 'a') return telemetry.voltage_harmonics_a ?? []
  if (phase === 'b') return telemetry.voltage_harmonics_b ?? []
  return telemetry.voltage_harmonics_c ?? []
}

function phasePeak(phase: Phase) {
  const points = harmonicPoints(phase).filter((point) => finite(point.value))
  if (!points.length) return { phase, order: null as number | null, value: null as number | null }
  const peak = points.reduce((best, point) => (point.value > best.value ? point : best), points[0])
  return { phase, order: peak.order, value: peak.value }
}

const pfTarget = computed(() => normalizePowerFactorTarget(props.controlProfile?.switch_on_power_factor, 0.95))
const voltageHarmonicThreshold = computed(() => normalizePercentThreshold(props.controlProfile?.voltage_harmonic_threshold, 5))
const currentHarmonicThreshold = computed(() => normalizePercentThreshold(props.controlProfile?.current_harmonic_threshold, 8))
const temperatureLimit = computed(() => props.controlProfile?.temperature_upper_limit ?? 65)

const currentPf = computed(() => phasePf(props.telemetry))
const currentReactivePower = computed(() => reactivePower(props.telemetry))
const pfHistory = computed(() => props.history.map(phasePf).filter(finite))
const averagePf = computed(() => avg(pfHistory.value))
const minPf = computed(() => pfHistory.value.length ? Math.min(...pfHistory.value) : null)
const lowPfCount = computed(() => pfHistory.value.filter((value) => value < pfTarget.value).length)

const phasePeaks = computed(() => (['a', 'b', 'c'] as Phase[]).map(phasePeak))
const topPeak = computed(() => {
  const available = phasePeaks.value.filter((item): item is { phase: Phase, order: number, value: number } => finite(item.value) && item.order !== null)
  if (!available.length) return null
  return available.reduce((best, item) => (item.value > best.value ? item : best), available[0])
})

const thdMax = computed(() => Math.max(
  props.telemetry?.voltage_thd_a ?? 0,
  props.telemetry?.voltage_thd_b ?? 0,
  props.telemetry?.voltage_thd_c ?? 0,
))

const conclusion = computed((): { status: string, title: string, detail: string, suggestion: string, tone: Tone } => {
  if (!props.telemetry && props.history.length === 0) {
    return {
      status: '数据不足',
      title: '当前时间范围内暂无可分析采样',
      detail: '请扩大时间范围或等待设备上报。',
      suggestion: '优先确认采集链路和最近成功采样时间。',
      tone: 'neutral',
    }
  }

  if (topPeak.value && topPeak.value.value > voltageHarmonicThreshold.value) {
    return {
      status: '越限',
      title: `${phaseLabels[topPeak.value.phase]} ${topPeak.value.order} 次电压谐波越限`,
      detail: `峰值 ${fmtPercent(topPeak.value.value)}，门限 ${fmtPercent(voltageHarmonicThreshold.value)}。`,
      suggestion: '优先复核补偿柜投切状态、谐波门限配置和现场负载变化。',
      tone: 'danger',
    }
  }

  if (thdMax.value > voltageHarmonicThreshold.value || (props.telemetry?.current_harmonic_a ?? 0) > currentHarmonicThreshold.value) {
    return {
      status: '越限',
      title: 'THD 指标存在越限',
      detail: `当前最大电压 THD ${fmtPercent(thdMax.value)}。`,
      suggestion: '建议联动查看谐波告警和投切事件。',
      tone: 'danger',
    }
  }

  if (currentPf.value !== null && currentPf.value < pfTarget.value) {
    return {
      status: '关注',
      title: '功率因数低于目标',
      detail: `当前 PF ${fmt(currentPf.value, 3)}，目标 ≥ ${fmt(pfTarget.value, 2)}。`,
      suggestion: '建议查看投切参数和最近控制动作。',
      tone: 'warning',
    }
  }

  return {
    status: '正常',
    title: '关键曲线处于目标区间',
    detail: `PF、谐波和温度均未触发分析阈值。`,
    suggestion: '可继续观察趋势变化和采样完整性。',
    tone: 'success',
  }
})

const relatedEvents = computed(() => {
  const keywords = ['谐波', '功率因数', 'PF', '投切', '控制', '电压', '电流', '温度', '过补']
  const alarmItems = props.alarms
    .filter((alarm) =>
      !alarm.is_resolved
      && isWithinRange(alarm.timestamp)
      && keywords.some((keyword) => alarm.message.includes(keyword) || alarm.category?.includes(keyword)),
    )
    .map((alarm) => ({
      key: `alarm-${alarm.id}`,
      time: alarm.timestamp,
      title: alarm.message,
      tag: alarm.severity === 'critical' || alarm.severity === 'danger' ? '严重' : '告警',
      tone: alarm.severity === 'critical' || alarm.severity === 'danger' ? 'danger' as Tone : 'warning' as Tone,
    }))

  const eventItems = props.events
    .filter((event) =>
      isWithinRange(event.time)
      && keywords.some((keyword) => event.title.includes(keyword) || event.detail?.includes(keyword)),
    )
    .map((event, index) => ({
      key: `event-${index}-${event.time}`,
      time: event.time,
      title: event.title,
      tag: event.tag || '事件',
      tone: event.tone === 'danger' || event.tone === 'warning' ? event.tone : 'neutral' as Tone,
    }))

  return [...alarmItems, ...eventItems]
    .sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime())
    .slice(0, 4)
})

const missingRows = computed(() =>
  props.history.filter((row) =>
    phasePf(row) === null
    && reactivePower(row) === null
    && row.voltage_thd_a == null
    && row.current_harmonic_a == null,
  ).length,
)

const latestTimestamp = computed(() =>
  props.telemetry?.timestamp
  || props.history.at(-1)?.timestamp
  || null,
)

const rangeText = computed(() => {
  if (!props.timeRange) return '当前查询范围'
  return `${fmtDateTime(props.timeRange[0])} - ${fmtDateTime(props.timeRange[1])}`
})
</script>

<template>
  <aside class="curve-aside">
    <section class="curve-card curve-card--hero" :class="`curve-card--${conclusion.tone}`">
      <header class="curve-card__head">
        <span class="curve-card__title"><span class="rt-accent" />曲线分析助手</span>
        <span class="curve-card__status">{{ conclusion.status }}</span>
      </header>
      <div class="curve-card__body">
        <div class="curve-card__eyebrow">分析结论</div>
        <strong class="curve-card__headline">{{ conclusion.title }}</strong>
        <p>{{ conclusion.detail }}</p>
        <p class="curve-card__suggestion">{{ conclusion.suggestion }}</p>
      </div>
    </section>

    <section class="curve-card">
      <header class="curve-card__head">
        <span class="curve-card__title"><span class="rt-accent" />当前曲线摘要</span>
      </header>
      <div class="curve-list">
        <div
          v-for="peak in phasePeaks"
          :key="peak.phase"
          class="curve-list__row"
        >
          <span>{{ phaseLabels[peak.phase] }}峰值</span>
          <strong>{{ peak.order ? `${peak.order}次 / ${fmtPercent(peak.value)}` : '暂无数据' }}</strong>
        </div>
        <div class="curve-list__row">
          <span>当前 PF</span>
          <strong>{{ fmt(currentPf, 3) }}</strong>
        </div>
        <div class="curve-list__row">
          <span>平均 / 最低 PF</span>
          <strong>{{ fmt(averagePf, 3) }} / {{ fmt(minPf, 3) }}</strong>
        </div>
        <div class="curve-list__row">
          <span>当前无功 Q</span>
          <strong>{{ fmt(currentReactivePower, 1) }} kVar</strong>
        </div>
      </div>
    </section>

    <section class="curve-card">
      <header class="curve-card__head">
        <span class="curve-card__title"><span class="rt-accent" />关联事件</span>
        <span class="curve-card__meta">{{ relatedEvents.length }} 条</span>
      </header>
      <div v-if="relatedEvents.length" class="curve-events">
        <div
          v-for="event in relatedEvents"
          :key="event.key"
          class="curve-event"
          :class="`curve-event--${event.tone}`"
        >
          <span class="curve-event__time">{{ fmtDateTime(event.time) }}</span>
          <strong>{{ event.title }}</strong>
          <span class="curve-event__tag">{{ event.tag }}</span>
        </div>
      </div>
      <div v-else class="curve-empty">当前时间范围内暂无关联事件</div>
    </section>

    <section class="curve-card">
      <header class="curve-card__head">
        <span class="curve-card__title"><span class="rt-accent" />分析基准与数据质量</span>
      </header>
      <div class="curve-list">
        <div class="curve-list__row">
          <span>PF 目标</span>
          <strong>≥ {{ fmt(pfTarget, 2) }}</strong>
        </div>
        <div class="curve-list__row">
          <span>电压谐波门限</span>
          <strong>{{ fmtPercent(voltageHarmonicThreshold) }}</strong>
        </div>
        <div class="curve-list__row">
          <span>电流谐波门限</span>
          <strong>{{ fmtPercent(currentHarmonicThreshold) }}</strong>
        </div>
        <div class="curve-list__row">
          <span>温度告警</span>
          <strong>{{ fmt(temperatureLimit, 0) }} ℃</strong>
        </div>
        <div class="curve-list__row">
          <span>采样点数</span>
          <strong>{{ history.length }}</strong>
        </div>
        <div class="curve-list__row">
          <span>缺测点数</span>
          <strong>{{ missingRows }}</strong>
        </div>
        <div class="curve-list__row curve-list__row--stack">
          <span>时间范围</span>
          <strong>{{ rangeText }}</strong>
        </div>
        <div class="curve-list__row">
          <span>最新采样</span>
          <strong>{{ fmtDateTime(latestTimestamp) }}</strong>
        </div>
        <div class="curve-list__row">
          <span>低 PF 次数</span>
          <strong>{{ lowPfCount }}</strong>
        </div>
      </div>
    </section>
  </aside>
</template>

<style scoped>
.curve-aside {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.curve-card {
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  overflow: hidden;
}

.curve-card--danger { border-color: rgba(248, 113, 113, 0.45); }
.curve-card--warning { border-color: rgba(245, 158, 11, 0.42); }
.curve-card--success { border-color: rgba(52, 211, 153, 0.28); }

.curve-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}

.curve-card__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
}

.rt-accent {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #22d3ee;
  flex: 0 0 auto;
}

.curve-card__status,
.curve-card__meta,
.curve-event__tag {
  flex: 0 0 auto;
  padding: 2px 7px;
  border-radius: 5px;
  border: 1px solid rgba(34, 211, 238, 0.3);
  color: #67e8f9;
  font-size: 10px;
  background: rgba(34, 211, 238, 0.08);
}

.curve-card--danger .curve-card__status {
  color: #fecdd3;
  border-color: rgba(248, 113, 113, 0.45);
  background: rgba(248, 113, 113, 0.12);
}

.curve-card--warning .curve-card__status {
  color: #fcd34d;
  border-color: rgba(245, 158, 11, 0.45);
  background: rgba(245, 158, 11, 0.12);
}

.curve-card--success .curve-card__status {
  color: #6ee7b7;
  border-color: rgba(52, 211, 153, 0.35);
  background: rgba(52, 211, 153, 0.09);
}

.curve-card__body {
  padding: 12px 14px 14px;
}

.curve-card__eyebrow {
  color: #5e6c83;
  font-size: 10px;
  margin-bottom: 7px;
}

.curve-card__headline {
  display: block;
  color: #e5edf7;
  font-size: 13px;
  line-height: 1.45;
}

.curve-card__body p {
  margin: 8px 0 0;
  color: #9aa7bd;
  font-size: 11px;
  line-height: 1.6;
}

.curve-card__suggestion {
  color: #67e8f9 !important;
}

.curve-list {
  padding: 8px 14px 10px;
}

.curve-list__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 28px;
  border-bottom: 1px solid rgba(31, 44, 65, 0.72);
  color: #7b8ca5;
  font-size: 11px;
}

.curve-list__row:last-child {
  border-bottom: none;
}

.curve-list__row strong {
  color: #e5edf7;
  font-size: 11px;
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.curve-list__row--stack {
  align-items: flex-start;
  flex-direction: column;
  gap: 4px;
  padding: 7px 0;
}

.curve-list__row--stack strong {
  text-align: left;
  color: #9aa7bd;
}

.curve-events {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 14px 12px;
}

.curve-event {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 4px 8px;
  padding: 9px 10px;
  border-radius: 8px;
  border: 1px solid #1f2c41;
  background: #0b1623;
}

.curve-event--warning { border-left: 3px solid #f59e0b; }
.curve-event--danger { border-left: 3px solid #f87171; }
.curve-event--neutral { border-left: 3px solid #22d3ee; }

.curve-event__time {
  color: #5e6c83;
  font-size: 10px;
}

.curve-event strong {
  grid-column: 1 / -1;
  color: #e5edf7;
  font-size: 11px;
  line-height: 1.45;
}

.curve-event__tag {
  grid-row: 1;
  grid-column: 2;
}

.curve-empty {
  padding: 16px 14px;
  color: #5e6c83;
  font-size: 11px;
}
</style>
