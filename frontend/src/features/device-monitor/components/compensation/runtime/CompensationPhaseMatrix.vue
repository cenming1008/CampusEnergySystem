<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

type CellSeverity = 'ok' | 'warn' | 'crit' | 'na'

type MatrixCell =
  | { display: 'value'; text: string }
  | { display: 'chip'; text: string; severity: CellSeverity }

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

function num(value: number | null | undefined): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function plainCell(text: string): MatrixCell {
  return { display: 'value', text }
}

function phaseStatusCell(flag: boolean | null | undefined): MatrixCell {
  if (flag === true) return { display: 'chip', text: '超前', severity: 'warn' }
  if (flag === false) return { display: 'chip', text: '正常', severity: 'ok' }
  return { display: 'chip', text: '--', severity: 'na' }
}

function valueCell(value: number | null, unit: string, threshold: number | null, digits = 1): MatrixCell {
  if (value === null) return { display: 'chip', text: '--', severity: 'na' }
  let severity: CellSeverity = 'ok'
  if (threshold !== null) {
    if (value > threshold) severity = 'crit'
    else if (value > threshold * 0.8) severity = 'warn'
  }
  return { display: 'chip', text: `${value.toFixed(digits)}${unit}`, severity }
}

function systemCell(cells: MatrixCell[]): MatrixCell {
  const chips = cells.filter((c): c is Extract<MatrixCell, { display: 'chip' }> => c.display === 'chip')
  if (chips.every((c) => c.severity === 'na')) return { display: 'chip', text: '--', severity: 'na' }
  if (chips.some((c) => c.severity === 'crit')) return { display: 'chip', text: '超限', severity: 'crit' }
  if (chips.some((c) => c.severity === 'warn')) return { display: 'chip', text: '异常', severity: 'warn' }
  return { display: 'chip', text: '正常', severity: 'ok' }
}

function fmtValue(value: number | null | undefined, digits: number): string {
  const n = num(value)
  return n === null ? '--' : n.toFixed(digits)
}

function meanCell(values: Array<number | null | undefined>, digits: number): MatrixCell {
  const defined = values.map(num).filter((v): v is number => v !== null)
  if (defined.length === 0) return plainCell('--')
  const mean = defined.reduce((a, b) => a + b, 0) / defined.length
  return plainCell(mean.toFixed(digits))
}

function sumCell(values: Array<number | null | undefined>, digits: number): MatrixCell {
  const defined = values.map(num).filter((v): v is number => v !== null)
  if (defined.length === 0) return plainCell('--')
  const sum = defined.reduce((a, b) => a + b, 0)
  return plainCell(sum.toFixed(digits))
}

const rows = computed<MatrixRow[]>(() => {
  const t = props.telemetry

  // --- 量测行 ---
  const measurementRows: MatrixRow[] = [
    {
      label: '电压 (V)',
      cells: [plainCell(fmtValue(t?.voltage_a, 1)), plainCell(fmtValue(t?.voltage_b, 1)), plainCell(fmtValue(t?.voltage_c, 1))],
      system: meanCell([t?.voltage_a, t?.voltage_b, t?.voltage_c], 1),
    },
    {
      label: '电流 (A)',
      cells: [plainCell(fmtValue(t?.current_a, 1)), plainCell(fmtValue(t?.current_b, 1)), plainCell(fmtValue(t?.current_c, 1))],
      system: meanCell([t?.current_a, t?.current_b, t?.current_c], 1),
    },
    {
      label: '有功 (kW)',
      cells: [plainCell(fmtValue(t?.active_power_a, 1)), plainCell(fmtValue(t?.active_power_b, 1)), plainCell(fmtValue(t?.active_power_c, 1))],
      system: sumCell([t?.active_power_a, t?.active_power_b, t?.active_power_c], 1),
    },
    {
      label: '无功 (kvar)',
      cells: [plainCell(fmtValue(t?.reactive_power_a, 1)), plainCell(fmtValue(t?.reactive_power_b, 1)), plainCell(fmtValue(t?.reactive_power_c, 1))],
      system: sumCell([t?.reactive_power_a, t?.reactive_power_b, t?.reactive_power_c], 1),
    },
    {
      label: '视在 (kVA)',
      cells: [plainCell(fmtValue(t?.apparent_power_a, 1)), plainCell(fmtValue(t?.apparent_power_b, 1)), plainCell(fmtValue(t?.apparent_power_c, 1))],
      system: sumCell([t?.apparent_power_a, t?.apparent_power_b, t?.apparent_power_c], 1),
    },
    {
      label: '功率因数',
      cells: [plainCell(fmtValue(t?.power_factor_a, 3)), plainCell(fmtValue(t?.power_factor_b, 3)), plainCell(fmtValue(t?.power_factor_c, 3))],
      system: meanCell([t?.power_factor_a, t?.power_factor_b, t?.power_factor_c], 3),
    },
  ]

  // --- 指标行 ---
  const leadingCells: MatrixCell[] = [
    phaseStatusCell(t?.leading_a),
    phaseStatusCell(t?.leading_b),
    phaseStatusCell(t?.leading_c),
  ]
  const vThdCells: MatrixCell[] = [
    valueCell(num(t?.voltage_thd_a), '%', VOLTAGE_THD_THRESHOLD),
    valueCell(num(t?.voltage_thd_b), '%', VOLTAGE_THD_THRESHOLD),
    valueCell(num(t?.voltage_thd_c), '%', VOLTAGE_THD_THRESHOLD),
  ]
  const iThdCells: MatrixCell[] = [
    valueCell(num(t?.current_harmonic_a), '%', CURRENT_THD_THRESHOLD),
    valueCell(num(t?.current_harmonic_b), '%', CURRENT_THD_THRESHOLD),
    valueCell(num(t?.current_harmonic_c), '%', CURRENT_THD_THRESHOLD),
  ]
  const indicatorRows: MatrixRow[] = [
    { label: '相位状态', cells: leadingCells, system: systemCell(leadingCells) },
    { label: 'V-THD (%)', cells: vThdCells, system: systemCell(vThdCells) },
    { label: 'I-THD (%)', cells: iThdCells, system: systemCell(iThdCells) },
  ]

  // --- 柜温行 ---
  const temp = num(t?.temperature)
  const tempText = temp === null ? '--' : `${temp.toFixed(0)} °C`
  const tempRow: MatrixRow = {
    label: '柜温 (°C)',
    cells: [plainCell('—'), plainCell('—'), plainCell('—')],
    system: plainCell(tempText),
  }

  return [...measurementRows, ...indicatorRows, tempRow]
})

const alarmCount = computed(() =>
  rows.value.reduce((sum, row) => {
    const phaseConcern = row.cells.filter(
      (c): c is Extract<MatrixCell, { display: 'chip' }> => c.display === 'chip',
    ).filter((c) => c.severity === 'crit' || c.severity === 'warn').length
    return sum + phaseConcern
  }, 0),
)
</script>

<template>
  <section class="matrix-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />三相量测总览</span>
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
              <span v-if="cell.display === 'chip'" class="matrix-cell" :class="`is-${cell.severity}`">{{ cell.text }}</span>
              <span v-else class="matrix-value" :class="{ 'is-missing': cell.text === '--' }">{{ cell.text }}</span>
            </td>
            <td>
              <span v-if="row.system.display === 'chip'" class="matrix-cell" :class="`is-${row.system.severity}`">{{ row.system.text }}</span>
              <span v-else class="matrix-value" :class="{ 'is-missing': row.system.text === '--' }">{{ row.system.text }}</span>
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
.matrix-value {
  display: inline-block;
  font-size: 11px;
  color: #e5edf7;
  font-variant-numeric: tabular-nums;
}
.matrix-value.is-missing {
  color: #5e6c83;
}
</style>
