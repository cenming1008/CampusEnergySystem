<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  park?: string
  operator?: string
  shift?: string
  samplingOnline?: number
  samplingTotal?: number
  mode?: string
  time?: string
  date?: string
}
const props = withDefaults(defineProps<Props>(), {
  park: '滨海科技园 · 一期',
  operator: '张工',
  shift: '白班 14:00-22:00',
  samplingOnline: 0,
  samplingTotal: 0,
  mode: '自动调度中',
  time: '',
  date: ''
})

const minuteTime = computed(() => (props.time || '').slice(0, 5))
const operatorInitial = computed(() => (props.operator || ' ').charAt(0))
const samplingHealthy = computed(() => props.samplingOnline >= props.samplingTotal && props.samplingTotal > 0)
</script>

<template>
  <div class="status-bar">
    <div class="left">
      <span class="brand-mark">P</span>
      <span class="brand-name">园区综合能源管理系统</span>
      <span class="brand-version mono">PARK · EMS · v4.2</span>
      <span class="vline" />
      <span class="park">{{ park }}<span class="caret">▾</span></span>
    </div>
    <div class="right">
      <div class="mode">
        <span class="mode-dot a-pulse" />
        <span>{{ mode }}</span>
      </div>
      <div class="operator">
        <div class="op-avatar">{{ operatorInitial }}</div>
        <div class="op-info">
          <span class="op-name">值班 · {{ operator }}</span>
          <span class="op-shift mono">{{ shift }}</span>
        </div>
      </div>
      <span class="vline tall" />
      <div class="sampling">
        <span class="dot" :class="{ ok: samplingHealthy, warn: !samplingHealthy }" />
        <span>采集 {{ samplingOnline }}/{{ samplingTotal }}</span>
      </div>
      <span class="vline tall" />
      <div class="clock">
        <span class="clock-time mono">{{ minuteTime || '--:--' }}</span>
        <span class="clock-date mono">{{ date }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.status-bar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-sizing: border-box;
}
.left, .right {
  display: flex;
  align-items: center;
}
.left { gap: 14px; }
.right { gap: 18px; }
.brand-mark {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  display: flex; align-items: center; justify-content: center;
  font-size: 11px;
  font-weight: 800;
  color: #0a0f17;
}
.brand-name { font-size: 14px; font-weight: 600; color: var(--text); }
.brand-version {
  font-size: 11px;
  color: var(--text-dim);
  letter-spacing: 0.5px;
}
.vline { width: 1px; height: 16px; background: var(--border-hi); margin-inline: 4px; }
.vline.tall { height: 22px; }
.park {
  font-size: 12px;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 6px;
}
.caret { color: var(--text-dim); font-size: 10px; }
.mode {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 10px;
  border-radius: 4px;
  background: rgba(77, 208, 196, 0.08);
  border: 1px solid rgba(77, 208, 196, 0.25);
  color: var(--accent);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.4px;
}
.mode-dot {
  width: 6px; height: 6px; border-radius: 3px; background: var(--accent);
}
.operator { display: flex; align-items: center; gap: 8px; }
.op-avatar {
  width: 22px; height: 22px; border-radius: 11px;
  background: var(--surface-hi);
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 600; color: var(--accent);
}
.op-info { display: flex; flex-direction: column; line-height: 1.1; }
.op-name { font-size: 11px; color: var(--text); }
.op-shift { font-size: 9px; color: var(--text-dim); }
.sampling {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: var(--text-mid);
}
.sampling .dot {
  width: 6px; height: 6px; border-radius: 3px;
}
.sampling .dot.ok { background: var(--ok); box-shadow: 0 0 6px var(--ok); }
.sampling .dot.warn { background: var(--warn); box-shadow: 0 0 6px var(--warn); }
.clock {
  display: flex; flex-direction: column; align-items: flex-end; line-height: 1.1;
}
.clock-time { font-size: 14px; color: var(--text); font-weight: 600; }
.clock-date { font-size: 10px; color: var(--text-dim); }
</style>
