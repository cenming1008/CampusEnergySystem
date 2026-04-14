<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { ModuleStatusModel, ModuleStateTone } from './types'

const props = defineProps({
  model: {
    type: Object as PropType<ModuleStatusModel>,
    required: true,
  },
})

const stateLabels: Record<ModuleStateTone, string> = {
  running: '运行',
  standby: '待机',
  alarm: '告警',
  fault: '故障',
}

const stateSummary = computed(() => {
  const counts = props.model.moduleStates.reduce<Record<ModuleStateTone, number>>(
    (acc, state) => {
      acc[state] += 1
      return acc
    },
    { running: 0, standby: 0, alarm: 0, fault: 0 },
  )

  const summaryParts = [
    counts.running > 0 ? `当前 ${counts.running} 个${props.model.unitLabel}运行` : '',
    counts.standby > 0 ? `${counts.standby} 个${props.model.unitLabel}待机` : '',
    counts.alarm > 0 ? `${counts.alarm} 个${props.model.unitLabel}告警` : '',
    counts.fault > 0 ? `${counts.fault} 个${props.model.unitLabel}故障` : '',
  ].filter(Boolean)

  return {
    counts,
    text: summaryParts.join('，'),
  }
})
</script>

<template>
  <div class="metric-card metric-card--module-status">
    <span class="metric-card__label">{{ model.title }}</span>
    <div class="metric-card__value">
      <strong>{{ model.runningModuleCount }} / {{ model.totalModuleCount }}</strong>
      <small>{{ model.unitLabel }}</small>
    </div>
    <span class="metric-card__hint">{{ stateSummary.text }}</span>
    <div
      class="module-blocks"
      :style="{ gridTemplateColumns: `repeat(${model.totalModuleCount}, minmax(0, 1fr))` }"
    >
      <span
        v-for="(state, index) in model.moduleStates"
        :key="`${state}-${index}`"
        class="module-block"
        :class="`is-${state}`"
        :title="`${model.unitLabel} ${index + 1}：${stateLabels[state]}`"
      />
    </div>
    <span class="metric-card__hint">{{ model.hint }}</span>
  </div>
</template>

<style scoped>
.metric-card {
  min-height: 128px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.metric-card--module-status {
  grid-column: span 2;
}

.metric-card__label {
  font-size: 12px;
  color: #8ea0bc;
}

.metric-card__value {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.metric-card__value strong {
  font-size: 28px;
  line-height: 1.1;
  color: #f5f7fb;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
}

.metric-card__value small,
.metric-card__hint {
  font-size: 11px;
  color: #7f93b2;
}

.module-blocks {
  display: grid;
  gap: 6px;
}

.module-block {
  height: 12px;
  border-radius: 999px;
  border: 1px solid rgba(108, 130, 160, 0.22);
}

.module-block.is-running {
  background: linear-gradient(90deg, rgba(20, 184, 166, 0.95), rgba(34, 197, 94, 0.95));
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.24);
}

.module-block.is-standby {
  background: rgba(76, 97, 126, 0.34);
}

.module-block.is-alarm {
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.92), rgba(251, 191, 36, 0.92));
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.2);
}

.module-block.is-fault {
  background: linear-gradient(90deg, rgba(239, 68, 68, 0.95), rgba(244, 63, 94, 0.95));
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.22);
}
</style>
