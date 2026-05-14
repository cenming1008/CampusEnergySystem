<script setup lang="ts">
export type MatrixStatus = 'on' | 'notice' | 'warn' | 'off'

export interface MatrixItem {
  n: string
  s: MatrixStatus
  v: string
  u: string
  reason?: string | null
}

export interface MatrixGroup {
  name: string
  color: string
  items: MatrixItem[]
}

interface Props {
  groups: MatrixGroup[]
  legend?: { ok: number; notice: number; warn: number; off: number }
}
defineProps<Props>()

function severityColor(s: MatrixStatus) {
  if (s === 'off') return 'var(--text-dim)'
  if (s === 'warn') return 'var(--warn)'
  if (s === 'notice') return 'var(--notice)'
  return 'var(--ok)'
}
function sevLabel(s: MatrixStatus) {
  if (s === 'off') return 'OFF'
  if (s === 'warn') return 'WARN'
  if (s === 'notice') return 'NOTICE'
  return ''
}
</script>

<template>
  <div class="card">
    <div class="card-head">
      <div class="title-block">
        <span class="title">设备状态矩阵</span>
        <span class="subtitle">按介质</span>
      </div>
      <div v-if="legend" class="legend">
        <span class="lg"><span class="ld" style="background: var(--ok)" />{{ legend.ok }} 在线</span>
        <span class="lg"><span class="ld" style="background: var(--notice)" />{{ legend.notice }} 注意</span>
        <span class="lg"><span class="ld" style="background: var(--warn)" />{{ legend.warn }} 警告</span>
        <span class="lg"><span class="ld" style="background: var(--text-dim); opacity: 0.7" />{{ legend.off }} 停机</span>
      </div>
    </div>
    <div class="grid">
      <div v-for="g in groups" :key="g.name" class="group">
        <div class="group-head">
          <span class="g-dot" :style="{ background: g.color }" />
          <span class="g-name">{{ g.name }}</span>
          <span class="g-count mono">{{ g.items.length }}</span>
        </div>
        <div
          v-for="(it, i) in g.items"
          :key="`${g.name}-${i}`"
          class="item"
          :class="[
            it.s === 'off' ? 'a-stripe off' : '',
            it.s === 'warn' ? 'warn' : '',
            it.s === 'notice' ? 'notice' : ''
          ]"
          :title="it.reason || `${it.n} · ${it.v} ${it.u}`"
        >
          <span class="dot" :style="{
            background: severityColor(it.s),
            boxShadow: it.s === 'warn'
              ? '0 0 6px var(--warn)'
              : (it.s === 'notice' ? '0 0 4px var(--notice)' : 'none')
          }" />
          <span class="n">{{ it.n }}</span>
          <span class="v mono" :style="{
            color: it.s === 'off'
              ? 'var(--text-dim)'
              : (it.s === 'warn' ? 'var(--warn)' : (it.s === 'notice' ? 'var(--notice)' : 'var(--text)'))
          }">{{ it.v }}</span>
          <span class="u mono">{{ it.u }}</span>
          <span v-if="sevLabel(it.s)" class="badge mono" :style="{ color: severityColor(it.s), borderColor: `color-mix(in srgb, ${severityColor(it.s)} 35%, transparent)` }">
            {{ sevLabel(it.s) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  flex: 1;
  box-sizing: border-box;
}
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.title-block { display: flex; align-items: baseline; gap: 10px; }
.title { font-size: 13px; font-weight: 600; color: var(--text); letter-spacing: 0.2px; }
.subtitle { font-size: 11px; color: var(--text-dim); }
.legend { display: flex; gap: 10px; font-size: 11px; color: var(--text-dim); align-items: center; }
.lg { display: flex; align-items: center; gap: 4px; }
.ld { width: 6px; height: 6px; border-radius: 3px; }
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  min-height: 0;
}
.group { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.group-head { display: flex; align-items: center; gap: 6px; margin-bottom: 2px; }
.g-dot { width: 8px; height: 8px; border-radius: 2px; }
.g-name { font-size: 11px; color: var(--text-mid); letter-spacing: 0.3px; }
.g-count { font-size: 10px; color: var(--text-dim); margin-left: auto; }
.item {
  display: grid;
  grid-template-columns: 8px 1fr auto auto;
  align-items: center;
  column-gap: 7px;
  padding: 6px 8px;
  border-radius: 4px;
  background: var(--surface-hi);
  border: 1px solid transparent;
  position: relative;
  cursor: help;
}
.item.warn { border-color: color-mix(in srgb, var(--warn) 40%, transparent); }
.item.notice { border-color: color-mix(in srgb, var(--notice) 27%, transparent); }
.item.off { background: transparent; border: 1px dashed var(--border-hi); }
.item .dot { width: 6px; height: 6px; border-radius: 3px; }
.item .n {
  font-size: 11px; color: var(--text);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.item.off .n { color: var(--text-dim); font-style: italic; }
.item .v { font-size: 11px; font-weight: 600; text-align: right; }
.item .u { font-size: 9px; color: var(--text-dim); min-width: 36px; text-align: left; }
.item .badge {
  position: absolute;
  right: 6px;
  top: -6px;
  font-size: 8px;
  padding: 1px 5px;
  border-radius: 3px;
  letter-spacing: 0.5px;
  background: var(--bg);
  border: 1px solid currentColor;
  font-weight: 700;
}
</style>
