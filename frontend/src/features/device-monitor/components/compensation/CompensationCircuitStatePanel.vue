<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

const props = defineProps({
  capacitorBankTelemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
  configuredSplitCircuitCount: {
    type: Number,
    default: null,
  },
  configuredCommonCircuitCount: {
    type: Number,
    default: null,
  },
})

interface CircuitGroup {
  label: string
  mask: number | null | undefined
  alarmFlag?: boolean | null
}

type SlotState = boolean | null | 'unconfigured'

function getCircuitGroups(t: CompensationCapacitorBankTelemetry): CircuitGroup[] {
  return [
    { label: 'A 相分补', mask: t.circuit_state_phase_a, alarmFlag: t.overvoltage_alarm_a },
    { label: 'B 相分补', mask: t.circuit_state_phase_b, alarmFlag: t.overvoltage_alarm_b },
    { label: 'C 相分补', mask: t.circuit_state_phase_c, alarmFlag: t.overvoltage_alarm_c },
    { label: '公补 1-8', mask: t.circuit_state_common_1 },
    { label: '公补 9-16', mask: t.circuit_state_common_2 },
    { label: '公补 17-24', mask: t.circuit_state_common_3 },
  ]
}

function distributeBalanced(total: number | null | undefined, buckets: number, maxPerBucket: number): number[] {
  const normalized = Math.max(0, Math.min(Number(total || 0), buckets * maxPerBucket))
  const base = Math.floor(normalized / buckets)
  const remainder = normalized % buckets
  return Array.from({ length: buckets }, (_, index) => Math.min(maxPerBucket, base + (index < remainder ? 1 : 0)))
}

function distributeSequential(total: number | null | undefined, bucketSizes: number[]): number[] {
  let remaining = Math.max(0, Number(total || 0))
  return bucketSizes.map((size) => {
    const allocated = Math.min(size, remaining)
    remaining -= allocated
    return allocated
  })
}

function resolvedConfiguredCounts(props: {
  configuredSplitCircuitCount?: number | null
  configuredCommonCircuitCount?: number | null
}) {
  return [
    ...distributeBalanced(props.configuredSplitCircuitCount, 3, 8),
    ...distributeSequential(props.configuredCommonCircuitCount, [8, 8, 8]),
  ]
}

/** 将 8-bit mask 展开为 8 个槽位状态，bit0 = 第 1 路 */
function toBits(mask: number | null | undefined, configuredCount: number): SlotState[] {
  return Array.from({ length: 8 }, (_, i) => {
    if (i >= configuredCount) return 'unconfigured'
    if (mask == null) return null
    return Boolean(mask & (1 << i))
  })
}

function stepLabel(groupIdx: number, bitIdx: number): string {
  const base = groupIdx >= 3 ? (groupIdx - 3) * 8 + 1 : 1
  return `${base + bitIdx}`
}

const groupConfiguredCounts = computed(() => resolvedConfiguredCounts(props))
</script>

<template>
  <section class="circuit-panel">
    <div class="circuit-panel__head">
      <h3>电容回路投切状态</h3>
      <span>来自 JKWF-LCD 投切寄存器（0x01~0x03）</span>
    </div>

    <template v-if="capacitorBankTelemetry">
      <div class="groups-grid">
        <div
          v-for="(group, gi) in getCircuitGroups(capacitorBankTelemetry)"
          :key="group.label"
          class="group-card"
          :class="{ 'group-card--alarm': group.alarmFlag }"
        >
          <div class="group-card__label">
            {{ group.label }}
            <span
              v-if="group.alarmFlag"
              class="alarm-badge"
            >过压</span>
          </div>
          <div class="steps-grid">
            <div
              v-for="(on, bi) in toBits(group.mask, groupConfiguredCounts[gi] || 0)"
              :key="bi"
              class="step-badge"
              :class="on === 'unconfigured' ? 'step-badge--unconfigured' : on === null ? 'step-badge--na' : on ? 'step-badge--on' : 'step-badge--off'"
              :title="on === 'unconfigured' ? `第 ${stepLabel(gi, bi)} 路 — 未配置` : on === null ? '无数据' : on ? `第 ${stepLabel(gi, bi)} 路 — 已投入` : `第 ${stepLabel(gi, bi)} 路 — 已切除`"
            >
              {{ stepLabel(gi, bi) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 状态标志摘要 -->
      <div class="flags-row">
        <span
          v-for="(flag, label) in {
            'A超前': capacitorBankTelemetry.leading_a,
            'B超前': capacitorBankTelemetry.leading_b,
            'C超前': capacitorBankTelemetry.leading_c,
            'A欠流': capacitorBankTelemetry.undercurrent_a,
            'B欠流': capacitorBankTelemetry.undercurrent_b,
            'C欠流': capacitorBankTelemetry.undercurrent_c,
            'V_THD告警A': capacitorBankTelemetry.voltage_thd_alarm_a,
            'V_THD告警B': capacitorBankTelemetry.voltage_thd_alarm_b,
            'V_THD告警C': capacitorBankTelemetry.voltage_thd_alarm_c,
            'I_THD告警A': capacitorBankTelemetry.current_thd_alarm_a,
            'I_THD告警B': capacitorBankTelemetry.current_thd_alarm_b,
            'I_THD告警C': capacitorBankTelemetry.current_thd_alarm_c,
            '温度告警': capacitorBankTelemetry.temp_alarm,
          }"
          :key="label"
          class="flag-chip"
          :class="flag ? 'flag-chip--active' : 'flag-chip--ok'"
        >
          {{ label }}
        </span>
      </div>
    </template>

    <div
      v-else
      class="empty-hint"
    >
      暂无投切状态数据，请确认 JKWF-LCD 设备已上报遥测记录。
    </div>
  </section>
</template>

<style scoped>
.circuit-panel {
  padding: 18px 20px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
}

.circuit-panel__head {
  margin-bottom: 16px;
}

.circuit-panel__head h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.circuit-panel__head span {
  display: block;
  margin-top: 4px;
  color: #8ea0bc;
  font-size: 12px;
}

.groups-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.group-card {
  padding: 10px 12px;
  background: rgba(22, 36, 55, 0.7);
  border: 1px solid rgba(53, 72, 97, 0.5);
  border-radius: 10px;
}

.group-card--alarm {
  border-color: rgba(220, 80, 80, 0.5);
  background: rgba(60, 22, 22, 0.4);
}

.group-card__label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #7f93b2;
  font-weight: 600;
  margin-bottom: 8px;
}

.alarm-badge {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(220, 80, 80, 0.25);
  color: #f87171;
  border: 1px solid rgba(220, 80, 80, 0.4);
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 5px;
}

.step-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 26px;
  border-radius: 5px;
  font-size: 11px;
  font-family: 'SFMono-Regular', monospace;
  cursor: default;
  transition: background 0.15s;
}

.step-badge--on {
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.45);
  color: #4ade80;
}

.step-badge--off {
  background: rgba(30, 48, 70, 0.4);
  border: 1px solid rgba(53, 72, 97, 0.4);
  color: #4a6080;
}

.step-badge--na {
  background: rgba(30, 48, 70, 0.2);
  border: 1px dashed rgba(53, 72, 97, 0.3);
  color: #344c68;
}

.step-badge--unconfigured {
  background: rgba(33, 42, 55, 0.24);
  border: 1px dashed rgba(120, 135, 156, 0.25);
  color: #5d6e86;
  opacity: 0.72;
}

/* 状态标志行 */
.flags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 14px;
}

.flag-chip {
  padding: 3px 8px;
  border-radius: 5px;
  font-size: 11px;
}

.flag-chip--active {
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.4);
  color: #fbbf24;
}

.flag-chip--ok {
  background: rgba(30, 48, 70, 0.4);
  border: 1px solid rgba(53, 72, 97, 0.4);
  color: #4a6080;
}

.empty-hint {
  padding: 20px 0;
  text-align: center;
  font-size: 13px;
  color: #5d7699;
}
</style>
