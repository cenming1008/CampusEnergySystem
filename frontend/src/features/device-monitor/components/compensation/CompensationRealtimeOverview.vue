<script setup lang="ts">
import type { PropType } from 'vue'
import type { CompensationLevelModel, CompensationMetric } from './types'

defineProps({
  coreMetric: {
    type: Object as PropType<CompensationMetric>,
    required: true,
  },
  pfMetric: {
    type: Object as PropType<CompensationMetric>,
    required: true,
  },
  metrics: {
    type: Array as PropType<CompensationMetric[]>,
    default: () => [],
  },
  level: {
    type: Object as PropType<CompensationLevelModel>,
    required: true,
  },
  extendedHint: {
    type: String,
    default: '',
  },
})

function progressColor(value: string) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return '#64748b'
  if (numeric >= 0.96) return '#22c55e'
  if (numeric >= 0.9) return '#f59e0b'
  return '#ef4444'
}

function progressValue(value: string) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return 0
  return Math.max(0, Math.min(100, numeric * 100))
}

function blockClass(index: number, level: CompensationLevelModel) {
  if (index < level.current) return 'is-active'
  return level.state === 'offline' ? 'is-offline' : 'is-idle'
}
</script>

<template>
  <section class="overview-grid">
    <div class="core-panel">
      <div class="core-panel__caption">
        <span>{{ coreMetric.label }}</span>
        <small>{{ coreMetric.hint }}</small>
      </div>
      <div class="core-panel__value">
        <strong>{{ coreMetric.value }}</strong>
        <small>{{ coreMetric.unit }}</small>
      </div>
      <div class="core-panel__foot">
        <span>当前无功补偿实时数据</span>
      </div>
    </div>

    <div class="overview-side">
      <div class="pf-card">
        <div class="pf-card__head">
          <span>{{ pfMetric.label }}</span>
          <small>{{ pfMetric.hint }}</small>
        </div>
        <div class="pf-card__body">
          <el-progress
            type="dashboard"
            :percentage="progressValue(pfMetric.value)"
            :stroke-width="11"
            :color="progressColor(pfMetric.value)"
            :width="126"
          >
            <template #default>
              <div class="pf-card__value">
                <strong>{{ pfMetric.value }}</strong>
                <small>PF</small>
              </div>
            </template>
          </el-progress>
        </div>
      </div>

      <div class="metric-grid">
        <div
          v-for="item in metrics"
          :key="item.key"
          class="metric-card"
        >
          <span class="metric-card__label">{{ item.label }}</span>
          <div
            class="metric-card__value"
            :class="item.tone ? `tone-${item.tone}` : ''"
          >
            <strong>{{ item.value }}</strong>
            <small v-if="item.unit">{{ item.unit }}</small>
          </div>
          <span class="metric-card__hint">{{ item.hint }}</span>
        </div>

        <div class="metric-card metric-card--level">
          <span class="metric-card__label">当前补偿级数</span>
          <div class="metric-card__value">
            <strong>{{ level.current }} / {{ level.total }}</strong>
            <small>组</small>
          </div>
          <div class="level-blocks">
            <span
              v-for="idx in level.total"
              :key="idx"
              class="level-block"
              :class="blockClass(idx - 1, level)"
            />
          </div>
          <span class="metric-card__hint">{{ level.hint }}</span>
        </div>
      </div>
    </div>
  </section>

  <div
    v-if="extendedHint"
    class="extended-hint"
  >
    {{ extendedHint }}
  </div>
</template>

<style scoped>
.overview-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.92fr) minmax(0, 1.38fr);
  gap: 16px;
}

.core-panel,
.pf-card,
.metric-card {
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.core-panel {
  padding: 22px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 258px;
}

.core-panel__caption {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.core-panel__caption span {
  font-size: 14px;
  color: #c5d2e7;
}

.core-panel__caption small,
.core-panel__foot {
  color: #7f93b2;
  font-size: 12px;
}

.core-panel__value {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.core-panel__value strong {
  font-size: 64px;
  line-height: 1;
  color: #3dd5f3;
  letter-spacing: 0.02em;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
}

.core-panel__value small {
  font-size: 16px;
  color: #8ea0bc;
}

.overview-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pf-card {
  padding: 18px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.pf-card__head {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pf-card__head span {
  font-size: 14px;
  color: #d9e3f2;
}

.pf-card__head small {
  font-size: 12px;
  color: #8ea0bc;
}

.pf-card__body {
  display: flex;
  align-items: center;
  justify-content: center;
}

.pf-card__value {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.pf-card__value strong {
  font-size: 24px;
  color: #f8fafc;
  line-height: 1;
}

.pf-card__value small {
  font-size: 11px;
  color: #8ea0bc;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  min-height: 128px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
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

.tone-success strong,
.tone-success small {
  color: #4ade80;
}

.tone-warning strong,
.tone-warning small {
  color: #fbbf24;
}

.tone-danger strong,
.tone-danger small {
  color: #fb7185;
}

.tone-info strong,
.tone-info small {
  color: #60a5fa;
}

.metric-card--level {
  grid-column: span 2;
}

.level-blocks {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 6px;
}

.level-block {
  height: 12px;
  border-radius: 999px;
  background: rgba(76, 97, 126, 0.34);
  border: 1px solid rgba(108, 130, 160, 0.22);
}

.level-block.is-active {
  background: linear-gradient(90deg, rgba(20, 184, 166, 0.95), rgba(34, 197, 94, 0.95));
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.24);
}

.level-block.is-offline {
  background: rgba(71, 85, 105, 0.72);
}

.extended-hint {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px dashed rgba(90, 109, 138, 0.58);
  background: rgba(13, 21, 34, 0.72);
  color: #8ea0bc;
  font-size: 12px;
}

@media (max-width: 1380px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
