<script setup lang="ts">
import { computed } from 'vue'
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
      <h3>
        电容回路投切状态
        <el-tooltip content="来自 JKWF-LCD 投切寄存器（0x01~0x03）" placement="top">
          <span class="head-info-icon">ℹ</span>
        </el-tooltip>
      </h3>
      <div class="legend-bar">
        <span class="legend-item legend-item--on"><i />投入</span>
        <span class="legend-item legend-item--off"><i />切除</span>
        <span class="legend-item legend-item--unconfigured"><i />未配置</span>
        <span class="legend-item legend-item--na"><i />等待回读</span>
      </div>
    </div>

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
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 16px;
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
  color: var(--text-label);
  font-size: var(--font-caption);
  cursor: default;
  vertical-align: middle;
}

/* Legend：始终内联展示，与标题同行（窄屏换行） */
.legend-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-caption);
  color: #c5d2e7;
}

/* 图例样本：与 step-badge 视觉等价，便于直观对照 */
.legend-item i {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 5px;
  font-style: normal;
  font-size: var(--font-caption);
  font-weight: 700;
  font-family: 'SFMono-Regular', monospace;
  flex-shrink: 0;
}

.legend-item--on i {
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.55);
  color: #6ee7a4;
}
.legend-item--on i::before { content: '✓'; }

.legend-item--off i {
  background: rgba(30, 48, 70, 0.4);
  border: 1px solid rgba(74, 96, 128, 0.65);
  color: #8aa0bf;
}
.legend-item--off i::before { content: '–'; }

.legend-item--unconfigured i {
  background: rgba(33, 42, 55, 0.24);
  border: 1px dashed rgba(140, 155, 180, 0.35);
  color: #8294b3;
}
.legend-item--unconfigured i::before { content: '·'; }

.legend-item--na i {
  background: rgba(30, 48, 70, 0.2);
  border: 1px dashed rgba(74, 96, 128, 0.5);
  color: #6b82a4;
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
  font-size: var(--font-caption);
  color: #b4c4dc;
  font-weight: 600;
}

.group-card__count {
  font-size: var(--font-caption);
  color: var(--text-label);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.group-card__progress {
  height: 6px;
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
  font-size: var(--font-caption);
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(220, 80, 80, 0.25);
  color: #fca5a5;
  border: 1px solid rgba(220, 80, 80, 0.45);
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.step-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  min-width: var(--touch-target);
  min-height: var(--touch-target);
  padding: 0 4px;
  border-radius: 5px;
  font-size: var(--font-caption);
  font-family: 'SFMono-Regular', monospace;
  cursor: default;
  transition: background 0.15s;
}

/* 颜色冗余：通=✓ / 断=– / 未配置=· / 等待回读=空（保留色块差异） */
.step-badge--on::before {
  content: '✓';
  font-weight: 700;
  line-height: 1;
}

.step-badge--off::before {
  content: '–';
  font-weight: 700;
  line-height: 1;
}

.step-badge--unconfigured::before {
  content: '·';
  font-weight: 700;
  line-height: 1;
}

.step-badge--on {
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.55);
  color: #6ee7a4;
}

.step-badge--off {
  background: rgba(30, 48, 70, 0.4);
  border: 1px solid rgba(74, 96, 128, 0.65);
  color: #8aa0bf;
}

.step-badge--na {
  background: rgba(30, 48, 70, 0.2);
  border: 1px dashed rgba(74, 96, 128, 0.5);
  color: #6b82a4;
}

.step-badge--unconfigured {
  background: rgba(33, 42, 55, 0.24);
  border: 1px dashed rgba(140, 155, 180, 0.35);
  color: #8294b3;
  opacity: 0.85;
}

/* Grouped flags */
.flags-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--divider);
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

</style>
