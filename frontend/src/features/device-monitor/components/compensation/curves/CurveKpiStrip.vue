<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'
import MiniSparkline from './MiniSparkline.vue'

const props = defineProps({
  telemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
  history: {
    type: Array as PropType<CompensationCapacitorBankTelemetry[]>,
    default: () => [],
  },
})

type Status = 'ok' | 'warn' | 'crit' | 'na'

interface Kpi {
  label: string
  hint: string
  value: string
  unit?: string
  target: string
  delta: string
  status: Status
  color: string
  domain?: [number, number]
  spark: Array<number | null>
  refValue?: number
}

function avg3(a: number | null | undefined, b: number | null | undefined, c: number | null | undefined): number | null {
  const vs = [a, b, c].filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
  if (!vs.length) return null
  return vs.reduce((s, v) => s + v, 0) / vs.length
}

function sum3(a: number | null | undefined, b: number | null | undefined, c: number | null | undefined): number | null {
  const vs = [a, b, c].filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
  if (!vs.length) return null
  return vs.reduce((s, v) => s + v, 0)
}

function fmt(value: number | null, digits = 2): string {
  return value == null ? '—' : value.toFixed(digits)
}

const kpis = computed<Kpi[]>(() => {
  const t = props.telemetry
  const h = props.history

  const pfHist = h.map((row) => avg3(row.power_factor_a, row.power_factor_b, row.power_factor_c))
  const qHist = h.map((row) => sum3(row.reactive_power_a, row.reactive_power_b, row.reactive_power_c))
  const thduHist = h.map((row) => (typeof row.voltage_thd_a === 'number' ? row.voltage_thd_a : null))
  const thdiHist = h.map((row) => (typeof row.current_harmonic_a === 'number' ? row.current_harmonic_a : null))
  const tempHist = h.map((row) => (typeof row.temperature === 'number' ? row.temperature : null))

  const pf = t ? avg3(t.power_factor_a, t.power_factor_b, t.power_factor_c) : null
  const q = t ? sum3(t.reactive_power_a, t.reactive_power_b, t.reactive_power_c) : null
  const thdu = t?.voltage_thd_a ?? null
  const thdi = t?.current_harmonic_a ?? null
  const temp = t?.temperature ?? null

  const pfStatus: Status = pf == null ? 'na' : pf >= 0.95 ? 'ok' : pf >= 0.9 ? 'warn' : 'crit'
  const qStatus: Status = q == null ? 'na' : Math.abs(q) <= 50 ? 'ok' : Math.abs(q) <= 200 ? 'warn' : 'crit'
  const thduStatus: Status = thdu == null ? 'na' : thdu < 5 ? 'ok' : 'warn'
  const thdiStatus: Status = thdi == null ? 'na' : thdi < 8 ? 'ok' : 'warn'
  const tempStatus: Status = temp == null ? 'na' : temp < 55 ? 'ok' : temp < 65 ? 'warn' : 'crit'

  return [
    {
      label: '补偿后 PF',
      hint: '功率因数 · 三相均值',
      value: fmt(pf, 3),
      target: '目标 ≥ 0.95',
      delta: pf == null ? '—' : pf >= 0.95 ? '达标' : `差 ${(0.95 - pf).toFixed(3)}`,
      status: pfStatus,
      color: '#3d8bff',
      domain: [0.8, 1.0],
      refValue: 0.95,
      spark: pfHist,
    },
    {
      label: '无功 Q',
      hint: '当前残余 · A+B+C',
      value: fmt(q, 1),
      unit: 'kVar',
      target: '阈值 ±50',
      delta: q == null ? '—' : Math.abs(q) <= 50 ? '在阈值内' : '偏离阈值',
      status: qStatus,
      color: '#34d399',
      spark: qHist,
    },
    {
      label: 'THDu A 相',
      hint: '电压总畸变',
      value: fmt(thdu, 2),
      unit: '%',
      target: '限值 5.00%',
      delta: thdu == null ? '—' : `余量 ${(5 - thdu).toFixed(2)}%`,
      status: thduStatus,
      color: '#22d3ee',
      domain: [0, 5],
      refValue: 5,
      spark: thduHist,
    },
    {
      label: 'THDi A 相',
      hint: '电流总畸变',
      value: fmt(thdi, 2),
      unit: '%',
      target: '限值 8.00%',
      delta: thdi == null ? '—' : thdi <= 8 ? `余量 ${(8 - thdi).toFixed(2)}%` : `超 ${(thdi - 8).toFixed(2)}%`,
      status: thdiStatus,
      color: '#fbbf24',
      domain: [0, 12],
      refValue: 8,
      spark: thdiHist,
    },
    {
      label: '柜温',
      hint: '机芯温度',
      value: fmt(temp, 1),
      unit: '℃',
      target: '告警 65℃',
      delta: temp == null ? '—' : temp < 55 ? '正常' : temp < 65 ? '偏高' : '越限',
      status: tempStatus,
      color: '#a78bfa',
      domain: [25, 70],
      refValue: 65,
      spark: tempHist,
    },
  ]
})

function statusLabel(s: Status) {
  if (s === 'ok') return '达标'
  if (s === 'warn') return '边界'
  if (s === 'crit') return '越限'
  return '缺测'
}
</script>

<template>
  <div class="kpi-strip">
    <div
      v-for="kpi in kpis"
      :key="kpi.label"
      class="kpi-card"
      :class="[`kpi-card--${kpi.status}`]"
    >
      <div class="kpi-card__head">
        <div class="kpi-card__title">
          <div class="kpi-card__label">{{ kpi.label }}</div>
          <div class="kpi-card__hint">{{ kpi.hint }}</div>
        </div>
        <span class="kpi-card__pill" :class="[`kpi-card__pill--${kpi.status}`]">
          <i />
          {{ statusLabel(kpi.status) }}
        </span>
      </div>
      <div class="kpi-card__value-row">
        <span class="kpi-card__value mono">{{ kpi.value }}</span>
        <span v-if="kpi.unit" class="kpi-card__unit">{{ kpi.unit }}</span>
      </div>
      <div class="kpi-card__spark">
        <MiniSparkline
          :data="kpi.spark"
          :color="kpi.color"
          :height="38"
          :domain="kpi.domain"
          :ref-value="kpi.refValue ?? null"
        />
      </div>
      <div class="kpi-card__foot">
        <span class="kpi-card__target">{{ kpi.target }}</span>
        <span class="kpi-card__delta">{{ kpi.delta }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.kpi-card {
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.kpi-card--warn { border-color: rgba(251, 191, 36, 0.45); }
.kpi-card--crit { border-color: rgba(248, 113, 113, 0.55); }

.kpi-card__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 6px;
}

.kpi-card__title { min-width: 0; flex: 1; }

.kpi-card__label {
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kpi-card__hint {
  font-size: 10px;
  color: #5e6c83;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kpi-card__pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 5px;
  flex-shrink: 0;
}

.kpi-card__pill i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  display: inline-block;
}

.kpi-card__pill--ok { color: #34d399; background: rgba(52, 211, 153, 0.1); }
.kpi-card__pill--ok i { background: #34d399; }
.kpi-card__pill--warn { color: #fbbf24; background: rgba(251, 191, 36, 0.12); }
.kpi-card__pill--warn i { background: #fbbf24; }
.kpi-card__pill--crit { color: #f87171; background: rgba(248, 113, 113, 0.12); }
.kpi-card__pill--crit i { background: #f87171; }
.kpi-card__pill--na { color: #8597b8; background: rgba(133, 151, 184, 0.1); }
.kpi-card__pill--na i { background: #8597b8; }

.kpi-card__value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-top: 6px;
}

.kpi-card__value {
  font-size: 28px;
  line-height: 0.95;
  font-weight: 300;
  color: #e5edf7;
  letter-spacing: 0;
  font-variant-numeric: tabular-nums;
}

.mono {
  font-family: inherit;
  font-feature-settings: normal;
}

.kpi-card__unit { font-size: 11px; color: #5e6c83; }

.kpi-card__spark { height: 38px; }

.kpi-card__foot {
  display: flex;
  justify-content: space-between;
  gap: 6px;
  font-size: 10px;
  margin-top: 2px;
}

.kpi-card__target { color: #5e6c83; }

.kpi-card__delta { color: #9aa7bd; font-weight: 500; }

@media (max-width: 900px) {
  .kpi-strip { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (max-width: 720px) {
  .kpi-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
