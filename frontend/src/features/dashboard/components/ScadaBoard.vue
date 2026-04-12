<script setup lang="ts">
import { ElScrollbar } from 'element-plus'
import { getDeviceTypeLabel } from '@/shared/deviceTypeLabels'

interface DeviceItem {
  id?: number
  name?: string
  location?: string
  is_active?: boolean
  energy_type?: string
  device_type?: string
}

interface DeviceGroup {
  key: string
  label: string
  devices: DeviceItem[]
  online: number
}

const props = defineProps<{
  groups: DeviceGroup[]
  currentDeviceId: number | undefined
  onlineCount: number
  totalCount: number
}>()

const emit = defineEmits<{
  'select-device': [id: number]
}>()

function onSelect(id: number | undefined) {
  if (id != null) emit('select-device', id)
}
</script>

<template>
  <section class="glass-card scada-board">
    <div class="scada-board__head">
      <div>
        <span class="card-eyebrow">SCADA Device Board</span>
        <span class="card-title">SCADA 设备导航</span>
      </div>
      <span class="scada-board__summary">{{ onlineCount }}/{{ totalCount }} 在线</span>
    </div>

    <ElScrollbar class="scada-scroll" always>
      <details
        v-for="group in groups"
        :key="group.key"
        class="scada-group"
        :open="group.devices.some((d) => d.id === currentDeviceId)"
      >
        <summary class="scada-group__summary">
          <div class="scada-group__info">
            <span class="scada-group__label">{{ group.label }}</span>
            <small class="scada-group__count">{{ group.devices.length }} 台</small>
          </div>
          <div class="scada-group__right">
            <span
              class="scada-group__badge"
              :class="group.online < group.devices.length ? 'scada-group__badge--warn' : 'scada-group__badge--ok'"
            >
              {{ group.online }}/{{ group.devices.length }}
            </span>
            <span class="scada-group__caret" />
          </div>
        </summary>

        <div class="scada-group__body">
          <button
            v-for="device in group.devices"
            :key="device.id"
            type="button"
            class="scada-item"
            :class="{ 'scada-item--active': device.id === currentDeviceId, 'scada-item--offline': !device.is_active }"
            @click="onSelect(device.id)"
          >
            <span class="scada-item__dot" :class="device.is_active ? 'scada-item__dot--on' : 'scada-item__dot--off'" />
            <span class="scada-item__name">{{ device.name }}</span>
            <span class="scada-item__tag">{{ getDeviceTypeLabel(device.device_type) }}</span>
          </button>
        </div>
      </details>
    </ElScrollbar>
  </section>
</template>

<style scoped>
.scada-board {
  padding: 14px;
  height: 100%;
  max-height: clamp(360px, calc(100vh - 290px), 620px);
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow: hidden;
}

.scada-board__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.scada-board__head > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.card-eyebrow {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: rgba(255, 255, 255, 0.38);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.scada-board__summary {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  flex-shrink: 0;
  margin-top: 16px;
}

.scada-scroll {
  flex: 1 1 0;
  min-height: 0;
}

.scada-scroll :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

.scada-scroll :deep(.el-scrollbar__view) {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: 100%;
  padding-right: 6px;
}

.scada-scroll :deep(.el-scrollbar__bar.is-vertical) {
  width: 8px;
  right: 0;
}

.scada-scroll :deep(.el-scrollbar__thumb) {
  background: rgba(125, 211, 252, 0.28);
  border-radius: 999px;
}

.scada-scroll :deep(.el-scrollbar__thumb:hover) {
  background: rgba(125, 211, 252, 0.4);
}

.scada-group {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.scada-group[open] {
  border-color: rgba(56, 189, 248, 0.15);
}

.scada-group__summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 10px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.04);
  list-style: none;
  user-select: none;
  transition: background 0.15s ease;
}

.scada-group__summary::-webkit-details-marker { display: none; }

.scada-group__summary:hover {
  background: rgba(255, 255, 255, 0.07);
}

.scada-group__info {
  display: flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
}

.scada-group__label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.78);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scada-group__count {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.38);
  flex-shrink: 0;
}

.scada-group__right {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}

.scada-group__badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 5px;
}

.scada-group__badge--ok   { background: rgba(52, 211, 153, 0.14); color: #6ee7b7; }
.scada-group__badge--warn { background: rgba(248, 113, 113, 0.14); color: #fca5a5; }

.scada-group__caret {
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 5px solid rgba(255, 255, 255, 0.35);
  transition: transform 0.18s ease;
}

.scada-group[open] .scada-group__caret {
  transform: rotate(180deg);
}

.scada-group__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px 6px;
  background: rgba(0, 0, 0, 0.12);
}

.scada-item {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 7px;
  border-radius: 7px;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s ease;
  width: 100%;
}

.scada-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.scada-item--active {
  background: rgba(56, 189, 248, 0.1);
  border: 1px solid rgba(56, 189, 248, 0.2);
}

.scada-item--offline {
  opacity: 0.55;
}

.scada-item__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.scada-item__dot--on  { background: #34d399; }
.scada-item__dot--off { background: #6b7280; }

.scada-item__name {
  flex: 1;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.72);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scada-item--active .scada-item__name {
  color: #7dd3fc;
}

.scada-item__tag {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.32);
  flex-shrink: 0;
}
</style>
