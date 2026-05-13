<script setup lang="ts">
import { computed, ref } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'
import {
  countOnSlots,
  getFlagGroups,
  getCircuitGroups,
  hasAnyActiveFlag,
  resolvedConfiguredCounts,
  toBits,
} from './circuitStateUtils'

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
  phaseACircuitTotalCount: {
    type: Number,
    default: null,
  },
  phaseBCircuitTotalCount: {
    type: Number,
    default: null,
  },
  phaseCCircuitTotalCount: {
    type: Number,
    default: null,
  },
  common1CircuitTotalCount: {
    type: Number,
    default: null,
  },
  common2CircuitTotalCount: {
    type: Number,
    default: null,
  },
  common3CircuitTotalCount: {
    type: Number,
    default: null,
  },
})

const legendVisible = ref(false)
const placeholderCircuitGroups = [
  { label: 'A相分补', alarmFlag: false, mask: 0 },
  { label: 'B相分补', alarmFlag: false, mask: 0 },
  { label: 'C相分补', alarmFlag: false, mask: 0 },
  { label: '公补 1-8', alarmFlag: false, mask: 0 },
  { label: '公补 9-16', alarmFlag: false, mask: 0 },
  { label: '公补 17-24', alarmFlag: false, mask: 0 },
]

function stepLabel(groupIdx: number, bitIdx: number): string {
  const base = groupIdx >= 3 ? (groupIdx - 3) * 8 + 1 : 1
  return `${base + bitIdx}`
}

const groupConfiguredCounts = computed(() => resolvedConfiguredCounts(props))
const renderedCircuitGroups = computed(() =>
  props.capacitorBankTelemetry ? getCircuitGroups(props.capacitorBankTelemetry) : placeholderCircuitGroups,
)
</script>

<template>
  <section class="circuit-panel">
    <div class="circuit-panel__head">
      <div>
        <h3>
          电容回路投切状态
          <el-tooltip content="来自 JKWF-LCD 投切寄存器（0x01~0x03）" placement="top">
            <span class="head-info-icon">ℹ</span>
          </el-tooltip>
        </h3>
      </div>
      <button
        class="legend-toggle"
        @click="legendVisible = !legendVisible"
      >
        {{ legendVisible ? '收起图例' : '图例说明' }}
      </button>
    </div>

    <transition name="legend-fade">
      <div
        v-if="legendVisible"
        class="legend-bar"
      >
        <span class="legend-item legend-item--on"><i />投入</span>
        <span class="legend-item legend-item--off"><i />切除</span>
        <span class="legend-item legend-item--unconfigured"><i />未配置</span>
        <span class="legend-item legend-item--na"><i />等待回读</span>
      </div>
    </transition>

    <div class="groups-grid">
      <div
        v-for="(group, gi) in renderedCircuitGroups"
        :key="group.label"
        class="group-card"
        :class="{ 'group-card--alarm': group.alarmFlag, 'group-card--placeholder': !capacitorBankTelemetry }"
      >
        <div class="group-card__header">
          <div class="group-card__label">
            {{ group.label }}
            <span
              v-if="group.alarmFlag"
              class="alarm-badge"
            >过压</span>
          </div>
          <span class="group-card__count">
            <template v-if="capacitorBankTelemetry && groupConfiguredCounts[gi] !== null">
              {{ countOnSlots(group.mask, groupConfiguredCounts[gi]) }}/{{ groupConfiguredCounts[gi] }} 投入
            </template>
            <template v-else-if="capacitorBankTelemetry">等待 MQTT 回读</template>
            <template v-else>-/- 投入</template>
          </span>
        </div>
        <div class="group-card__progress">
          <div
            class="group-card__progress-fill"
            :style="{
              width: capacitorBankTelemetry && groupConfiguredCounts[gi]
                ? `${(countOnSlots(group.mask, groupConfiguredCounts[gi]) / groupConfiguredCounts[gi]!) * 100}%`
                : '0%',
              background: group.alarmFlag ? '#f87171' : '#22c55e',
            }"
          />
        </div>
        <div class="steps-grid">
          <div
            v-for="(on, bi) in capacitorBankTelemetry ? toBits(group.mask, groupConfiguredCounts[gi]) : Array.from({ length: 8 }, () => null)"
            :key="bi"
            class="step-badge"
            :class="on === 'unconfigured' ? 'step-badge--unconfigured' : on === null ? 'step-badge--na' : on ? 'step-badge--on' : 'step-badge--off'"
            :title="capacitorBankTelemetry ? (on === 'unconfigured' ? `第 ${stepLabel(gi, bi)} 路 — 未配置` : on === null ? '等待 MQTT 回读回路配置' : on ? `第 ${stepLabel(gi, bi)} 路 — 已投入` : `第 ${stepLabel(gi, bi)} 路 — 已切除`) : '暂无投切数据'"
          >
            {{ capacitorBankTelemetry ? stepLabel(gi, bi) : '-' }}
          </div>
        </div>
      </div>
    </div>

    <!-- 分组告警标志 -->
    <div
      v-if="capacitorBankTelemetry"
      class="flags-section"
    >
      <div
        v-for="group in getFlagGroups(capacitorBankTelemetry)"
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
        v-if="!hasAnyActiveFlag(getFlagGroups(capacitorBankTelemetry))"
        class="flags-all-ok"
      >
        所有标志正常
      </div>
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
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.circuit-panel__head h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.head-info-icon {
  display: inline-block;
  margin-left: 6px;
  color: #5d7699;
  font-size: 12px;
  cursor: default;
  vertical-align: middle;
}

.legend-toggle {
  flex-shrink: 0;
  padding: 4px 10px;
  border: 1px solid rgba(53, 72, 97, 0.6);
  border-radius: 6px;
  background: transparent;
  color: #8ea0bc;
  font-size: 11px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.legend-toggle:hover {
  color: #c5d2e7;
  border-color: rgba(90, 120, 160, 0.6);
}

/* Legend */
.legend-bar {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 14px;
  padding: 10px 12px;
  background: rgba(14, 22, 34, 0.5);
  border: 1px solid rgba(53, 72, 97, 0.4);
  border-radius: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #aebbd0;
}

.legend-item i {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 3px;
  flex-shrink: 0;
}

.legend-item--on i {
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.45);
}
.legend-item--off i {
  background: rgba(30, 48, 70, 0.4);
  border: 1px solid rgba(53, 72, 97, 0.4);
}
.legend-item--unconfigured i {
  background: rgba(33, 42, 55, 0.24);
  border: 1px dashed rgba(120, 135, 156, 0.25);
}
.legend-item--na i {
  background: rgba(30, 48, 70, 0.2);
  border: 1px dashed rgba(53, 72, 97, 0.3);
}

.legend-fade-enter-active,
.legend-fade-leave-active {
  transition: opacity 0.18s, transform 0.18s;
}
.legend-fade-enter-from,
.legend-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Group cards */
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

.group-card--placeholder {
  background: rgba(22, 36, 55, 0.46);
  border-color: rgba(53, 72, 97, 0.42);
}

.group-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 6px;
}

.group-card__label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #7f93b2;
  font-weight: 600;
}

.group-card__count {
  font-size: 10px;
  color: #5d7699;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.group-card__progress {
  height: 3px;
  background: rgba(53, 72, 97, 0.4);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 8px;
}

.group-card__progress-fill {
  height: 100%;
  border-radius: 999px;
  opacity: 0.7;
  transition: width 0.3s ease;
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

/* Grouped flags */
.flags-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(41, 57, 77, 0.5);
}

.flag-group {
  display: flex;
  align-items: center;
  gap: 5px;
}

.flag-group__label {
  font-size: 10px;
  color: #4a6080;
  font-weight: 600;
  white-space: nowrap;
}

.flag-group__label--active {
  color: #fbbf24;
}

.flag-group__chips {
  display: flex;
  gap: 3px;
}

.flag-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}

.flag-chip--active {
  background: rgba(251, 191, 36, 0.15);
  border: 1px solid rgba(251, 191, 36, 0.4);
  color: #fbbf24;
}

.flag-chip--ok {
  background: rgba(30, 48, 70, 0.35);
  border: 1px solid rgba(53, 72, 97, 0.35);
  color: #3f5572;
}

.flags-all-ok {
  margin-left: auto;
  font-size: 11px;
  color: #4ade80;
  opacity: 0.7;
}

</style>
