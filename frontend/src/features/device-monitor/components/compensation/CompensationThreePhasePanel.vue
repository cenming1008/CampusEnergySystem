<script setup lang="ts">
import { computed, type PropType } from 'vue'
import type {
  CompensationCapacitorBankTelemetry,
  CompensationSvgTelemetry,
} from '@/api/compensation'

const props = defineProps({
  svgTelemetry: {
    type: Object as PropType<CompensationSvgTelemetry | null>,
    default: null,
  },
  capacitorBankTelemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
  isCapacitorBank: {
    type: Boolean,
    default: false,
  },
})

// 优先展示 JKWF-LCD 数据，回退到 SVG 数据
const activeData = computed(() => props.capacitorBankTelemetry ?? props.svgTelemetry)
const showCapacitorBankTables = computed(() => props.isCapacitorBank || !!props.capacitorBankTelemetry)

function fmt(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return '--'
  return Number(value).toFixed(digits)
}

function directionLabel(dir: string | null | undefined): string {
  if (dir === 'inductive') return '感性（吸收无功）'
  if (dir === 'capacitive') return '容性（发出无功）'
  return dir ?? '--'
}

function subtitle(): string {
  if (props.capacitorBankTelemetry) return '当前三相电压、电流与功率分布'
  if (props.svgTelemetry) return '当前三相电气量与补偿输出'
  return '当前实时快照'
}

function panelTitle(): string {
  if (props.capacitorBankTelemetry) return '三相电气快照'
  if (props.svgTelemetry) return '三相电气快照'
  return '三相电气快照'
}

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 19)
}
</script>

<template>
  <section class="threephase-panel">
    <div class="threephase-panel__head">
      <h3>{{ panelTitle() }}</h3>
      <span>{{ subtitle() }}</span>
    </div>

    <!-- 三相电压 -->
    <div class="group-label">三相电压</div>
    <div class="phase-grid">
      <div class="phase-card" style="--phase-accent: #60a5fa;">
        <span class="phase-card__phase phase-card__phase--colored">A 相</span>
        <strong class="phase-card__val">{{ fmt(activeData?.voltage_a) }}</strong>
        <small class="phase-card__unit">V</small>
      </div>
      <div class="phase-card" style="--phase-accent: #fbbf24;">
        <span class="phase-card__phase phase-card__phase--colored">B 相</span>
        <strong class="phase-card__val">{{ fmt(activeData?.voltage_b) }}</strong>
        <small class="phase-card__unit">V</small>
      </div>
      <div class="phase-card" style="--phase-accent: #f87171;">
        <span class="phase-card__phase phase-card__phase--colored">C 相</span>
        <strong class="phase-card__val">{{ fmt(activeData?.voltage_c) }}</strong>
        <small class="phase-card__unit">V</small>
      </div>
    </div>

    <!-- 三相电流 -->
    <div class="group-label">三相电流</div>
    <div class="phase-grid">
      <div class="phase-card" style="--phase-accent: #60a5fa;">
        <span class="phase-card__phase phase-card__phase--colored">A 相</span>
        <strong class="phase-card__val">{{ fmt(activeData?.current_a) }}</strong>
        <small class="phase-card__unit">A</small>
      </div>
      <div class="phase-card" style="--phase-accent: #fbbf24;">
        <span class="phase-card__phase phase-card__phase--colored">B 相</span>
        <strong class="phase-card__val">{{ fmt(activeData?.current_b) }}</strong>
        <small class="phase-card__unit">A</small>
      </div>
      <div class="phase-card" style="--phase-accent: #f87171;">
        <span class="phase-card__phase phase-card__phase--colored">C 相</span>
        <strong class="phase-card__val">{{ fmt(activeData?.current_c) }}</strong>
        <small class="phase-card__unit">A</small>
      </div>
    </div>

    <!-- JKWF-LCD 专有：三相功率 -->
    <template v-if="showCapacitorBankTables">
      <div class="group-label">三相功率</div>
      <div class="power-table">
        <div class="power-table__head">
          <span></span>
          <span>有功 (kW)</span>
          <span>无功 (kvar)</span>
          <span>视在 (kVA)</span>
          <span>功率因数</span>
        </div>
        <div
          v-for="(phase, i) in ['A', 'B', 'C']"
          :key="phase"
          class="power-table__row"
          :style="{ '--phase-accent': i === 0 ? '#60a5fa' : i === 1 ? '#fbbf24' : '#f87171' }"
        >
          <span class="power-table__phase power-table__phase--colored">{{ phase }} 相</span>
          <span>{{ fmt(i === 0 ? capacitorBankTelemetry?.active_power_a : i === 1 ? capacitorBankTelemetry?.active_power_b : capacitorBankTelemetry?.active_power_c) }}</span>
          <span>{{ fmt(i === 0 ? capacitorBankTelemetry?.reactive_power_a : i === 1 ? capacitorBankTelemetry?.reactive_power_b : capacitorBankTelemetry?.reactive_power_c) }}</span>
          <span>{{ fmt(i === 0 ? capacitorBankTelemetry?.apparent_power_a : i === 1 ? capacitorBankTelemetry?.apparent_power_b : capacitorBankTelemetry?.apparent_power_c) }}</span>
          <span>{{ fmt(i === 0 ? capacitorBankTelemetry?.power_factor_a : i === 1 ? capacitorBankTelemetry?.power_factor_b : capacitorBankTelemetry?.power_factor_c, 3) }}</span>
        </div>
      </div>

      <!-- 谐波 -->
      <div class="group-label">谐波分析（THD）</div>
      <div class="harmonic-grid">
        <div class="harmonic-row harmonic-row--head">
          <span></span>
          <span style="color: #60a5fa;">A 相</span>
          <span style="color: #fbbf24;">B 相</span>
          <span style="color: #f87171;">C 相</span>
        </div>
        <div class="harmonic-row">
          <span class="harmonic-label">电压 THD</span>
          <span>{{ fmt(capacitorBankTelemetry?.voltage_thd_a, 1) }} %</span>
          <span>{{ fmt(capacitorBankTelemetry?.voltage_thd_b, 1) }} %</span>
          <span>{{ fmt(capacitorBankTelemetry?.voltage_thd_c, 1) }} %</span>
        </div>
        <div class="harmonic-row">
          <span class="harmonic-label">谐波电流幅值</span>
          <span>{{ fmt(capacitorBankTelemetry?.current_harmonic_a, 1) }} A</span>
          <span>{{ fmt(capacitorBankTelemetry?.current_harmonic_b, 1) }} A</span>
          <span>{{ fmt(capacitorBankTelemetry?.current_harmonic_c, 1) }} A</span>
        </div>
      </div>
    </template>

    <!-- 其他扩展量 -->
    <div class="group-label">其他量测</div>
    <div class="extra-grid">
      <div class="extra-row">
        <span>电网频率</span>
        <strong>{{ fmt(activeData?.frequency, 2) }} <small>Hz</small></strong>
      </div>
      <div class="extra-row">
        <span>采样时间</span>
        <strong>{{ formatTimestamp(activeData?.timestamp) }}</strong>
      </div>
      <template v-if="!showCapacitorBankTables && svgTelemetry">
        <div class="extra-row">
          <span>SVG 无功输出</span>
          <strong>{{ fmt((svgTelemetry as CompensationSvgTelemetry).svg_reactive_output) }} <small>kVAR</small></strong>
        </div>
        <div class="extra-row">
          <span>补偿容量利用率</span>
          <strong>{{ fmt((svgTelemetry as CompensationSvgTelemetry).capacity_utilization) }} <small>%</small></strong>
        </div>
        <div class="extra-row">
          <span>直流母线电压</span>
          <strong>{{ fmt((svgTelemetry as CompensationSvgTelemetry).dc_bus_voltage) }} <small>V</small></strong>
        </div>
        <div class="extra-row">
          <span>输出方向</span>
          <strong>{{ directionLabel((svgTelemetry as CompensationSvgTelemetry).output_direction) }}</strong>
        </div>
      </template>
      <template v-if="showCapacitorBankTables">
        <div class="extra-row">
          <span>柜内温度</span>
          <strong>{{ fmt(capacitorBankTelemetry?.temperature, 1) }} <small>°C</small></strong>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
.threephase-panel {
  padding: 18px 20px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
}

.threephase-panel__head {
  margin-bottom: 16px;
}

.threephase-panel__head h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.threephase-panel__head span {
  display: block;
  margin-top: 4px;
  color: #8ea0bc;
  font-size: 12px;
}

.group-label {
  font-size: var(--font-caption);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-label);
  margin-bottom: 8px;
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid var(--divider);
}

.group-label:first-of-type {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.phase-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 4px;
}

.phase-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px 10px;
  background: rgba(30, 48, 70, 0.55);
  border: 1px solid rgba(53, 72, 97, 0.6);
  border-radius: 10px;
}

.phase-card__phase {
  font-size: var(--font-caption);
  color: #7f93b2;
  letter-spacing: 0.04em;
}

.phase-card__val {
  font-size: 22px;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
  color: #e2ecf9;
  line-height: 1;
}

.phase-card__unit {
  font-size: var(--font-caption);
  color: var(--text-label);
}

/* 三相功率表格 */
.power-table {
  background: rgba(22, 36, 55, 0.6);
  border: 1px solid rgba(53, 72, 97, 0.5);
  border-radius: 10px;
  overflow: hidden;
}

.power-table__head,
.power-table__row {
  display: grid;
  grid-template-columns: 48px repeat(4, 1fr);
  align-items: center;
}

.power-table__head {
  padding: 6px 12px;
  background: rgba(30, 48, 70, 0.8);
  font-size: var(--font-caption);
  color: var(--text-label);
  font-weight: 600;
  text-align: right;
}

.power-table__head span:first-child {
  text-align: left;
}

.power-table__row {
  padding: 8px 12px;
  font-size: 12px;
  color: #c5d5e8;
  text-align: right;
  border-top: 1px solid rgba(41, 57, 77, 0.4);
}

.power-table__phase {
  color: #7f93b2;
  font-size: var(--font-caption);
  text-align: left;
}

/* 谐波表格 */
.harmonic-grid {
  background: rgba(22, 36, 55, 0.6);
  border: 1px solid rgba(53, 72, 97, 0.5);
  border-radius: 10px;
  overflow: hidden;
}

.harmonic-row {
  display: grid;
  grid-template-columns: 100px repeat(3, 1fr);
  align-items: center;
  padding: 8px 12px;
  font-size: 12px;
  color: #c5d5e8;
  text-align: right;
  border-top: 1px solid rgba(41, 57, 77, 0.4);
}

.harmonic-row--head {
  background: rgba(30, 48, 70, 0.8);
  font-size: var(--font-caption);
  color: var(--text-label);
  font-weight: 600;
  border-top: none;
}

.harmonic-label {
  text-align: left;
  color: #8ea0bc;
}

/* 其他量测 */
.extra-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 24px;
  row-gap: 0;
}

.extra-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--divider);
}

.extra-row:last-child,
.extra-row:nth-last-child(2):nth-child(odd) {
  border-bottom: none;
}

.extra-row span {
  font-size: var(--font-caption);
  color: var(--text-label);
}

.extra-row strong {
  font-size: 13px;
  color: #e2ecf9;
}

.extra-row strong small {
  font-size: var(--font-caption);
  color: var(--text-label);
  margin-left: 3px;
}

.empty-hint {
  padding: 24px 0 10px;
  text-align: center;
  color: var(--text-label);
}

.empty-hint strong {
  display: block;
  font-size: 14px;
  color: #d8e4f4;
  font-weight: 600;
}

.empty-hint p {
  max-width: 560px;
  margin: 10px auto 0;
  font-size: 12px;
  line-height: 1.7;
}

/* 相位颜色编码 */
.phase-card {
  border-top: 3px solid var(--phase-accent, rgba(53, 72, 97, 0.6));
}

.phase-card__phase--colored {
  color: var(--phase-accent, #7f93b2);
}

.power-table__row {
  border-left: 3px solid var(--phase-accent, transparent);
}

.power-table__phase--colored {
  color: var(--phase-accent, #7f93b2);
}
</style>
