<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationMetric, ModuleStatusModel } from './types'

const props = defineProps({
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
  moduleStatus: {
    type: Object as PropType<ModuleStatusModel>,
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

function stateTagText(state: CompensationMetric['state']) {
  if (state === 'live') return '● 实时'
  if (state === 'mock') return '◑ 估算'
  if (state === 'missing') return '✕ 缺测'
  if (state === 'offline') return '⊘ 离线'
  if (state === 'unconfigured') return '○ 待配置'
  return ''
}

function stateTagType(state: CompensationMetric['state']) {
  if (state === 'live') return 'success'
  if (state === 'mock') return 'warning'
  if (state === 'missing' || state === 'offline') return 'danger'
  if (state === 'unconfigured') return 'info'
  return 'info'
}

const capacityUsagePct = computed(() => {
  const found = props.metrics.find(m => m.key === 'capacityUsage')
  if (!found) return 0
  const n = Number(found.value)
  return Number.isNaN(n) ? 0 : Math.max(0, Math.min(100, n))
})
</script>

<template>
  <section class="bento-overview">
    <!-- TOP: PF 仪表盘 | 无功功率 Hero -->
    <div class="bento-top">
      <div class="bento-pf">
        <div class="metric-label-row">
          <el-tooltip :content="pfMetric.hint" placement="top" :disabled="!pfMetric.hint">
            <span class="bento-pf__label">{{ pfMetric.label }}</span>
          </el-tooltip>
          <el-tag
            v-if="pfMetric.state && pfMetric.state !== 'live'"
            size="small"
            effect="plain"
            :type="stateTagType(pfMetric.state)"
          >
            {{ stateTagText(pfMetric.state) }}
          </el-tag>
        </div>
        <div class="bento-pf__gauge">
          <el-progress
            type="dashboard"
            :percentage="progressValue(pfMetric.value)"
            :stroke-width="11"
            :color="progressColor(pfMetric.value)"
            :width="140"
          >
            <template #default>
              <div class="bento-pf__inner">
                <strong>{{ pfMetric.value }}</strong>
                <small>PF</small>
              </div>
            </template>
          </el-progress>
        </div>
      </div>

      <div class="bento-hero">
        <div class="bento-hero__top">
          <div class="metric-label-row">
            <el-tooltip :content="coreMetric.hint" placement="top" :disabled="!coreMetric.hint">
              <span class="bento-hero__label">{{ coreMetric.label }}</span>
            </el-tooltip>
            <el-tag
              v-if="coreMetric.state && coreMetric.state !== 'live'"
              size="small"
              effect="plain"
              :type="stateTagType(coreMetric.state)"
            >
              {{ stateTagText(coreMetric.state) }}
            </el-tag>
          </div>
        </div>
        <div class="bento-hero__value">
          <strong>{{ coreMetric.value }}</strong>
          <small>{{ coreMetric.unit }}</small>
        </div>
        <div class="bento-hero__bar-row">
          <span class="bento-hero__bar-label">补偿容量</span>
          <div class="bento-hero__bar-track">
            <div
              class="bento-hero__bar-fill"
              :style="{ width: `${capacityUsagePct}%` }"
            />
          </div>
          <span class="bento-hero__bar-pct">{{ capacityUsagePct.toFixed(1) }}%</span>
        </div>
        <div class="bento-hero__pills">
          <span
            class="module-pill"
            :class="moduleStatus.runningModuleCount > 0 ? 'module-pill--running' : 'module-pill--standby'"
          >
            {{ moduleStatus.runningModuleCount }}/{{ moduleStatus.totalModuleCount }} {{ moduleStatus.unitLabel }}运行
          </span>
        </div>
      </div>
    </div>

    <!-- BOTTOM STRIP: 6 指标 -->
    <div class="bento-strip">
      <div
        v-for="item in metrics"
        :key="item.key"
        class="strip-cell"
      >
        <div class="metric-label-row metric-label-row--compact">
          <el-tooltip :content="item.hint" placement="top" :disabled="!item.hint">
            <span class="strip-cell__label">{{ item.label }}</span>
          </el-tooltip>
          <el-tag
            v-if="item.state && item.state !== 'live'"
            size="small"
            effect="plain"
            :type="stateTagType(item.state)"
          >
            {{ stateTagText(item.state) }}
          </el-tag>
        </div>
        <div
          class="strip-cell__value"
          :class="item.tone ? `tone-${item.tone}` : ''"
        >
          <strong>{{ item.value }}</strong>
          <small v-if="item.unit">{{ item.unit }}</small>
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
/* ── Bento container ─────────────────────────────────────────── */
.bento-overview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Top zone: PF gauge | Hero ───────────────────────────────── */
.bento-top {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 12px;
  min-height: 200px;
}

.bento-pf,
.bento-hero {
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

/* PF panel */
.bento-pf {
  padding: 20px 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
}

.bento-pf__label {
  font-size: 13px;
  color: #c5d2e7;
}

.metric-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}

.metric-label-row--compact {
  align-items: flex-start;
}

.bento-pf__gauge {
  display: flex;
  align-items: center;
  justify-content: center;
}

.bento-pf__inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.bento-pf__inner strong {
  font-size: 26px;
  color: #f8fafc;
  line-height: 1;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
}

.bento-pf__inner small {
  font-size: 11px;
  color: #8ea0bc;
}

/* Hero panel */
.bento-hero {
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 10px;
}

.bento-hero__top {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bento-hero__label {
  font-size: 13px;
  color: #c5d2e7;
}

.bento-hero__value {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.bento-hero__value strong {
  font-size: 56px;
  line-height: 1;
  color: #3dd5f3;
  letter-spacing: 0.02em;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
}

.bento-hero__value small {
  font-size: 16px;
  color: #8ea0bc;
}

/* Capacity bar */
.bento-hero__bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bento-hero__bar-label {
  font-size: 11px;
  color: #7f93b2;
  white-space: nowrap;
  flex-shrink: 0;
}

.bento-hero__bar-track {
  flex: 1;
  height: 4px;
  background: rgba(53, 72, 97, 0.5);
  border-radius: 999px;
  overflow: hidden;
}

.bento-hero__bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #06b6d4);
  border-radius: 999px;
  transition: width 0.4s ease;
}

.bento-hero__bar-pct {
  font-size: 11px;
  color: #8ea0bc;
  white-space: nowrap;
  flex-shrink: 0;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
}

/* Module pill */
.bento-hero__pills {
  display: flex;
  gap: 8px;
}

.module-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
}

.module-pill--running {
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.module-pill--standby {
  background: rgba(76, 97, 126, 0.2);
  border: 1px solid rgba(76, 97, 126, 0.4);
  color: #8ea0bc;
}

/* ── Bottom strip: 6 metric cards ────────────────────────────── */
.bento-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
}

.strip-cell {
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-top: 3px solid rgba(59, 130, 246, 0.25);
  border-radius: 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 6px;
  min-height: 88px;
}

.strip-cell__label {
  font-size: 11px;
  color: #8ea0bc;
  line-height: 1.3;
}

.strip-cell__value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.strip-cell__value strong {
  font-size: 20px;
  line-height: 1;
  color: #f5f7fb;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
}

.strip-cell__value small {
  font-size: 10px;
  color: #7f93b2;
}


/* Tone modifiers */
.tone-success .strip-cell__value strong { color: #4ade80; }
.tone-warning .strip-cell__value strong { color: #fbbf24; }
.tone-danger  .strip-cell__value strong { color: #fb7185; }
.tone-info    .strip-cell__value strong { color: #60a5fa; }

/* Extended hint */
.extended-hint {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px dashed rgba(90, 109, 138, 0.58);
  background: rgba(13, 21, 34, 0.72);
  color: #8ea0bc;
  font-size: 12px;
}

/* ── Responsive ──────────────────────────────────────────────── */
@media (max-width: 1380px) {
  .bento-top {
    grid-template-columns: 1fr;
  }

  .bento-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .bento-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
