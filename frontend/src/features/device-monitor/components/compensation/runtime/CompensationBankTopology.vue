<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'
import {
  getCircuitGroups,
  resolvedConfiguredCounts,
  toBits,
} from '../circuitStateUtils'
import type { CompensationCircuitPick, CompensationCircuitSlotState } from '../types'

interface CircuitProfileView {
  splitCircuitCount?: number
  commonCircuitCount?: number
  phaseACircuitTotalCount?: number
  phaseBCircuitTotalCount?: number
  phaseCCircuitTotalCount?: number
  common1CircuitTotalCount?: number
  common2CircuitTotalCount?: number
  common3CircuitTotalCount?: number
}

const props = defineProps({
  telemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
  circuitProfile: {
    type: Object as PropType<CircuitProfileView | null>,
    default: null,
  },
})

const emit = defineEmits<{ (e: 'pick', circuit: CompensationCircuitPick): void }>()

const BUS_META: Array<{
  phase: 'A' | 'B' | 'C' | 'COMMON'
  commonGroup: 1 | 2 | 3 | null
  phaseClass: string
  chip: string
  sectionLabel: string | null
}> = [
  { phase: 'A', commonGroup: null, phaseClass: 'a', chip: 'A', sectionLabel: '分相补偿' },
  { phase: 'B', commonGroup: null, phaseClass: 'b', chip: 'B', sectionLabel: null },
  { phase: 'C', commonGroup: null, phaseClass: 'c', chip: 'C', sectionLabel: null },
  { phase: 'COMMON', commonGroup: 1, phaseClass: 'n', chip: 'N', sectionLabel: '共补回路' },
  { phase: 'COMMON', commonGroup: 2, phaseClass: 'n', chip: 'N', sectionLabel: null },
  { phase: 'COMMON', commonGroup: 3, phaseClass: 'n', chip: 'N', sectionLabel: null },
]

const buses = computed(() => {
  const t = props.telemetry
  const groups = t
    ? getCircuitGroups(t)
    : Array.from({ length: 6 }, () => ({ label: '', mask: null as number | null, alarmFlag: null }))
  const counts = resolvedConfiguredCounts({
    configuredSplitCircuitCount: props.circuitProfile?.splitCircuitCount ?? null,
    configuredCommonCircuitCount: props.circuitProfile?.commonCircuitCount ?? null,
    phaseACircuitTotalCount: props.circuitProfile?.phaseACircuitTotalCount ?? null,
    phaseBCircuitTotalCount: props.circuitProfile?.phaseBCircuitTotalCount ?? null,
    phaseCCircuitTotalCount: props.circuitProfile?.phaseCCircuitTotalCount ?? null,
    common1CircuitTotalCount: props.circuitProfile?.common1CircuitTotalCount ?? null,
    common2CircuitTotalCount: props.circuitProfile?.common2CircuitTotalCount ?? null,
    common3CircuitTotalCount: props.circuitProfile?.common3CircuitTotalCount ?? null,
  })

  return BUS_META.map((meta, i) => {
    const group = groups[i]
    const slots = toBits(group.mask, counts[i])
    const phaseAlarm = Boolean(group.alarmFlag)
    const runningCount = slots.filter((slot) => slot === true).length
    const configuredCount = slots.filter((slot) => slot !== null).length
    return {
      ...meta,
      label: group.label || meta.chip,
      phaseAlarm,
      runningCount,
      configuredCount,
      caps: slots.map((slot, slotIdx) => {
        const state: CompensationCircuitSlotState =
          slot === true ? 'on' : slot === false ? 'off' : 'unconfigured'
        return { slotIdx, index: slotIdx + 1, state }
      }),
    }
  })
})

const summary = computed(() => {
  let running = 0
  let total = 0
  for (const bus of buses.value) {
    for (const cap of bus.caps) {
      if (cap.state === 'unconfigured') continue
      total += 1
      if (cap.state === 'on') running += 1
    }
  }
  const rate = total > 0 ? Math.round((running / total) * 1000) / 10 : 0
  return { running, total, rate }
})

function handlePick(
  bus: (typeof buses.value)[number],
  cap: { index: number; state: CompensationCircuitSlotState },
) {
  if (cap.state === 'unconfigured') return
  emit('pick', {
    groupLabel: bus.label,
    phase: bus.phase,
    commonGroup: bus.commonGroup,
    index: cap.index,
    state: cap.state,
    phaseAlarm: bus.phaseAlarm,
  })
}
</script>

<template>
  <section class="topo-card">
    <header class="rt-card-head">
      <span class="rt-card-title">
        <span class="rt-accent" />电容器组拓扑
        <span class="rt-sub">分补 + 公补 · {{ summary.running }} 路投运</span>
      </span>
      <div class="topo-head-actions">
        <slot name="header-actions" />
        <div class="topo-legend">
          <span><i class="sw on" />投入</span>
          <span><i class="sw off" />切除</span>
          <span><i class="sw empty" />未配置</span>
        </div>
      </div>
    </header>

    <div class="topo-body">
      <div class="topo">
        <template v-for="bus in buses" :key="`${bus.phase}-${bus.commonGroup}`">
          <div v-if="bus.sectionLabel" class="topo-section-label">{{ bus.sectionLabel }}</div>
          <div class="topo-bus" data-test="topo-bus">
            <div class="topo-phase">
              <span class="topo-chip" :class="bus.phaseClass">{{ bus.chip }}</span>
              <span class="topo-phase-label">
                {{ bus.label }}
                <span v-if="bus.phaseAlarm" class="topo-phase-alarm" title="该相存在告警">!</span>
              </span>
            </div>
            <div class="topo-rail">
              <button
                v-for="cap in bus.caps"
                :key="cap.slotIdx"
                type="button"
                class="topo-cap"
                :class="{
                  'is-on': cap.state === 'on',
                  'is-off': cap.state === 'off',
                  'is-empty': cap.state === 'unconfigured',
                }"
                :disabled="cap.state === 'unconfigured'"
                @click="handlePick(bus, cap)"
              >
                <span class="topo-cap-idx">#{{ cap.index }}</span>
              </button>
            </div>
            <div class="topo-row-summary">
              <b>{{ bus.runningCount }}/{{ bus.configuredCount }}</b>
            </div>
          </div>
        </template>
      </div>
      <div class="topo-summary">
        <span><b>{{ summary.running }} / {{ summary.total }}</b> 路投运</span>
        <span>投运率 <b>{{ summary.rate }}%</b></span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.topo-card {
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
.rt-sub {
  color: #5e6c83;
  font-weight: 400;
}
.topo-head-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}
.topo-legend {
  display: flex;
  gap: 8px;
  font-size: 10px;
  color: #5e6c83;
}
.topo-legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 20px;
  padding: 0 7px;
  border: 1px solid rgba(31, 44, 65, 0.75);
  border-radius: 999px;
  background: rgba(11, 22, 35, 0.42);
}
.topo-legend .sw {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  border: 1px solid #1f2c41;
}
.topo-legend .sw.on { background: #22d3a6; border-color: rgba(52, 211, 153, 0.72); }
.topo-legend .sw.off { background: #0b1623; }
.topo-legend .sw.empty { border-style: dashed; }
.topo-body {
  display: flex;
  flex-direction: column;
  padding: 8px 14px;
  flex: 1;
  min-height: 0;
}
.topo {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}
.topo-section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 18px;
  margin-top: 2px;
  color: #7b8ca5;
  font-size: 10px;
  font-weight: 600;
}
.topo-section-label::after {
  content: "";
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(31, 44, 65, 0.9), rgba(31, 44, 65, 0.08));
}
.topo-bus {
  display: flex;
  align-items: center;
  gap: 10px;
}
.topo-phase {
  width: 96px;
  display: flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
}
.topo-chip {
  width: 22px;
  height: 22px;
  border-radius: 5px;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 11px;
  color: #07101c;
}
.topo-chip.a { background: #facc15; }
.topo-chip.b { background: #34d399; }
.topo-chip.c { background: #f87171; }
.topo-chip.n { background: #a78bfa; }
.topo-phase-label {
  font-size: 11px;
  color: #e5edf7;
}
.topo-phase-alarm {
  display: inline-grid;
  place-items: center;
  width: 14px;
  height: 14px;
  margin-left: 2px;
  border-radius: 50%;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
}
.topo-rail {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 6px;
  position: relative;
}
.topo-rail::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 2px;
  background: linear-gradient(90deg, rgba(34, 211, 238, 0.2), rgba(34, 211, 238, 0.04));
}
.topo-cap {
  position: relative;
  height: 36px;
  border-radius: 6px;
  background: #0b1623;
  border: 1px solid #1f2c41;
  color: #9aa7bd;
  cursor: pointer;
  display: grid;
  place-items: center;
}
.topo-cap-idx {
  font-size: 12px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.topo-cap:hover:not(:disabled) {
  border-color: #22d3ee;
}
.topo-cap.is-on {
  background: linear-gradient(180deg, rgba(34, 211, 166, 0.34), rgba(20, 184, 166, 0.15));
  border-color: rgba(45, 212, 191, 0.78);
  color: #b7f7e6;
  box-shadow: 0 0 0 1px rgba(45, 212, 191, 0.18), 0 0 16px rgba(20, 184, 166, 0.2);
}
.topo-cap.is-off {
  background: rgba(8, 19, 31, 0.84);
  color: #78889f;
}
.topo-cap.is-empty {
  border-style: dashed;
  opacity: 0.28;
  cursor: not-allowed;
}
.topo-row-summary {
  width: 42px;
  flex-shrink: 0;
  text-align: right;
  color: #5e6c83;
  font-size: 10px;
  font-variant-numeric: tabular-nums;
}
.topo-row-summary b {
  color: #c4d3e7;
  font-weight: 600;
}
.topo-summary {
  display: flex;
  gap: 16px;
  padding-top: 8px;
  font-size: 11px;
  color: #9aa7bd;
}
.topo-summary b {
  color: #e5edf7;
  font-variant-numeric: tabular-nums;
}
</style>
