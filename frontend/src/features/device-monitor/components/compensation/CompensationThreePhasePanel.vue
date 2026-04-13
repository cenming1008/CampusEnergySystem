<script setup lang="ts">
import type { PropType } from 'vue'
import type { SVGTelemetry } from '@/api/svg'

defineProps({
  telemetry: {
    type: Object as PropType<SVGTelemetry | null>,
    default: null,
  },
})

function fmt(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return '--'
  return Number(value).toFixed(digits)
}

function directionLabel(dir: string | null | undefined): string {
  if (dir === 'inductive') return '感性（吸收无功）'
  if (dir === 'capacitive') return '容性（发出无功）'
  return dir ?? '--'
}
</script>

<template>
  <section class="threephase-panel">
    <div class="threephase-panel__head">
      <h3>三相电气量</h3>
      <span>来自 SVG 遥测扩展数据</span>
    </div>

    <template v-if="telemetry">
      <!-- 三相电压 -->
      <div class="group-label">三相电压</div>
      <div class="phase-grid">
        <div class="phase-card">
          <span class="phase-card__phase">A 相</span>
          <strong class="phase-card__val">{{ fmt(telemetry.voltage_a) }}</strong>
          <small class="phase-card__unit">V</small>
        </div>
        <div class="phase-card">
          <span class="phase-card__phase">B 相</span>
          <strong class="phase-card__val">{{ fmt(telemetry.voltage_b) }}</strong>
          <small class="phase-card__unit">V</small>
        </div>
        <div class="phase-card">
          <span class="phase-card__phase">C 相</span>
          <strong class="phase-card__val">{{ fmt(telemetry.voltage_c) }}</strong>
          <small class="phase-card__unit">V</small>
        </div>
      </div>

      <!-- 三相电流 -->
      <div class="group-label">三相电流</div>
      <div class="phase-grid">
        <div class="phase-card">
          <span class="phase-card__phase">A 相</span>
          <strong class="phase-card__val">{{ fmt(telemetry.current_a) }}</strong>
          <small class="phase-card__unit">A</small>
        </div>
        <div class="phase-card">
          <span class="phase-card__phase">B 相</span>
          <strong class="phase-card__val">{{ fmt(telemetry.current_b) }}</strong>
          <small class="phase-card__unit">A</small>
        </div>
        <div class="phase-card">
          <span class="phase-card__phase">C 相</span>
          <strong class="phase-card__val">{{ fmt(telemetry.current_c) }}</strong>
          <small class="phase-card__unit">A</small>
        </div>
      </div>

      <!-- 其他扩展量 -->
      <div class="group-label">其他量测</div>
      <div class="extra-grid">
        <div class="extra-row">
          <span>电网频率</span>
          <strong>{{ fmt(telemetry.frequency, 2) }} <small>Hz</small></strong>
        </div>
        <div class="extra-row">
          <span>SVG 无功输出</span>
          <strong>{{ fmt(telemetry.svg_reactive_output) }} <small>kVAR</small></strong>
        </div>
        <div class="extra-row">
          <span>补偿容量利用率</span>
          <strong>{{ fmt(telemetry.capacity_utilization) }} <small>%</small></strong>
        </div>
        <div class="extra-row">
          <span>直流母线电压</span>
          <strong>{{ fmt(telemetry.dc_bus_voltage) }} <small>V</small></strong>
        </div>
        <div class="extra-row">
          <span>输出方向</span>
          <strong>{{ directionLabel(telemetry.output_direction) }}</strong>
        </div>
      </div>
    </template>

    <div
      v-else
      class="empty-hint"
    >
      暂无三相遥测数据，请确认 SVG 设备已上报遥测记录。
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
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #5d7699;
  margin-bottom: 8px;
  margin-top: 14px;
}

.group-label:first-of-type {
  margin-top: 0;
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
  font-size: 11px;
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
  font-size: 11px;
  color: #5d7699;
}

.extra-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.extra-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(41, 57, 77, 0.55);
}

.extra-row:last-child {
  border-bottom: none;
}

.extra-row span {
  font-size: 12px;
  color: #8ea0bc;
}

.extra-row strong {
  font-size: 13px;
  color: #e2ecf9;
}

.extra-row strong small {
  font-size: 11px;
  color: #5d7699;
  margin-left: 3px;
}

.empty-hint {
  padding: 20px 0;
  text-align: center;
  font-size: 13px;
  color: #5d7699;
}
</style>
