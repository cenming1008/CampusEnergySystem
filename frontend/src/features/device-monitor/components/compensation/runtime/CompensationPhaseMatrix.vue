<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

type CellSeverity = 'ok' | 'warn' | 'crit' | 'na'

interface MatrixCell {
  text: string
  severity: CellSeverity
}

interface MatrixRow {
  label: string
  cells: MatrixCell[]
  system: MatrixCell
}

const props = defineProps({
  telemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
})

const VOLTAGE_THD_THRESHOLD = 5
const CURRENT_THD_THRESHOLD = 5
const TEMP_THRESHOLD = 55

function num(value: number | null | undefined): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function valueCell(value: number | null, unit: string, threshold: number | null, digits = 1): MatrixCell {
  if (value === null) return { text: '--', severity: 'na' }
  let severity: CellSeverity = 'ok'
  if (threshold !== null) {
    if (value > threshold) severity = 'crit'
    else if (value > threshold * 0.8) severity = 'warn'
  }
  return { text: `${value.toFixed(digits)}${unit}`, severity }
}

function systemCell(cells: MatrixCell[]): MatrixCell {
  if (cells.every((c) => c.severity === 'na')) return { text: '--', severity: 'na' }
  if (cells.some((c) => c.severity === 'crit')) return { text: '超限', severity: 'crit' }
  if (cells.some((c) => c.severity === 'warn')) return { text: '异常', severity: 'warn' }
  return { text: '正常', severity: 'ok' }
}

const rows = computed<MatrixRow[]>(() => {
  const t = props.telemetry
  const definitions: Array<{ label: string; unit: string; threshold: number | null; values: Array<number | null> }> = [
    {
      label: '电流幅值',
      unit: ' A',
      threshold: null,
      values: [num(t?.current_a), num(t?.current_b), num(t?.current_c)],
    },
    {
      label: 'V-THD 谐波',
      unit: '%',
      threshold: VOLTAGE_THD_THRESHOLD,
      values: [num(t?.voltage_thd_a), num(t?.voltage_thd_b), num(t?.voltage_thd_c)],
    },
    {
      label: 'I-THD 谐波',
      unit: '%',
      threshold: CURRENT_THD_THRESHOLD,
      values: [num(t?.current_harmonic_a), num(t?.current_harmonic_b), num(t?.current_harmonic_c)],
    },
  ]
  const result = definitions.map((def) => {
    const cells = def.values.map((v) => valueCell(v, def.unit, def.threshold))
    return { label: def.label, cells, system: systemCell(cells) }
  })

  // 柜内温度：单值，铺到系统列
  const temp = num(t?.temperature)
  const tempCell = valueCell(temp, ' °C', TEMP_THRESHOLD, 0)
  result.push({
    label: '柜内温度',
    cells: [
      { text: '—', severity: 'na' },
      { text: '—', severity: 'na' },
      { text: '—', severity: 'na' },
    ],
    system: tempCell,
  })
  return result
})

const alarmCount = computed(() =>
  rows.value.reduce((sum, row) => {
    const cellCount = row.cells.filter((c) => c.severity === 'crit' || c.severity === 'warn').length
    const sysCount = row.system.severity === 'crit' || row.system.severity === 'warn' ? 1 : 0
    return sum + cellCount + sysCount
  }, 0),
)
</script>

<template>
  <section class="matrix-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />三相状态总览</span>
      <span class="matrix-meta">{{ alarmCount }} 项关注</span>
    </header>
    <div class="matrix-body">
      <table class="matrix">
        <thead>
          <tr>
            <th class="matrix-row-head">指标</th>
            <th>A 相</th>
            <th>B 相</th>
            <th>C 相</th>
            <th>系统</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.label">
            <td class="matrix-row-head">{{ row.label }}</td>
            <td v-for="(cell, i) in row.cells" :key="i">
              <span class="matrix-cell" :class="`is-${cell.severity}`">{{ cell.text }}</span>
            </td>
            <td>
              <span class="matrix-cell" :class="`is-${row.system.severity}`">{{ row.system.text }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.matrix-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  min-height: 0;
}
.rt-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rt-card-title {
  display: flex;
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
}
.matrix-meta {
  font-size: 11px;
  color: #5e6c83;
}
.matrix-body {
  padding: 6px 14px 10px;
  flex: 1;
  min-height: 0;
}
.matrix {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}
.matrix th,
.matrix td {
  text-align: center;
  padding: 5px 4px;
  font-size: 11px;
  color: #9aa7bd;
  border-bottom: 1px solid #1f2c41;
}
.matrix th {
  color: #5e6c83;
  font-size: 10px;
  font-weight: 400;
}
.matrix tr:last-child td {
  border-bottom: none;
}
.matrix-row-head {
  text-align: left !important;
  color: #9aa7bd;
}
.matrix-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  height: 20px;
  padding: 0 6px;
  border-radius: 5px;
  font-size: 10px;
  border: 1px solid #1f2c41;
  background: #0b1623;
  color: #5e6c83;
}
.matrix-cell.is-ok {
  color: #6ee7b7;
  border-color: rgba(52, 211, 153, 0.25);
  background: rgba(52, 211, 153, 0.06);
}
.matrix-cell.is-warn {
  color: #fcd34d;
  border-color: rgba(245, 158, 11, 0.4);
  background: rgba(245, 158, 11, 0.1);
}
.matrix-cell.is-crit {
  color: #fda4af;
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.12);
}
.matrix-cell.is-na {
  opacity: 0.5;
}
</style>
