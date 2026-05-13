<script setup lang="ts">
import { computed } from 'vue'
import type { StorageMetric } from './types'

const props = defineProps<{
  socValue: string
  socState: string
  powerValue: string
  powerState: string
  powerDirection: 'charging' | 'discharging' | 'idle' | 'unknown'
  metrics: StorageMetric[]
}>()

const socNumeric = computed(() => {
  const n = Number(props.socValue)
  return Number.isNaN(n) ? 0 : Math.max(0, Math.min(100, n))
})

const socColor = computed(() => {
  if (socNumeric.value >= 80) return '#22c55e'
  if (socNumeric.value >= 30) return '#f59e0b'
  return '#ef4444'
})

const powerDirectionLabel = computed(() => {
  if (props.powerDirection === 'charging') return '充电'
  if (props.powerDirection === 'discharging') return '放电'
  if (props.powerDirection === 'idle') return '静止'
  return '--'
})

const powerColor = computed(() => {
  if (props.powerDirection === 'charging') return '#3dd5f3'
  if (props.powerDirection === 'discharging') return '#4ade80'
  return '#8ea0bc'
})

const powerPillClass = computed(() => {
  if (props.powerDirection === 'charging') return 'pill--charging'
  if (props.powerDirection === 'discharging') return 'pill--discharging'
  return 'pill--idle'
})

function stateTagText(state: string) {
  if (state === 'live') return '● 实时'
  if (state === 'mock') return '◑ 估算'
  if (state === 'missing') return '✕ 缺测'
  if (state === 'offline') return '⊘ 离线'
  return ''
}

function stateTagType(state: string) {
  if (state === 'live') return 'success'
  if (state === 'mock') return 'warning'
  return 'danger'
}
</script>

<template>
  <section class="bento-overview">
    <!-- TOP: SOC 仪表盘 | 功率 Hero -->
    <div class="bento-top">
      <!-- SOC 仪表 -->
      <div class="bento-pf">
        <div class="metric-label-row">
          <span class="bento-pf__label">荷电状态（SOC）</span>
          <el-tag
            v-if="socState !== 'live'"
            size="small"
            effect="plain"
            :type="stateTagType(socState)"
          >
            {{ stateTagText(socState) }}
          </el-tag>
        </div>
        <div class="bento-pf__gauge">
          <el-progress
            type="dashboard"
            :percentage="socNumeric"
            :stroke-width="11"
            :color="socColor"
            :width="140"
          >
            <template #default>
              <div class="bento-pf__inner">
                <strong>{{ socState === 'live' ? `${socNumeric.toFixed(1)}` : '--' }}</strong>
                <small>%</small>
              </div>
            </template>
          </el-progress>
        </div>
      </div>

      <!-- 功率 Hero -->
      <div class="bento-hero">
        <div class="bento-hero__top">
          <div class="metric-label-row">
            <span class="bento-hero__label">有功功率</span>
            <el-tag
              v-if="powerState !== 'live'"
              size="small"
              effect="plain"
              :type="stateTagType(powerState)"
            >
              {{ stateTagText(powerState) }}
            </el-tag>
          </div>
        </div>
        <div class="bento-hero__value">
          <strong :style="{ color: powerColor }">{{ powerValue !== '--' ? powerValue : '--' }}</strong>
          <small>kW</small>
        </div>
        <div class="bento-hero__pills">
          <span
            class="direction-pill"
            :class="powerPillClass"
          >
            {{ powerDirectionLabel }}
          </span>
        </div>
      </div>
    </div>

    <!-- BOTTOM STRIP: 4 指标 -->
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
</template>

<style scoped>
.bento-overview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Top zone ────────────────────────────────────────────────── */
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
  letter-spacing: 0.02em;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
  transition: color 0.3s ease;
}

.bento-hero__value small {
  font-size: 16px;
  color: #8ea0bc;
}

.bento-hero__pills {
  display: flex;
  gap: 8px;
}

.direction-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
}

.pill--charging {
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: #7dd3fc;
}

.pill--discharging {
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.pill--idle {
  background: rgba(76, 97, 126, 0.2);
  border: 1px solid rgba(76, 97, 126, 0.4);
  color: #8ea0bc;
}

/* ── Bottom strip ────────────────────────────────────────────── */
.bento-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.strip-cell {
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-top: 3px solid rgba(34, 197, 94, 0.22);
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

.tone-success .strip-cell__value strong { color: #4ade80; }
.tone-warning .strip-cell__value strong { color: #fbbf24; }
.tone-danger  .strip-cell__value strong { color: #fb7185; }
.tone-info    .strip-cell__value strong { color: #60a5fa; }

/* ── Responsive ──────────────────────────────────────────────── */
@media (max-width: 1380px) {
  .bento-top {
    grid-template-columns: 1fr;
  }

  .bento-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
