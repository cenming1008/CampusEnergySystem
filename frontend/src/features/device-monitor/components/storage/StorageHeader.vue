<script setup lang="ts">
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
import type { StorageRunState, StorageTone } from './types'

const props = defineProps<{
  title: string
  serial: string
  location: string
  runtimeLabel: string
  runtimeCode: string
  runState: StorageRunState
  isOnline: boolean
}>()

const emit = defineEmits<{
  back: []
  refresh: []
}>()

function runStateChipClass(state: StorageRunState): string {
  if (state === 'charging') return 'comp-header__chip--mode'
  if (state === 'discharging') return 'comp-header__chip--success'
  if (state === 'fault') return 'comp-header__chip--danger'
  if (state === 'standby' || state === 'idle') return 'comp-header__chip--neutral'
  return 'comp-header__chip--neutral'
}

function runtimeChipClass(code: string): string {
  if (code === 'running') return 'comp-header__chip--success'
  if (code === 'alarm' || code === 'offline') return 'comp-header__chip--danger'
  if (code === 'degraded') return 'comp-header__chip--warning'
  return 'comp-header__chip--neutral'
}

const RUN_STATE_LABELS: Record<StorageRunState, string> = {
  charging: '充电中',
  discharging: '放电中',
  idle: '空闲',
  standby: '待机',
  fault: '故障',
  unknown: '状态未知',
}
</script>

<template>
  <div class="comp-header">
    <div class="comp-header__identity">
      <button
        type="button"
        class="comp-header__back"
        @click="emit('back')"
      >
        <el-icon><ArrowLeft /></el-icon>
        <span>返回设备台账</span>
      </button>

      <div class="comp-header__main">
        <div class="comp-header__mark">
          {{ serial.slice(0, 3).toUpperCase() }}
        </div>
        <div class="comp-header__title">
          <h2>{{ title }}</h2>
          <p>
            <span>设备编号：{{ serial }}</span>
            <i />
            <span>安装位置：{{ location }}</span>
          </p>
        </div>
      </div>
    </div>

    <div class="comp-header__status">
      <div class="comp-header__tags">
        <span
          class="comp-header__chip"
          :class="runtimeChipClass(runtimeCode)"
        >
          <i />
          {{ runtimeLabel }}
        </span>
        <span
          class="comp-header__chip"
          :class="runStateChipClass(runState)"
        >
          {{ RUN_STATE_LABELS[runState] }}
        </span>
      </div>

      <div class="comp-header__actions">
        <button
          type="button"
          class="comp-header__action comp-header__action--neutral"
          @click="emit('refresh')"
        >
          <el-icon :size="14"><Refresh /></el-icon>
          <span>刷新</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comp-header {
  display: grid;
  grid-template-columns: minmax(360px, 1fr) minmax(320px, auto);
  gap: 28px;
  align-items: center;
  padding: 20px 22px;
  background:
    linear-gradient(135deg, rgba(13, 24, 38, 0.98), rgba(15, 29, 47, 0.96)),
    linear-gradient(90deg, rgba(59, 130, 246, 0.06), rgba(34, 197, 94, 0.04));
  border: 1px solid rgba(58, 76, 102, 0.88);
  border-radius: 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.comp-header__identity,
.comp-header__status {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.comp-header__status {
  align-items: flex-end;
}

.comp-header__back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: fit-content;
  padding: 0;
  border: 0;
  background: transparent;
  color: #7f93b2;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.comp-header__back:hover { color: #dbeafe; }

.comp-header__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.comp-header__mark {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(74, 222, 128, 0.24);
  color: #bbf7d0;
  font-size: 12px;
  font-weight: 700;
  flex: 0 0 auto;
}

.comp-header__title h2 {
  margin: 0;
  font-size: 24px;
  color: #f5f7fb;
  line-height: 1.15;
}

.comp-header__title p {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin: 8px 0 0;
  font-size: 12px;
  color: #8ea0bc;
}

.comp-header__title i {
  width: 1px;
  height: 10px;
  background: rgba(142, 160, 188, 0.42);
}

.comp-header__tags,
.comp-header__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.comp-header__chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 7px;
  border: 1px solid rgba(72, 96, 130, 0.68);
  background: rgba(7, 15, 26, 0.58);
  color: #cbd5e1;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
}

.comp-header__chip i {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: currentColor;
  flex: 0 0 auto;
}

.comp-header__chip--success { color: #86efac; border-color: rgba(34, 197, 94, 0.35); }
.comp-header__chip--warning { color: #fde68a; border-color: rgba(245, 158, 11, 0.38); }
.comp-header__chip--danger  { color: #fca5a5; border-color: rgba(248, 113, 113, 0.35); }
.comp-header__chip--mode    { color: #bfdbfe; border-color: rgba(96, 165, 250, 0.32); }
.comp-header__chip--neutral { color: #cbd5e1; border-color: rgba(72, 96, 130, 0.68); }

.comp-header__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 80px;
  height: 34px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid rgba(72, 96, 130, 0.76);
  background: rgba(7, 15, 26, 0.68);
  color: #dbeafe;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.16s ease, background 0.16s ease;
}

.comp-header__action:hover {
  background: rgba(15, 29, 47, 0.95);
  border-color: rgba(96, 165, 250, 0.45);
}

.comp-header__action--neutral { color: #dbeafe; }

@media (max-width: 1320px) {
  .comp-header {
    grid-template-columns: 1fr;
  }

  .comp-header__status {
    width: 100%;
    align-items: flex-start;
  }

  .comp-header__tags,
  .comp-header__actions {
    justify-content: flex-start;
  }
}
</style>
