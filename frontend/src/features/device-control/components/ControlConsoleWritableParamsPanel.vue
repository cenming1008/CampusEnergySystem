<script setup lang="ts">
import type { ControlConsoleWriteSectionView } from '@/features/device-control/viewMapping'
import type { CapacitorBankControlParameterMeta } from '@/features/device-control/capacitorBankControlProfile'
import ControlConsoleParameterSection from '@/features/device-control/components/ControlConsoleParameterSection.vue'
import MonitorInlineAlert from '@/shared/components/MonitorInlineAlert.vue'

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
  <ControlConsoleParameterSection
    :title="writeSectionView.title"
    :section-label="writeSectionView.sectionLabel"
    :tone="writeSectionView.tone"
    :description="`${writeSectionView.description} 当前账号参数权限：${writeSectionView.roleSummaryText}`"
    :tags="writeSectionView.tags"
    :locked="!canWriteParameters"
  >
    <template #alert>
      <MonitorInlineAlert
        v-if="writeSectionView.alert"
        :title="writeSectionView.alert.title"
        :message="writeSectionView.alert.message"
        :tone="writeSectionView.alert.tone"
        subtle
        class="write-alert"
      />
    </template>
    <div class="editable-grid">
      <button
        v-for="item in editableParameterCards"
        :key="item.key"
        class="editable-card"
        type="button"
        :disabled="!canWriteParameters"
        @click="emit('openWriteDialog', String(item.key))"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.currentValue }}</strong>
        <small>{{ item.description }}</small>
        <em>{{ canWriteParameters ? '修改参数' : '当前不可写入' }}</em>
      </button>
    </div>
  </ControlConsoleParameterSection>
</template>

<style scoped>
.write-alert {
  margin-bottom: 14px;
}

.editable-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.editable-card {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background: rgba(19, 34, 53, 0.75);
  color: #dbe5f4;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 7px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.editable-card:not(:disabled):hover {
  border-color: rgba(251, 191, 36, 0.5);
  box-shadow: 0 2px 12px rgba(251, 191, 36, 0.07);
}

.editable-card:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.editable-card span {
  color: #91a5c2;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.editable-card strong {
  color: #f8fbff;
  font-size: 16px;
}

.editable-card small {
  color: #7a90ab;
  font-size: 11px;
  line-height: 1.5;
}

.editable-card em {
  margin-top: auto;
  font-style: normal;
  color: #fbbf24;
  font-size: 11px;
}

.editable-card:disabled em {
  color: #4b6282;
}

@media (max-width: 1400px) {
  .editable-grid {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
}

@media (max-width: 800px) {
  .editable-grid {
    grid-template-columns: 1fr;
  }
}
</style>
