<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useSocketStore } from '@/stores/useSocketStore'
import { useAuthStore } from '@/stores/useAuthStore'
import { useAlarmPolling } from '@/features/alarm/composables/useAlarmPolling'
import { useDashboardCharts } from '@/features/dashboard/composables/useDashboardCharts'
import { useDashboardClock } from '@/features/dashboard/composables/useDashboardClock'
import { useDashboardDeviceSelection } from '@/features/dashboard/composables/useDashboardDeviceSelection'
import { useDashboardEnergyStats } from '@/features/dashboard/composables/useDashboardEnergyStats'
import { useDashboardRealtime } from '@/features/dashboard/composables/useDashboardRealtime'
import KpiStrip from '@/features/dashboard/components/KpiStrip.vue'
import OnlineGauge from '@/features/dashboard/components/OnlineGauge.vue'
import EnergyMix from '@/features/dashboard/components/EnergyMix.vue'
import AlarmFeed from '@/features/dashboard/components/AlarmFeed.vue'
import TrendPanel from '@/features/dashboard/components/TrendPanel.vue'
import DeviceSpotlight from '@/features/dashboard/components/DeviceSpotlight.vue'
import ScadaBoard from '@/features/dashboard/components/ScadaBoard.vue'
import RegionRanking from '@/features/dashboard/components/RegionRanking.vue'
import type { Device } from '@/api/device'
import type { DeviceAnalysis } from '@/api/telemetry'
import {
  getDeviceMonitorOverview,
  getDeviceMonitorStatusHistory,
  type DeviceStatusEvent,
  type MonitorOverview,
} from '@/api/deviceMonitor'

const socketStore = useSocketStore()
const authStore = useAuthStore()
const { latestMessage, isConnected } = storeToRefs(socketStore)
const { alarmCount, alarmList } = useAlarmPolling({ interval: 10000 })
const { currentTime, currentDate } = useDashboardClock()
const { currentDevice, currentDeviceId, deviceList, selectableDevices, totalDevices, onlineDevices, loadDeviceList } = useDashboardDeviceSelection()
const { energyStats, todayEnergy, monthlyEnergy, loadEnergyStats } = useDashboardEnergyStats()
const {
  analysisSnapshot,
  displayCurrent,
  displayEnergy,
  displayPower,
  energyTrendData,
  loading: realtimeLoading,
  realTimeData,
  loadDeviceData
} = useDashboardRealtime({
  currentDeviceId,
  deviceList,
  latestMessage
})

const monitorOverview = ref<MonitorOverview | null>(null)
const monitorStatusHistory = ref<DeviceStatusEvent[]>([])
const focusCardDevice = ref<Device | undefined>(undefined)
const focusCardOverview = ref<MonitorOverview | null>(null)
const focusCardAnalysis = ref<DeviceAnalysis | null>(null)
const focusCardRealtime = ref({
  power: 0,
  energy: 0,
  current: 0,
  voltage: 0
})
const focusCardSwitching = ref(false)
const locationScope = computed(() => authStore.locationScope?.trim() || '')

const energyNameMap: Record<string, string> = {
  electricity: '电力',
  water: '水务',
  gas: '燃气',
  heat: '热力',
  cooling: '冷量'
}

const deviceTypeMap: Record<string, string> = {
  load: '负荷设备',
  electricity: '电表',
  water: '水表',
  gas: '气表',
  heat: '热量表',
  cooling: '冷量表',
  storage: '储能设备'
}

const deviceCategoryMap: Record<string, string> = {
  load: '负荷设备',
  solar: '光伏发电',
  wind: '风力发电',
  storage: '储能设备',
  charger: '充电桩',
  water_meter: '水表',
  gas_meter: '燃气表',
  heat_meter: '热量表',
  cooling_meter: '冷量表'
}

function formatAlarmTime(timestamp: string) {
  const diffMinutes = Math.max(0, Math.round((Date.now() - new Date(timestamp).getTime()) / 60000))
  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes} 分钟前`
  const diffHours = Math.round(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours} 小时前`
  return new Date(timestamp).toLocaleString('zh-CN', { hour12: false })
}

function resolveShiftLabel(current: string) {
  const hour = Number(current.split(':')[0] || Number.NaN)
  if (!Number.isFinite(hour)) return '白天时段'
  if (hour >= 8 && hour < 18) return '白天时段'
  if (hour >= 18 && hour < 23) return '夜间值守'
  return '深夜巡检'
}

function formatNumber(value: number, digits = 1) {
  return Number.isFinite(value) ? value.toFixed(digits) : '0.0'
}

function formatCompactDateTime(value?: string | null) {
  if (!value) return '--'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'

  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

function resolvePreferredDeviceId() {
  const devices = selectableDevices.value
  const exactHeatMeter = devices.find((device) => device.name?.includes('1号热量表'))
  if (exactHeatMeter?.id) return exactHeatMeter.id

  const heatMeter = devices.find((device) => device.energy_type === 'heat')
  if (heatMeter?.id) return heatMeter.id

  const fallback = devices.find((device) => device.device_type === 'load')
  return fallback?.id || devices[0]?.id
}

function syncFocusCardState() {
  focusCardDevice.value = currentDevice.value || focusDevice.value
  focusCardOverview.value = monitorOverview.value
  focusCardAnalysis.value = analysisSnapshot.value
  focusCardRealtime.value = {
    power: realTimeData.power,
    energy: realTimeData.energy,
    current: realTimeData.current,
    voltage: realTimeData.voltage
  }
}

const onlineRate = computed(() => {
  if (totalDevices.value === 0) return 0
  return Math.round((onlineDevices.value / totalDevices.value) * 100)
})

const offlineDevices = computed(() => Math.max(0, totalDevices.value - onlineDevices.value))

const focusDevice = computed<Device | undefined>(() => {
  if (currentDevice.value) return currentDevice.value
  return selectableDevices.value.find((device) => device.id === resolvePreferredDeviceId())
})

const focusArchive = computed(() => focusCardOverview.value?.archive)
const focusIdentity = computed(() => focusArchive.value || focusCardDevice.value || focusDevice.value)
const focusDeviceName = computed(() => focusIdentity.value?.name || '1号热量表')
const focusDeviceType = computed(() => deviceTypeMap[focusIdentity.value?.device_type || ''] || focusIdentity.value?.device_type || '热量表')
const focusEnergyType = computed(() => energyNameMap[focusIdentity.value?.energy_type || ''] || focusIdentity.value?.energy_type || '热力')
const focusRuntime = computed(() => focusCardOverview.value?.runtime_status)
const focusIngestion = computed<Record<string, unknown>>(() => (focusCardOverview.value?.ingestion_health as Record<string, unknown>) || {})
const focusStatusLabel = computed(() => {
  if (focusDevice.value?.is_active === false || focusRuntime.value?.is_active === false) {
    return '离线待机'
  }

  if (focusRuntime.value?.code === 'alarm') {
    return focusRuntime.value?.label || '告警中'
  }

  if (focusRuntime.value?.code === 'degraded') {
    return focusRuntime.value?.label || '运行波动'
  }

  return '在线运行'
})

const focusStatusTone = computed((): 'online' | 'offline' | 'alarm' => {
  if (focusDevice.value?.is_active === false || focusRuntime.value?.is_active === false) {
    return 'offline'
  }

  if (focusRuntime.value?.code === 'alarm') {
    return 'alarm'
  }

  return 'online'
})
const focusRatedCapacity = computed(() => Number(focusArchive.value?.rated_capacity || focusDevice.value?.rated_capacity || 0))
const focusCapacityUtilization = computed(() => {
  if (focusRatedCapacity.value <= 0) return null
  return Math.min(100, Math.max(0, (Math.abs(focusCardRealtime.value.power) / focusRatedCapacity.value) * 100))
})

const warningThreshold = computed(() => {
  if (focusRatedCapacity.value > 0) return focusRatedCapacity.value * 0.85
  if (Math.abs(focusCardRealtime.value.power) > 0) return Math.max(Math.abs(focusCardRealtime.value.power) * 1.5, 50)
  return 50
})

const focusMeasurementLabel = computed(() => focusCardAnalysis.value?.current_value_label || '当前瞬时值')
const focusMeasurementUnit = computed(() => focusCardAnalysis.value?.current_value_unit || focusArchive.value?.unit || 'kW')
const focusTodayUnit = computed(() => focusCardAnalysis.value?.today_consumption_unit || 'kWh')
const focusSummaryItems = computed(() => {
  const latestReportAt = focusRuntime.value?.latest_timestamp || focusRuntime.value?.last_success_at || focusRuntime.value?.last_message_at
  const alarmCount = focusRuntime.value?.unresolved_alarm_count || 0
  const communicationValue = focusRuntime.value?.is_online
    ? '正常'
    : (focusRuntime.value?.is_active === false ? '停用' : '待确认')

  return [
    { label: '最近上报', value: formatCompactDateTime(latestReportAt) },
    { label: '通讯状态', value: communicationValue, tone: focusRuntime.value?.is_online ? 'good' as const : 'warn' as const },
    { label: '今日告警', value: `${alarmCount} 条`, tone: alarmCount > 0 ? 'warn' as const : 'good' as const },
    { label: '安装位置', value: focusIdentity.value?.location?.trim() || '未标注' }
  ]
})

const charts = useDashboardCharts({
  currentDevice: focusDevice,
  energyTrendData,
  warningThreshold,
  displayPower,
  gaugeValue: onlineRate,
  gaugeUnit: '%',
  gaugeMax: 100,
  energyStats,
})

const trendChartEl = charts.mainChart.chartRef
const gaugeChartEl = charts.gaugeChart.chartRef
const pieChartEl = charts.pieChart.chartRef

const trendValues = computed(() => energyTrendData.values.map((value) => Math.abs(Number(value) || 0)))
const trendCurrent = computed(() => trendValues.value.at(-1) || 0)
const trendPeak = computed(() => (trendValues.value.length ? Math.max(...trendValues.value) : 0))
const trendValley = computed(() => (trendValues.value.length ? Math.min(...trendValues.value) : 0))
const trendAverage = computed(() => {
  if (trendValues.value.length === 0) return 0
  return trendValues.value.reduce((sum, value) => sum + value, 0) / trendValues.value.length
})

const hasEnergyDistributionData = computed(() => (
  Object.values(energyStats).some((item) => (item?.total_consumption || 0) > 0)
))

const trendStats = computed(() => [
  { label: '当前值', value: `${formatNumber(trendCurrent.value)} kW` },
  { label: '峰值', value: `${formatNumber(trendPeak.value)} kW` },
  { label: '谷值', value: `${formatNumber(trendValley.value)} kW` },
  { label: '均值', value: `${formatNumber(trendAverage.value)} kW` }
])

const unresolvedAlarms = computed(() => (
  alarmList.value.slice(0, 4).map((alarm) => ({
    id: alarm.id,
    message: alarm.message,
    time: formatAlarmTime(alarm.timestamp)
  }))
))

const scadaDeviceGroups = computed(() => {
  const groups = new Map<string, { key: string; label: string; devices: typeof selectableDevices.value }>()

  for (const device of selectableDevices.value) {
    const categoryKey = (device.device_category || device.device_type || 'uncategorized').trim()
    const categoryLabel = deviceCategoryMap[categoryKey] || deviceTypeMap[categoryKey] || categoryKey || '未分类设备'
    const existing = groups.get(categoryKey)

    if (existing) {
      existing.devices.push(device)
      continue
    }

    groups.set(categoryKey, {
      key: categoryKey,
      label: categoryLabel,
      devices: [device]
    })
  }

  return Array.from(groups.values())
    .sort((left, right) => right.devices.length - left.devices.length)
    .map((group) => ({
      ...group,
      online: group.devices.filter((device) => device.is_active).length
    }))
})

const regionRankings = computed(() => {
  const regions = new Map<string, { score: number; online: number; total: number }>()
  for (const device of deviceList.value) {
    const region = device.location?.trim() || '未分区'
    const current = regions.get(region) || { score: 0, online: 0, total: 0 }
    const ratedCapacity = Number(device.rated_capacity || 0)
    current.total += 1
    if (device.is_active) current.online += 1
    current.score += ratedCapacity > 0 ? ratedCapacity : (device.is_active ? 24 : 8)
    regions.set(region, current)
  }

  return Array.from(regions.entries())
    .map(([name, stats]) => ({ name, ...stats }))
    .sort((left, right) => right.score - left.score)
    .slice(0, 5)
})

const statusLabel = computed(() => (isConnected.value ? '系统正常运行' : '通讯链路中断'))
const dashboardSubtitle = computed(() => {
  if (!locationScope.value) return '面向园区、区域、楼栋与设备表计的综合能源管理平台'
  return `当前范围：${locationScope.value}`
})

const selectDevice = (deviceId?: number) => {
  if (typeof deviceId !== 'number' || deviceId === currentDeviceId.value) return
  currentDeviceId.value = deviceId
}

const loadFocusMonitorData = async () => {
  if (!currentDeviceId.value) return

  try {
    const [overview, history] = await Promise.all([
      getDeviceMonitorOverview(currentDeviceId.value),
      getDeviceMonitorStatusHistory(currentDeviceId.value, { limit: 6, hours: 48 })
    ])
    monitorOverview.value = overview
    monitorStatusHistory.value = history.items || []
  } catch {
    monitorOverview.value = null
    monitorStatusHistory.value = []
  }
}

onMounted(async () => {
  socketStore.connect()
  await nextTick()
  await loadDeviceList()

  const preferredId = resolvePreferredDeviceId()
  if (preferredId) currentDeviceId.value = preferredId

  await Promise.all([
    loadDeviceData(),
    loadEnergyStats(),
    loadFocusMonitorData()
  ])

  syncFocusCardState()

  await charts.initCharts()
})

watch(currentDeviceId, async (deviceId, previousId) => {
  if (!deviceId || deviceId === previousId) return

  focusCardSwitching.value = true

  try {
    await Promise.all([
      loadDeviceData(),
      loadFocusMonitorData()
    ])
    if (currentDeviceId.value === deviceId) {
      syncFocusCardState()
    }
  } finally {
    if (currentDeviceId.value === deviceId) {
      focusCardSwitching.value = false
    }
  }
})

watch(
  [analysisSnapshot, monitorOverview, () => realTimeData.power, () => realTimeData.energy, () => realTimeData.current, () => realTimeData.voltage],
  () => {
    if (focusCardSwitching.value) return
    if (!currentDeviceId.value) return
    syncFocusCardState()
  }
)
</script>

<template>
  <div class="ems-cockpit">
    <div class="cockpit-noise" />

    <!-- ── 顶部 Header（极简化） ── -->
    <header class="top-header">
      <div class="brand-block">
        <div class="brand-mark">
          <span class="brand-mark__dot" />
        </div>
        <div class="brand-text">
          <p class="brand-kicker">Park Energy Cockpit</p>
          <h1>园区综合能源管理系统</h1>
          <p class="brand-subtitle">{{ dashboardSubtitle }}</p>
        </div>
      </div>

      <div class="header-right">
        <div class="time-panel">
          <span class="time-panel__date">{{ currentDate }}</span>
          <strong class="time-panel__clock">{{ currentTime }}</strong>
        </div>
        <div class="run-badge" :class="{ 'run-badge--offline': !isConnected }">
          <span class="run-badge__dot" />
          <span>{{ statusLabel }}</span>
        </div>
      </div>
    </header>

    <!-- ── KPI Strip（全宽核心指标） ── -->
    <KpiStrip
      :current-load="displayPower"
      :online-count="onlineDevices"
      :total-count="totalDevices"
      :alarm-count="alarmCount"
      :today-energy="todayEnergy"
      :monthly-energy="monthlyEnergy"
      :shift="resolveShiftLabel(currentTime)"
    />

    <!-- ── 主内容三栏布局 ── -->
    <main class="bento-layout">

      <!-- 左栏 -->
      <aside class="left-column">
        <OnlineGauge
          :online-count="onlineDevices"
          :offline-count="offlineDevices"
          :total-count="totalDevices"
          :online-rate="onlineRate"
        >
          <template #chart>
            <div ref="gaugeChartEl" class="chart-mount" />
          </template>
        </OnlineGauge>

        <EnergyMix
          :today-energy="todayEnergy"
          :monthly-energy="monthlyEnergy"
          :has-distribution-data="hasEnergyDistributionData"
        >
          <template #chart>
            <div ref="pieChartEl" class="chart-mount" />
          </template>
        </EnergyMix>

        <AlarmFeed :alarms="unresolvedAlarms" />
      </aside>

      <!-- 中栏 -->
      <section class="center-column">
        <TrendPanel :stats="trendStats">
          <template #chart>
            <div ref="trendChartEl" class="chart-mount" />
          </template>
        </TrendPanel>

        <DeviceSpotlight
          :device-name="focusDeviceName"
          :device-type="focusDeviceType"
          :energy-type="focusEnergyType"
          :status-label="focusStatusLabel"
          :status-tone="focusStatusTone"
          :current-value="Math.abs(focusCardRealtime.power)"
          :current-unit="focusMeasurementUnit"
          :measurement-label="focusMeasurementLabel"
          :today-value="Math.abs(focusCardRealtime.energy)"
          :today-unit="focusTodayUnit"
          :rated-capacity="focusRatedCapacity"
          :capacity-utilization="focusCapacityUtilization"
          :summary-items="focusSummaryItems"
          :selectable-devices="selectableDevices"
          :current-device-id="currentDeviceId"
          :loading="focusCardSwitching"
          @device-change="selectDevice"
        />
      </section>

      <!-- 右栏 -->
      <aside class="right-column">
        <ScadaBoard
          :groups="scadaDeviceGroups"
          :current-device-id="currentDeviceId"
          :online-count="onlineDevices"
          :total-count="totalDevices"
          @select-device="selectDevice"
        />

        <RegionRanking :rankings="regionRankings" />
      </aside>
    </main>
  </div>
</template>

<style scoped>
/* ── 页面容器 ── */
.ems-cockpit {
  position: relative;
  width: 100%;
  min-height: 100%;
  height: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  overflow-y: auto;
  overflow-x: hidden;
  color: #f5f7fa;
  background:
    radial-gradient(circle at top left, rgba(107, 184, 255, 0.08), transparent 28%),
    radial-gradient(circle at bottom right, rgba(56, 189, 248, 0.05), transparent 26%),
    #090e17;
  box-sizing: border-box;
}

.cockpit-noise {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(255,255,255,0.012), transparent 20%, transparent 80%, rgba(255,255,255,0.012));
  opacity: 0.3;
  z-index: 0;
}

/* ── Header（极简） ── */
.top-header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 108px;
  padding: 22px 22px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px) saturate(135%);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06), 0 8px 24px rgba(0,0,0,0.18);
  box-sizing: border-box;
}

.brand-block {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: rgba(107, 184, 255, 0.12);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
  margin-top: 2px;
}

.brand-mark__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #6bb8ff;
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.brand-kicker {
  margin: 0;
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.46);
}

.brand-text h1 {
  margin: 0;
  font-size: clamp(22px, 2vw, 28px);
  font-weight: 700;
  line-height: 1.02;
  letter-spacing: -0.04em;
}

.brand-subtitle {
  margin: 0;
  font-size: 12px;
  color: rgba(255,255,255,0.48);
  line-height: 1.3;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.time-panel {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.time-panel__date {
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.44);
}

.time-panel__clock {
  font-size: clamp(20px, 1.7vw, 24px);
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.03em;
}

.run-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(0, 224, 176, 0.1);
  box-shadow: inset 0 0 0 1px rgba(0, 224, 176, 0.18);
  color: #c8fff4;
  font-size: 10px;
  font-weight: 500;
}

.run-badge__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #00e0b0;
  box-shadow: 0 0 10px rgba(0, 224, 176, 0.5);
}

.run-badge--offline {
  background: rgba(248, 113, 113, 0.1);
  box-shadow: inset 0 0 0 1px rgba(248, 113, 113, 0.2);
  color: #ffe2e2;
}

.run-badge--offline .run-badge__dot {
  background: #f87171;
  box-shadow: 0 0 10px rgba(248, 113, 113, 0.5);
}

/* ── 三栏网格布局 ── */
.bento-layout {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(200px, 0.82fr) minmax(0, 1.8fr) minmax(200px, 0.82fr);
  grid-template-rows: 1fr;
  gap: 12px;
}

.left-column {
  display: grid;
  grid-template-rows: auto auto auto;
  gap: 12px;
  min-height: 0;
}

.center-column {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 12px;
  min-height: 0;
}

.right-column {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 12px;
  min-height: 0;
}

/* ── ECharts 挂载容器 ── */
.chart-mount {
  width: 100%;
  height: 100%;
}
</style>
