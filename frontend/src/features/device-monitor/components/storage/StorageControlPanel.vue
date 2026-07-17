<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  dataSourceLabel: string
  controlMode: string
  actualPower: number | null
  targetPower: number | null
  availableChargePower: number | null
  availableDischargePower: number | null
  bmsStatus: string
  pcsStatus: string
  gridStatus: string
  commandSource: string
  currentPlanLabel: string
  autoAuthorized: boolean
  canControl: boolean
  canManageAuto: boolean
  pending: boolean
  submitting: boolean
}>()

const emit = defineEmits<{
  'set-power': [value: number]
  'set-mode': [value: 'auto' | 'manual']
  stop: []
  'update-auto': [value: boolean]
}>()

const powerInput = ref<number>(props.targetPower ?? 0)

watch(() => props.targetPower, (value) => {
  if (value != null) powerInput.value = value
})

const controlsDisabled = computed(() => !props.canControl || props.pending || props.submitting)
const autoGateDisabled = computed(() => !props.canManageAuto || props.pending || props.submitting)

function formatPower(value: number | null) {
  return value == null ? '--' : `${Number(value).toFixed(1)} kW`
}

function statusClass(value: string) {
  return ['normal', 'running', 'connected', 'standby'].includes(value.toLowerCase())
    ? 'is-healthy'
    : value === '--'
      ? ''
      : 'is-warning'
}

function submitPower() {
  if (controlsDisabled.value || !Number.isFinite(powerInput.value)) return
  emit('set-power', Number(powerInput.value))
}
</script>

<template>
  <section class="storage-control-panel">
    <div class="storage-control-panel__head">
      <div>
        <h3>储能监控与控制</h3>
        <p>正功率充电，负功率放电；命令成功以设备回执为准。</p>
      </div>
      <span
        class="source-badge"
        :class="dataSourceLabel === '仿真数据' ? 'is-simulated' : 'is-real'"
      >
        {{ dataSourceLabel }}
      </span>
    </div>

    <div class="storage-control-panel__metrics">
      <div><span>实际功率</span><strong>{{ formatPower(actualPower) }}</strong></div>
      <div><span>目标功率</span><strong>{{ formatPower(targetPower) }}</strong></div>
      <div><span>可充功率</span><strong>{{ formatPower(availableChargePower) }}</strong></div>
      <div><span>可放功率</span><strong>{{ formatPower(availableDischargePower) }}</strong></div>
      <div><span>BMS</span><strong :class="statusClass(bmsStatus)">{{ bmsStatus }}</strong></div>
      <div><span>PCS</span><strong :class="statusClass(pcsStatus)">{{ pcsStatus }}</strong></div>
      <div><span>并网</span><strong :class="statusClass(gridStatus)">{{ gridStatus }}</strong></div>
      <div><span>命令来源</span><strong>{{ commandSource }}</strong></div>
      <div><span>当前计划</span><strong>{{ currentPlanLabel }}</strong></div>
    </div>

    <div class="storage-control-panel__actions">
      <label class="power-field">
        <span>目标有功功率（kW）</span>
        <input
          v-model.number="powerInput"
          data-test="storage-power-input"
          type="number"
          step="1"
          :disabled="controlsDisabled"
          @keyup.enter="submitPower"
        >
      </label>
      <button
        data-test="storage-set-power"
        type="button"
        :disabled="controlsDisabled"
        @click="submitPower"
      >
        下发功率
      </button>
      <button
        data-test="storage-stop"
        type="button"
        class="is-danger"
        :disabled="controlsDisabled"
        @click="emit('stop')"
      >
        停止充放电
      </button>
      <button
        data-test="storage-mode-manual"
        type="button"
        :class="{ 'is-active': controlMode === 'manual' }"
        :disabled="controlsDisabled"
        @click="emit('set-mode', 'manual')"
      >
        手动模式
      </button>
      <button
        data-test="storage-mode-auto"
        type="button"
        :class="{ 'is-active': controlMode === 'auto' }"
        :disabled="controlsDisabled"
        @click="emit('set-mode', 'auto')"
      >
        自动模式
      </button>
      <label class="auto-gate">
        <input
          data-test="storage-auto-gate"
          type="checkbox"
          :checked="autoAuthorized"
          :disabled="autoGateDisabled"
          @change="emit('update-auto', ($event.target as HTMLInputElement).checked)"
        >
        <span>允许 EMS 自动控制</span>
        <small>{{ canManageAuto ? '管理员授权' : '仅管理员可修改' }}</small>
      </label>
    </div>

    <p
      v-if="pending"
      class="pending-hint"
    >
      当前存在执行中的命令，冲突控制已暂时锁定。
    </p>
    <p
      v-else-if="!canControl"
      class="pending-hint"
    >
      当前账号仅可查看储能状态，不能下发控制命令。
    </p>
  </section>
</template>

<style scoped>
.storage-control-panel {
  padding: 18px;
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
}

.storage-control-panel__head,
.storage-control-panel__actions,
.auto-gate {
  display: flex;
  align-items: center;
}

.storage-control-panel__head { justify-content: space-between; gap: 20px; }
.storage-control-panel__head h3 { margin: 0; color: #f5f7fb; font-size: 16px; }
.storage-control-panel__head p { margin: 6px 0 0; color: #8ea0bc; font-size: 12px; }

.source-badge {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}
.source-badge.is-simulated { color: #fde68a; background: rgba(245, 158, 11, 0.14); border: 1px solid rgba(245, 158, 11, 0.35); }
.source-badge.is-real { color: #bbf7d0; background: rgba(34, 197, 94, 0.14); border: 1px solid rgba(34, 197, 94, 0.35); }

.storage-control-panel__metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(110px, 1fr));
  gap: 10px;
  margin-top: 16px;
}
.storage-control-panel__metrics > div { padding: 10px; border-radius: 10px; background: rgba(7, 15, 26, 0.55); }
.storage-control-panel__metrics span { display: block; color: #7f93b2; font-size: 11px; }
.storage-control-panel__metrics strong { display: block; margin-top: 5px; color: #e5edf7; font-size: 13px; }
.storage-control-panel__metrics strong.is-healthy { color: #4ade80; }
.storage-control-panel__metrics strong.is-warning { color: #fb7185; }

.storage-control-panel__actions { flex-wrap: wrap; gap: 8px; margin-top: 16px; }
.power-field { display: flex; align-items: center; gap: 8px; color: #aebbd0; font-size: 12px; }
.power-field input { width: 120px; padding: 8px 10px; border: 1px solid #314055; border-radius: 8px; color: #f5f7fb; background: #0b1320; }
.storage-control-panel__actions button { padding: 8px 12px; border: 1px solid #3b82f6; border-radius: 8px; color: #bfdbfe; background: rgba(59, 130, 246, 0.12); cursor: pointer; }
.storage-control-panel__actions button.is-active { color: #bbf7d0; border-color: #22c55e; background: rgba(34, 197, 94, 0.14); }
.storage-control-panel__actions button.is-danger { color: #fecdd3; border-color: #e11d48; background: rgba(225, 29, 72, 0.12); }
.storage-control-panel__actions button:disabled,
.power-field input:disabled { opacity: 0.45; cursor: not-allowed; }
.auto-gate { gap: 7px; margin-left: auto; color: #cbd5e1; font-size: 12px; }
.auto-gate small { color: #64748b; }
.pending-hint { margin: 12px 0 0; color: #fbbf24; font-size: 12px; }

@media (max-width: 1100px) {
  .storage-control-panel__metrics { grid-template-columns: repeat(3, minmax(110px, 1fr)); }
  .auto-gate { margin-left: 0; width: 100%; }
}
</style>
