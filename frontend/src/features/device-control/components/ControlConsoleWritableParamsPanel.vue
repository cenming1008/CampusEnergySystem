<script setup lang="ts">
import type { ControlConsoleWriteSectionView } from '@/features/device-control/viewMapping'
import type { CapacitorBankControlParameterMeta } from '@/features/device-control/capacitorBankControlProfile'

defineProps<{
  writeSectionView: ControlConsoleWriteSectionView
  canWriteParameters: boolean
  editableParameterCards: Array<CapacitorBankControlParameterMeta & { currentValue: string }>
}>()

const emit = defineEmits<{
  (e: 'openWriteDialog', parameterKey: string): void
}>()
</script>

<template>
  <div
    class="writable-params-panel"
    :class="{ 'writable-params-panel--locked': !canWriteParameters }"
  >
    <div
      class="write-status-strip"
      :class="canWriteParameters ? 'write-status-strip--enabled' : 'write-status-strip--locked'"
    >
      <span>{{ writeSectionView.writeStatusText }}</span>
      <small>
        {{ writeSectionView.alert ? writeSectionView.alert.message : writeSectionView.roleSummaryText }}
      </small>
    </div>

    <div class="editable-list">
      <button
        v-for="item in editableParameterCards"
        :key="item.key"
        class="editable-row"
        type="button"
        :disabled="!canWriteParameters"
        :title="item.description"
        @click="emit('openWriteDialog', String(item.key))"
      >
        <span class="editable-row__label">{{ item.label }}</span>
        <strong>{{ item.currentValue }}</strong>
        <em>{{ canWriteParameters ? '修改参数' : '当前不可写入' }}</em>
      </button>
    </div>
  </div>
</template>

<style scoped>
.writable-params-panel {
  display: flex;
  flex-direction: column;
}

.writable-params-panel--locked {
  opacity: 0.78;
}

.write-status-strip {
  min-height: 44px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(71, 100, 135, 0.4);
  background: rgba(12, 22, 38, 0.62);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.write-status-strip span {
  flex: 0 0 auto;
  font-size: 13px;
  font-weight: 700;
}

.write-status-strip small {
  color: #91a5c2;
  font-size: 12px;
  line-height: 1.5;
  text-align: right;
}

.write-status-strip--enabled span {
  color: #86efac;
}

.write-status-strip--locked span {
  color: #fcd34d;
}

.editable-list {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 10px;
}

.editable-row {
  min-height: 54px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background:
    linear-gradient(180deg, rgba(45, 212, 191, 0.04), rgba(12, 24, 39, 0.78)),
    rgba(19, 34, 53, 0.75);
  color: #dbe5f4;
  text-align: left;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 10px;
  align-items: center;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.editable-row:not(:disabled):hover {
  border-color: rgba(251, 191, 36, 0.5);
  box-shadow: 0 2px 12px rgba(251, 191, 36, 0.07);
}

.editable-row:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.editable-row__label {
  color: #91a5c2;
  font-size: 12px;
  letter-spacing: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.editable-row strong {
  color: #f8fbff;
  font-size: 14px;
  white-space: nowrap;
}

.editable-row em {
  font-style: normal;
  color: #fbbf24;
  font-size: 11px;
  white-space: nowrap;
}

.editable-row:disabled em {
  color: #4b6282;
}

@media (max-width: 1400px) {
  .editable-list {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
}

@media (max-width: 800px) {
  .write-status-strip {
    flex-direction: column;
    align-items: flex-start;
  }

  .write-status-strip small {
    text-align: left;
  }

  .editable-list {
    grid-template-columns: 1fr;
  }

  .editable-row {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
