<script setup lang="ts">
import { useRouter } from 'vue-router'

interface Device {
  id?: number
  name?: string
  device_type?: string
  energy_type?: string
  location?: string
  is_active?: boolean
}

interface SpotlightSummaryItem {
  label: string
  value: string
  tone?: 'default' | 'good' | 'warn'
}

const props = defineProps<{
  deviceName: string
  deviceType: string
  energyType: string
  statusLabel: string
  statusTone: 'online' | 'offline' | 'alarm'
  currentValue: number
  currentUnit: string
  measurementLabel: string
  todayValue: number
  todayUnit: string
  ratedCapacity: number
  capacityUtilization: number | null
  summaryItems: SpotlightSummaryItem[]
  selectableDevices: Device[]
  currentDeviceId: number | undefined
  loading: boolean
}>()

const emit = defineEmits<{
  'device-change': [id: number]
}>()

const router = useRouter()

function onSelect(event: Event) {
  const id = Number((event.target as HTMLSelectElement).value)
  if (id) emit('device-change', id)
}

function goToDetail() {
  if (props.currentDeviceId) {
    void router.push(`/devices/${props.currentDeviceId}/monitor`)
  }
}

function fmt(v: number, d = 1) {
  return Number.isFinite(v) ? v.toFixed(d) : '0.0'
}
</script>

<template>
  <section class="glass-card spotlight-card">
    <div class="spotlight-header">
      <div class="spotlight-identity">
        <span class="card-eyebrow">Key Device</span>
        <div class="spotlight-name-row">
          <span class="spotlight-name">{{ deviceName }}</span>
          <span class="spotlight-type-tag">{{ deviceType }}</span>
          <span class="spotlight-type-tag spotlight-type-tag--energy">{{ energyType }}</span>
        </div>
      </div>

      <div class="spotlight-controls">
        <div class="spotlight-status" :class="`spotlight-status--${statusTone}`">
          <span class="spotlight-status__dot" />
          <span>{{ statusLabel }}</span>
        </div>
        <select class="device-switcher" :value="currentDeviceId" @change="onSelect">
          <option
            v-for="device in selectableDevices"
            :key="device.id"
            :value="device.id"
          >
            {{ device.name }}
          </option>
        </select>
      </div>
    </div>

    <div class="spotlight-metrics">
      <div class="spotlight-hero">
        <span class="spotlight-hero__label">{{ measurementLabel }}</span>
        <div class="spotlight-hero__value">
          <strong :class="{ loading: loading }">{{ fmt(currentValue) }}</strong>
          <span>{{ currentUnit }}</span>
        </div>
      </div>

      <div class="spotlight-secondary">
        <div class="spotlight-metric spotlight-metric--primary">
          <span>今日累计</span>
          <strong>{{ fmt(todayValue) }}</strong>
          <small>{{ todayUnit }}</small>
        </div>
        <div v-if="ratedCapacity > 0" class="spotlight-metric">
          <span>额定容量</span>
          <strong>{{ fmt(ratedCapacity) }}</strong>
          <small>{{ currentUnit }}</small>
        </div>
        <div v-if="capacityUtilization !== null" class="spotlight-metric">
          <span>利用率</span>
          <strong>{{ capacityUtilization.toFixed(0) }}</strong>
          <small>%</small>
        </div>
      </div>

      <div class="spotlight-summary-grid">
        <div
          v-for="item in summaryItems"
          :key="item.label"
          class="spotlight-summary-card"
          :class="item.tone ? `spotlight-summary-card--${item.tone}` : ''"
        >
          <span class="spotlight-summary-card__label">{{ item.label }}</span>
          <strong class="spotlight-summary-card__value">{{ item.value }}</strong>
        </div>
      </div>
    </div>

    <button class="spotlight-link" type="button" @click="goToDetail">
      查看详情 →
    </button>
  </section>
</template>

<style scoped>
.spotlight-card {
  padding: 14px;
  gap: 0;
}

.spotlight-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.spotlight-identity {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.card-eyebrow {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: rgba(255, 255, 255, 0.38);
}

.spotlight-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.spotlight-name {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: #f0f6ff;
}

.spotlight-type-tag {
  padding: 2px 7px;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.07);
  font-size: 10px;
  color: rgba(255, 255, 255, 0.55);
  white-space: nowrap;
}

.spotlight-type-tag--energy {
  background: rgba(56, 189, 248, 0.1);
  color: #7dd3fc;
}

.spotlight-controls {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.spotlight-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 500;
}

.spotlight-status--online  { background: rgba(52, 211, 153, 0.12); color: #6ee7b7; }
.spotlight-status--offline { background: rgba(248, 113, 113, 0.12); color: #fca5a5; }
.spotlight-status--alarm   { background: rgba(251, 146, 60, 0.12); color: #fdba74; }

.spotlight-status__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.spotlight-status--online  .spotlight-status__dot { box-shadow: 0 0 6px rgba(52, 211, 153, 0.6); }
.spotlight-status--offline .spotlight-status__dot { box-shadow: 0 0 6px rgba(248, 113, 113, 0.5); }
.spotlight-status--alarm   .spotlight-status__dot { box-shadow: 0 0 6px rgba(251, 146, 60, 0.5); }

.device-switcher {
  appearance: none;
  padding: 4px 22px 4px 8px;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.07) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%2394a3b8' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E") no-repeat right 6px center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.75);
  font-size: 11px;
  cursor: pointer;
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-switcher:focus {
  outline: none;
  border-color: rgba(56, 189, 248, 0.4);
}

.device-switcher option {
  background: #131d2b;
  color: #f0f6ff;
}

.spotlight-metrics {
  display: grid;
  grid-template-columns: 220px 120px minmax(220px, 1fr);
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  margin-bottom: 10px;
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.spotlight-hero {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.spotlight-hero__label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.44);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.spotlight-hero__value {
  display: flex;
  align-items: baseline;
  gap: 5px;
  min-width: 0;
}

.spotlight-hero__value strong {
  display: inline-block;
  width: 4.8ch;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.05em;
  color: #38bdf8;
  line-height: 1;
  text-align: right;
  font-variant-numeric: tabular-nums;
  transition: opacity 0.2s ease;
}

.spotlight-hero__value strong.loading {
  opacity: 0.72;
}

.spotlight-hero__value span {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.spotlight-secondary {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 12px;
  border-left: 1px solid rgba(255, 255, 255, 0.07);
  min-width: 0;
}

.spotlight-metric--primary {
  margin-bottom: 2px;
}

.spotlight-metric {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.spotlight-metric span {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  min-width: 50px;
}

.spotlight-metric strong {
  font-size: 14px;
  font-weight: 600;
  color: #e2eeff;
}

.spotlight-metric small {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.38);
}

.spotlight-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  min-width: 0;
}

.spotlight-summary-card {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-height: 58px;
  padding: 9px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.spotlight-summary-card--good {
  background: rgba(52, 211, 153, 0.06);
  border-color: rgba(52, 211, 153, 0.14);
}

.spotlight-summary-card--warn {
  background: rgba(251, 146, 60, 0.06);
  border-color: rgba(251, 146, 60, 0.14);
}

.spotlight-summary-card__label {
  font-size: 10px;
  letter-spacing: 0.04em;
  color: rgba(255, 255, 255, 0.42);
}

.spotlight-summary-card__value {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
  color: #e7f1ff;
}

.spotlight-link {
  align-self: flex-end;
  padding: 0;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 11px;
  color: rgba(56, 189, 248, 0.7);
  letter-spacing: 0.02em;
  transition: color 0.15s ease;
}

.spotlight-link:hover {
  color: #38bdf8;
}
</style>
