<script setup lang="ts">
import { computed, ref } from 'vue'
import type {
  ControlConsoleReadonlySectionView,
  ControlConsoleReadonlySummaryView,
  ControlConsoleWriteSectionView,
} from '@/features/device-control/viewMapping'
import type { CapacitorBankControlParameterMeta } from '@/features/device-control/capacitorBankControlProfile'

const props = defineProps<{
  sectionView: ControlConsoleReadonlySectionView
  readonlySummaryView: ControlConsoleReadonlySummaryView
  writeSectionView: ControlConsoleWriteSectionView
  canWriteParameters: boolean
  editableParameterCards: Array<CapacitorBankControlParameterMeta & { currentValue: string }>
}>()

const emit = defineEmits<{
  (e: 'open-write-dialog', parameterKey: string): void
}>()

const capacityExpanded = ref(true)

const snapshotTag = computed(() => props.sectionView.tags[0] ?? null)

const editableKeySet = computed(
  () => new Set(props.editableParameterCards.map((item) => String(item.key))),
)

const writeDisabledReason = computed(
  () => props.writeSectionView.alert?.message
    || props.writeSectionView.roleSummaryText
    || '当前不可写入',
)

const phaseCapacityItems = computed(() =>
  props.readonlySummaryView.capacityExpansionItems.filter((item) => item.label.includes('相')),
)

const commonCapacitySlots = computed(() =>
  props.readonlySummaryView.capacityExpansionItems
    .filter((item) => !item.label.includes('相'))
    .flatMap((item) => capacitySlots(item)),
)

function capacitySlotLabel(groupLabel: string, index: number) {
  const range = groupLabel.match(/(\d+)\s*-\s*(\d+)/)
  if (range) return `${Number(range[1]) + index}路`
  const phase = groupLabel.match(/^([ABC])相/)
  if (phase) return `${phase[1]}${index + 1}`
  return `${index + 1}路`
}

function capacitySlots(item: { label: string; value: string }) {
  return item.value
    .split('/')
    .map((value) => value.trim())
    .filter(Boolean)
    .map((value, index) => ({
      key: `${item.label}-${index}`,
      label: capacitySlotLabel(item.label, index),
      value,
    }))
}

function isEditable(parameterKey: string) {
  return editableKeySet.value.has(parameterKey)
}
</script>

<template>
  <div class="params-panel">
    <header
      class="params-header"
      data-test="params-header"
    >
      <div class="params-header__col">
        <span
          v-if="snapshotTag"
          class="params-badge"
          :class="`params-badge--${snapshotTag.tone}`"
        >
          {{ snapshotTag.text }}
        </span>
        <small>{{ readonlySummaryView.sourceMeta }}</small>
      </div>
      <div class="params-header__col params-header__col--right">
        <span
          class="params-badge"
          :class="`params-badge--${writeSectionView.writeStatusTone}`"
        >
          {{ writeSectionView.writeStatusText }}
        </span>
        <small>{{ writeSectionView.roleSummaryText }}</small>
      </div>
    </header>
    <p
      v-if="writeSectionView.alert"
      class="params-alert"
      data-test="params-alert"
    >
      {{ writeSectionView.alert.message }}
    </p>

    <div class="param-section-grid">
      <section
        v-for="group in readonlySummaryView.groupedParameters"
        :key="group.key"
        class="param-section"
        data-test="param-group-card"
      >
        <header class="param-section__head">
          <h4>{{ group.label }}</h4>
          <span>{{ group.items.length }} 个参数</span>
        </header>
        <table class="param-table">
          <thead>
            <tr>
              <th>参数</th>
              <th>当前值</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in group.items"
              :key="item.key"
              data-test="param-row"
            >
              <td :title="item.description">{{ item.label }}</td>
              <td class="param-table__value">{{ item.currentValue }}</td>
              <td>
                <button
                  v-if="isEditable(item.key)"
                  type="button"
                  class="param-edit-button"
                  data-test="param-edit-button"
                  :disabled="!canWriteParameters"
                  :title="canWriteParameters ? '修改参数' : writeDisabledReason"
                  @click="emit('open-write-dialog', item.key)"
                >
                  修改
                </button>
                <span
                  v-else
                  class="param-write-pending"
                  data-test="param-write-pending"
                >
                  写入待开通
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <section
      v-if="sectionView.showCapacityExpansion"
      class="capacity-panel"
    >
      <header class="capacity-panel__head">
        <strong>容量展开详情</strong>
        <button
          type="button"
          class="capacity-toggle"
          data-test="toggle-capacity"
          @click="capacityExpanded = !capacityExpanded"
        >
          {{ capacityExpanded ? '收起' : '展开' }}
        </button>
      </header>
      <div
        v-if="capacityExpanded"
        class="capacity-body"
      >
        <div
          v-if="phaseCapacityItems.length"
          class="capacity-group"
        >
          <span class="capacity-group__title">分相补偿</span>
          <div
            v-for="item in phaseCapacityItems"
            :key="item.label"
            class="capacity-phase-row"
          >
            <span class="capacity-phase-row__label">{{ item.label }}</span>
            <div class="capacity-slot-grid">
              <div
                v-for="slot in capacitySlots(item)"
                :key="slot.key"
                class="capacity-slot"
                data-test="capacity-slot"
              >
                <small>{{ slot.label }}</small>
                <strong>{{ slot.value }}</strong>
              </div>
            </div>
          </div>
        </div>
        <div
          v-if="commonCapacitySlots.length"
          class="capacity-group"
        >
          <span class="capacity-group__title">公共补偿</span>
          <div class="capacity-slot-grid capacity-slot-grid--common">
            <div
              v-for="slot in commonCapacitySlots"
              :key="slot.key"
              class="capacity-slot"
              data-test="capacity-slot"
            >
              <small>{{ slot.label }}</small>
              <strong>{{ slot.value }}</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.params-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.params-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background: rgba(12, 22, 38, 0.7);
}

.params-header__col {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.params-header__col--right {
  justify-content: flex-end;
}

.params-header__col small {
  color: #8da2bf;
  font-size: 11px;
  line-height: 1.5;
}

.params-badge {
  flex: 0 0 auto;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid transparent;
}

.params-badge--success {
  color: #86efac;
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.32);
}

.params-badge--warning {
  color: #fcd34d;
  background: rgba(251, 191, 36, 0.12);
  border-color: rgba(251, 191, 36, 0.32);
}

.params-badge--info {
  color: #93c5fd;
  background: rgba(96, 165, 250, 0.12);
  border-color: rgba(96, 165, 250, 0.32);
}

.params-alert {
  margin: 0;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(251, 191, 36, 0.32);
  background: rgba(251, 191, 36, 0.08);
  color: #fcd34d;
  font-size: 12px;
  line-height: 1.5;
}

.param-section-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  align-items: start;
}

.param-section {
  border: 1px solid rgba(44, 65, 89, 0.7);
  border-radius: 10px;
  background: rgba(12, 22, 38, 0.7);
  overflow: hidden;
}

.param-section__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 9px 14px;
  border-bottom: 1px solid rgba(44, 65, 89, 0.7);
}

.param-section__head h4 {
  margin: 0;
  font-size: 13px;
  color: #c8d8ee;
}

.param-section__head span {
  color: #6a84a2;
  font-size: 11px;
}

.param-table {
  width: 100%;
  border-collapse: collapse;
}

.param-table th {
  text-align: left;
  padding: 7px 10px;
  font-size: 11px;
  font-weight: 500;
  color: #6a84a2;
  background: rgba(8, 17, 30, 0.4);
  border-bottom: 1px solid rgba(33, 52, 74, 0.6);
}

.param-table th:last-child,
.param-table td:last-child {
  text-align: right;
  width: 84px;
}

.param-table td {
  padding: 8px 10px;
  font-size: 12px;
  color: #91a5c2;
  border-bottom: 1px solid rgba(33, 52, 74, 0.6);
}

.param-table tbody tr:last-child td {
  border-bottom: none;
}

.param-table__value {
  color: #f7fbff;
  font-weight: 600;
}

.param-edit-button {
  min-height: 26px;
  padding: 0 12px;
  border-radius: 7px;
  border: 1px solid rgba(245, 158, 11, 0.42);
  background: rgba(120, 53, 15, 0.18);
  color: #fde68a;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.param-edit-button:hover:not(:disabled) {
  background: rgba(120, 53, 15, 0.3);
  border-color: rgba(245, 158, 11, 0.62);
}

.param-edit-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.param-write-pending {
  color: #4b6282;
  font-size: 11px;
}

.capacity-panel {
  border: 1px solid rgba(48, 70, 95, 0.72);
  border-radius: 12px;
  background: rgba(12, 22, 38, 0.64);
  overflow: hidden;
}

.capacity-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
}

.capacity-panel__head strong {
  color: #f7fbff;
  font-size: 13px;
}

.capacity-toggle {
  border: 1px solid rgba(71, 100, 135, 0.5);
  background: transparent;
  color: #93a7c4;
  font: inherit;
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 6px;
  cursor: pointer;
}

.capacity-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 14px 14px;
}

.capacity-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.capacity-group__title {
  color: #6ddbd0;
  font-size: 11px;
  font-weight: 700;
}

.capacity-phase-row {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
}

.capacity-phase-row__label {
  color: #91a5c2;
  font-size: 11px;
}

.capacity-slot-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
}

.capacity-slot-grid--common {
  grid-template-columns: repeat(8, minmax(0, 1fr));
}

.capacity-slot {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid rgba(48, 70, 95, 0.62);
  background: rgba(8, 17, 30, 0.42);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.capacity-slot small {
  color: #6ddbd0;
  font-size: 10px;
}

.capacity-slot strong {
  color: #f7fbff;
  font-size: 12px;
}

@media (max-width: 1280px) {
  .param-section-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1100px) {
  .capacity-slot-grid--common {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .params-header__col--right {
    justify-content: flex-start;
  }

  .param-section-grid {
    grid-template-columns: 1fr;
  }

  .capacity-slot-grid,
  .capacity-slot-grid--common {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .capacity-phase-row {
    grid-template-columns: 1fr;
  }
}
</style>
