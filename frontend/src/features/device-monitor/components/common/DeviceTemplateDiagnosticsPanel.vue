<script setup lang="ts">
import { computed } from 'vue'
import type { MonitorTemplateDiagnostics } from '@/api/deviceMonitor'

const props = defineProps<{
  diagnostics: MonitorTemplateDiagnostics
}>()

const statusMeta = computed(() => {
  const map = {
    passed: { label: '接入完整', tone: 'success' },
    partial: { label: '部分接入', tone: 'warning' },
    missing: { label: '指标缺失', tone: 'danger' },
    offline: { label: '采集离线', tone: 'danger' },
  } as const
  return map[props.diagnostics.overall_status] || map.partial
})

const metricCoverageText = computed(() =>
  `${props.diagnostics.metric_coverage.live}/${props.diagnostics.metric_coverage.total}`,
)

const offlineHint = computed(() =>
  props.diagnostics.overall_status === 'offline'
    ? '采集离线，当前按最后一次可用模板结果展示接入检查'
    : '',
)

const ingestionStatusText = computed(() => {
  const status = props.diagnostics.ingestion_health?.ingestion_status
  if (props.diagnostics.overall_status === 'offline' || status === 'offline') return '采集离线'
  if (status === 'online') return '在线采集'
  if (status === 'degraded') return '采集异常'
  return '待确认'
})

const fieldLabelMap: Record<string, string> = {
  reactive_power: '无功功率',
  power_factor: '功率因数',
  voltage: '母线电压',
  current: '线电流',
  running_circuit_count: '投入回路',
  capacity_utilization: '容量利用率',
  flow_rate: '瞬时流量',
  consumption: '累计读数',
  pressure: '压力',
  temperature: '温度',
  supply_temp: '供水温度',
  return_temp: '回水温度',
  temperature_delta: '供回水温差',
  soc: 'SOC',
  soh: 'SOH',
  active_power: '有功功率',
  run_state: '运行状态',
  cell_temp_max: '最高温度',
  charge_energy_today: '今日充电量',
  discharge_energy_today: '今日放电量',
  cabinet_temperature: '柜内温度',
  module_count: '模块数',
}

const panelLabelMap: Record<string, string> = {
  three_phase: '三相快照',
  circuit_state: '回路状态',
  control_profile: '控制档案',
  control_summary: '控制摘要',
  module_status: '模块状态',
  device_profile: '设备档案',
  storage_realtime: '储能实时',
  storage_trend: '储能趋势',
  storage_status: '储能状态',
}

function readableKey(key: string) {
  const label = fieldLabelMap[key]
  return label ? `${label}（${key}）` : key
}

function readablePanel(key: string) {
  const label = panelLabelMap[key]
  return label ? `${label}（${key}）` : key
}

function joinReadableKeys(keys: string[]) {
  return keys.length ? keys.map(readableKey).join('、') : '无'
}

function joinReadablePanels(keys: string[]) {
  return keys.length ? keys.map(readablePanel).join('、') : '无'
}

const missingKeysText = computed(() => {
  const coverage = props.diagnostics.metric_coverage
  if (coverage.missing_keys.length) return joinReadableKeys(coverage.missing_keys)
  if (coverage.missing > 0) return '缺失字段待后端确认'
  return '无'
})

</script>

<template>
  <section class="template-diagnostics">
    <div class="template-diagnostics__header">
      <div>
        <span>接入诊断</span>
        <strong>{{ diagnostics.display_name || diagnostics.template_key }}</strong>
      </div>
      <em :class="`template-diagnostics__status template-diagnostics__status--${statusMeta.tone}`">
        {{ statusMeta.label }}
      </em>
    </div>

    <p
      v-if="offlineHint"
      class="template-diagnostics__hint"
    >
      {{ offlineHint }}
    </p>

    <div class="template-diagnostics__grid">
      <div class="template-diagnostics__item template-diagnostics__item--template">
        <span>模板 key</span>
        <strong>{{ diagnostics.template_key }}</strong>
      </div>
      <div class="template-diagnostics__item">
        <span>采集状态</span>
        <strong>{{ ingestionStatusText }}</strong>
      </div>
      <div class="template-diagnostics__item">
        <span>指标覆盖</span>
        <strong>{{ metricCoverageText }}</strong>
      </div>
      <div class="template-diagnostics__item">
        <span>可绘趋势</span>
        <strong>{{ diagnostics.trend_coverage.drawable_keys.length }}</strong>
      </div>
      <div class="template-diagnostics__item">
        <span>专属面板</span>
        <strong>{{ diagnostics.panel_coverage.specific_panels.length }}</strong>
      </div>
    </div>

    <dl class="template-diagnostics__details">
      <div>
        <dt>等待字段</dt>
        <dd>{{ missingKeysText }}</dd>
      </div>
      <div>
        <dt>可绘图字段</dt>
        <dd>{{ joinReadableKeys(diagnostics.trend_coverage.drawable_keys) }}</dd>
      </div>
      <div>
        <dt>暂不可绘图</dt>
        <dd>{{ joinReadableKeys(diagnostics.trend_coverage.unsupported_keys) }}</dd>
      </div>
      <div>
        <dt>专属面板</dt>
        <dd>{{ joinReadablePanels(diagnostics.panel_coverage.specific_panels) }}</dd>
      </div>
    </dl>
  </section>
</template>

<style scoped>
.template-diagnostics {
  padding: 16px;
  display: grid;
  gap: 14px;
  color: #dbe7f6;
  background: #131d2b;
  border: 1px solid #243244;
  border-radius: 8px;
}

.template-diagnostics__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.template-diagnostics__hint {
  margin: 0;
  padding: 8px 10px;
  color: #fca5a5;
  font-size: 12px;
  line-height: 1.45;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.18);
  border-radius: 8px;
}

.template-diagnostics__header div {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.template-diagnostics__header span,
.template-diagnostics__item span,
.template-diagnostics__details dt {
  color: #8ea0bc;
  font-size: 12px;
}

.template-diagnostics__header strong {
  color: #f8fafc;
  font-size: 16px;
  overflow-wrap: anywhere;
}

.template-diagnostics__status {
  padding: 4px 8px;
  flex: 0 0 auto;
  font-style: normal;
  font-size: 12px;
  border-radius: 999px;
}

.template-diagnostics__status--success {
  color: #86efac;
  background: rgba(34, 197, 94, 0.12);
}

.template-diagnostics__status--warning {
  color: #facc15;
  background: rgba(234, 179, 8, 0.12);
}

.template-diagnostics__status--danger {
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.12);
}

.template-diagnostics__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(96px, 0.45fr);
  gap: 10px;
}

.template-diagnostics__item {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.template-diagnostics__item--template {
  grid-column: 1 / -1;
}

.template-diagnostics__item strong {
  min-width: 0;
  color: #f8fafc;
  font-size: 18px;
  line-height: 1.2;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.template-diagnostics__details {
  margin: 0;
  display: grid;
  gap: 10px;
}

.template-diagnostics__details div {
  display: grid;
  gap: 4px;
}

.template-diagnostics__details dd {
  margin: 0;
  color: #f8fafc;
  font-size: 13px;
  line-height: 1.45;
  overflow-wrap: anywhere;
  word-break: break-word;
}

@media (max-width: 520px) {
  .template-diagnostics__header {
    align-items: stretch;
    flex-direction: column;
  }

  .template-diagnostics__status {
    width: fit-content;
  }

  .template-diagnostics__grid {
    grid-template-columns: 1fr;
  }

  .template-diagnostics__item--template {
    grid-column: auto;
  }
}
</style>
