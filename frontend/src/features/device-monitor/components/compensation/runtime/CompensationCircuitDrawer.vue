<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCircuitPick } from '../types'
import type { CompensationEventItem } from '../types'

const props = defineProps({
  circuit: {
    type: Object as PropType<CompensationCircuitPick>,
    required: true,
  },
  canControl: { type: Boolean, default: false },
  events: {
    type: Array as PropType<CompensationEventItem[]>,
    default: () => [],
  },
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'switch', payload: { phase: 'A' | 'B' | 'C' | 'COMMON'; commonGroup: 1 | 2 | 3 | null; action: 'on' | 'off' }): void
}>()

const stateText = computed(() => {
  if (props.circuit.state === 'on') return '投入运行'
  if (props.circuit.state === 'off') return '已切除'
  return '未配置'
})

const stateClass = computed(() => `state-${props.circuit.state}`)

const switchScopeHint = computed(() =>
  props.circuit.phase === 'COMMON'
    ? '投切指令作用于整个公补组'
    : '投切指令作用于整相回路',
)

function doSwitch(action: 'on' | 'off') {
  if (!props.canControl) return
  emit('switch', {
    phase: props.circuit.phase,
    commonGroup: props.circuit.commonGroup,
    action,
  })
}
</script>

<template>
  <div class="drawer-mask" data-test="drawer-mask" @click="emit('close')">
    <aside class="drawer" @click.stop>
      <header class="drawer-head">
        <div>
          <div class="drawer-title">{{ circuit.groupLabel }} · 第 {{ circuit.index }} 路</div>
          <div class="drawer-sub">
            状态：<span :class="stateClass">{{ stateText }}</span>
          </div>
        </div>
        <button type="button" class="drawer-close" @click="emit('close')">✕</button>
      </header>

      <section class="drawer-section">
        <h3>当前参数</h3>
        <div class="drawer-grid">
          <div><span class="k">所属相</span><span class="v">{{ circuit.phase === 'COMMON' ? '公补' : `${circuit.phase} 相` }}</span></div>
          <div><span class="k">回路序号</span><span class="v">第 {{ circuit.index }} 路</span></div>
          <div><span class="k">投切状态</span><span class="v" :class="stateClass">{{ stateText }}</span></div>
          <div><span class="k">相级告警</span><span class="v">{{ circuit.phaseAlarm ? '存在' : '无' }}</span></div>
        </div>
      </section>

      <section class="drawer-section">
        <h3>投切动作历史</h3>
        <div v-if="events.length === 0" class="drawer-empty">暂无该回路的投切记录</div>
        <ul v-else class="drawer-events">
          <li v-for="(ev, i) in events" :key="i">
            <span class="ev-time">{{ ev.time }}</span>
            <span class="ev-title">{{ ev.title }}</span>
          </li>
        </ul>
      </section>

      <section class="drawer-section">
        <h3>操作</h3>
        <p class="drawer-scope-hint">{{ switchScopeHint }}</p>
        <div class="drawer-actions">
          <button
            type="button"
            class="drawer-btn primary"
            data-test="circuit-action"
            :disabled="!canControl"
            @click="doSwitch('on')"
          >立即投入</button>
          <button
            type="button"
            class="drawer-btn"
            data-test="circuit-action-off"
            :disabled="!canControl"
            @click="doSwitch('off')"
          >立即切除</button>
        </div>
        <p v-if="!canControl" class="drawer-deny">当前无远程控制权限或设备不可投切</p>
      </section>
    </aside>
  </div>
</template>

<style scoped>
.drawer-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 2000;
  display: flex;
  justify-content: flex-end;
}
.drawer {
  width: 380px;
  max-width: 92vw;
  height: 100%;
  background: #0b1623;
  border-left: 1px solid #1f2c41;
  overflow-y: auto;
}
.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid #1f2c41;
}
.drawer-title {
  font-size: 15px;
  font-weight: 600;
  color: #e5edf7;
}
.drawer-sub {
  font-size: 11px;
  color: #5e6c83;
  margin-top: 2px;
}
.drawer-close {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  background: #121d2e;
  border: 1px solid #1f2c41;
  color: #9aa7bd;
  cursor: pointer;
}
.drawer-section {
  padding: 16px 18px;
  border-bottom: 1px solid #1f2c41;
}
.drawer-section h3 {
  margin: 0 0 10px;
  font-size: 12px;
  color: #9aa7bd;
  font-weight: 600;
}
.drawer-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 14px;
}
.drawer-grid .k {
  display: block;
  font-size: 11px;
  color: #5e6c83;
}
.drawer-grid .v {
  font-size: 13px;
  color: #e5edf7;
}
.state-on { color: #34d399; }
.state-off { color: #9aa7bd; }
.state-unconfigured { color: #5e6c83; }
.drawer-empty {
  font-size: 12px;
  color: #5e6c83;
}
.drawer-events {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.drawer-events li {
  display: flex;
  gap: 10px;
  font-size: 12px;
}
.ev-time {
  color: #5e6c83;
  font-variant-numeric: tabular-nums;
}
.ev-title {
  color: #e5edf7;
}
.drawer-scope-hint {
  margin: 0 0 8px;
  font-size: 11px;
  color: #f59e0b;
}
.drawer-actions {
  display: flex;
  gap: 10px;
}
.drawer-btn {
  flex: 1;
  height: 34px;
  border-radius: 7px;
  background: #182538;
  border: 1px solid #2a3a55;
  color: #e5edf7;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}
.drawer-btn.primary {
  background: linear-gradient(180deg, #0891b2, #155e75);
  border-color: #0891b2;
  color: #ecfeff;
}
.drawer-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.drawer-deny {
  margin: 8px 0 0;
  font-size: 11px;
  color: #5e6c83;
}
</style>
