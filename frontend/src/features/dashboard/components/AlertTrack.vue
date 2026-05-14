<script setup lang="ts">
import { computed } from 'vue'

export type AlertSeverity = 'crit' | 'warn' | 'info'

export interface AlertItem {
  id: number | string
  sev: AlertSeverity
  title: string
  detail?: string
  time: string
  loc?: string
  ack?: boolean
}

interface Props {
  alerts: AlertItem[]
  pinnedId?: number | string | null
  totalCount?: number
}
const props = defineProps<Props>()

const sevConfig = {
  crit: { color: 'var(--err)', label: '严重' },
  warn: { color: 'var(--warn)', label: '警告' },
  info: { color: 'var(--accent-2)', label: '提示' }
}

const items = computed(() => props.alerts || [])
</script>

<template>
  <div class="card">
    <div class="card-head">
      <div class="title-block">
        <span class="title">告警轨道</span>
        <span v-if="totalCount != null" class="subtitle">近 24 小时 · {{ totalCount }} 条</span>
      </div>
      <button type="button" class="link">查看全部 →</button>
    </div>
    <div v-if="items.length === 0" class="empty">
      <span class="empty-dot" />
      暂无告警 · 系统运行正常
    </div>
    <div v-else class="list">
      <div
        v-for="a in items"
        :key="a.id"
        class="row"
        :class="[
          a.sev === 'crit' && !a.ack && pinnedId !== a.id ? 'a-glow-err loud' : '',
          a.ack ? 'ack' : '',
          pinnedId === a.id ? 'pinned' : ''
        ]"
        :style="{
          '--sc': sevConfig[a.sev].color,
          'border-left-width': (a.sev === 'crit' && !a.ack && pinnedId !== a.id) ? '5px' : '3px'
        }"
      >
        <div class="row-body">
          <div class="row-head">
            <span class="pill" :style="{ color: sevConfig[a.sev].color, background: `color-mix(in srgb, ${sevConfig[a.sev].color} 13%, transparent)` }">
              {{ sevConfig[a.sev].label }}
            </span>
            <span class="ttl">{{ a.title }}</span>
            <span v-if="pinnedId === a.id" class="pinned-chip mono">↑ 顶部展示中</span>
          </div>
          <div v-if="a.detail" class="detail">{{ a.detail }}</div>
          <div class="meta mono">
            <span v-if="a.loc">📍 {{ a.loc }}</span>
            <span>· {{ a.time }}</span>
            <span v-if="a.ack" class="ack-tag">· 已确认</span>
          </div>
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
  min-height: 0;
  min-width: 0;
  flex: 1 1 auto;
  box-sizing: border-box;
}
.card-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 12px; }
.title-block { display: flex; align-items: baseline; gap: 10px; }
.title { font-size: 13px; font-weight: 600; color: var(--text); letter-spacing: 0.2px; }
.subtitle { font-size: 11px; color: var(--text-dim); }
.link { background: none; border: none; color: var(--accent); font-size: 11px; cursor: pointer; font-family: inherit; }
.empty {
  display: flex; align-items: center; gap: 8px;
  padding: 20px 12px; font-size: 12px; color: var(--text-dim);
  border: 1px dashed var(--border); border-radius: 6px;
}
.empty-dot { width: 6px; height: 6px; border-radius: 3px; background: var(--ok); box-shadow: 0 0 6px var(--ok); }
.list { display: flex; flex-direction: column; gap: 8px; overflow: hidden; min-height: 0; }
.row {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--sc) 6%, transparent);
  border: 1px solid color-mix(in srgb, var(--sc) 25%, transparent);
  border-left: 3px solid var(--sc);
}
.row.loud { background: color-mix(in srgb, var(--sc) 10%, transparent); border-color: color-mix(in srgb, var(--sc) 53%, transparent); }
.row.ack { background: transparent; border-color: var(--border); opacity: 0.62; }
.row.pinned { border-color: color-mix(in srgb, var(--sc) 20%, transparent); }
.row-body { flex: 1; min-width: 0; }
.row-head {
  display: flex; align-items: center; gap: 8px; margin-bottom: 3px; flex-wrap: wrap;
}
.pill {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.4px;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--mono);
}
.ttl { font-size: 12px; color: var(--text); font-weight: 500; }
.pinned-chip {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.4px;
  padding: 2px 6px;
  border-radius: 3px;
  color: var(--text-mid);
  background: var(--surface-hi);
  border: 1px solid var(--border-hi);
}
.detail { font-size: 11px; color: var(--text-mid); margin-bottom: 4px; }
.meta { display: flex; gap: 10px; font-size: 10px; color: var(--text-dim); }
.ack-tag { color: var(--ok); }
</style>
