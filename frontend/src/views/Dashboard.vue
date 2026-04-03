<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useSocketStore } from '@/stores/useSocketStore'
import { useAuthStore } from '@/stores/useAuthStore'
import { useAlarmPolling } from '@/features/alarm/composables/useAlarmPolling'
import { useDashboardClock } from '@/features/dashboard/composables/useDashboardClock'
import { useDashboardDeviceSelection } from '@/features/dashboard/composables/useDashboardDeviceSelection'
import { useDashboardEnergyStats } from '@/features/dashboard/composables/useDashboardEnergyStats'
import { useDashboardRealtime } from '@/features/dashboard/composables/useDashboardRealtime'
import type { Device } from '@/api/device'
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

const BRAND = '#00e0b0'
const monitorOverview = ref<MonitorOverview | null>(null)
const monitorStatusHistory = ref<DeviceStatusEvent[]>([])
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

function formatDateTime(value?: string | null) {
  if (!value) return '暂无记录'
  return new Date(value).toLocaleString('zh-CN', {
    hour12: false,
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function createSmoothPath(values: number[], width: number, height: number) {
  if (values.length === 0) {
    const mid = height * 0.55
    return {
      line: `M 0 ${mid} C ${width * 0.25} ${mid} ${width * 0.75} ${mid} ${width} ${mid}`,
      area: `M 0 ${height} L 0 ${mid} C ${width * 0.25} ${mid} ${width * 0.75} ${mid} ${width} ${mid} L ${width} ${height} Z`
    }
  }

  const safeMin = Math.min(...values)
  const safeMax = Math.max(...values)
  const range = Math.max(safeMax - safeMin, 1)
  const points = values.map((value, index) => {
    const x = values.length === 1 ? width / 2 : (index / (values.length - 1)) * width
    const y = height - ((value - safeMin) / range) * (height * 0.72 + 8) - 18
    return { x, y }
  })

  let line = `M ${points[0].x} ${points[0].y}`
  for (let index = 0; index < points.length - 1; index += 1) {
    const current = points[index]
    const next = points[index + 1]
    const cpX = (current.x + next.x) / 2
    line += ` C ${cpX} ${current.y}, ${cpX} ${next.y}, ${next.x} ${next.y}`
  }

  return {
    line,
    area: `${line} L ${width} ${height} L 0 ${height} Z`
  }
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

const onlineRate = computed(() => {
  if (totalDevices.value === 0) return 0
  return Math.round((onlineDevices.value / totalDevices.value) * 100)
})

const offlineDevices = computed(() => Math.max(0, totalDevices.value - onlineDevices.value))

const focusDevice = computed<Device | undefined>(() => {
  if (currentDevice.value) return currentDevice.value
  return selectableDevices.value.find((device) => device.id === resolvePreferredDeviceId())
})

const focusDeviceName = computed(() => focusDevice.value?.name || '1号热量表')
const focusDeviceType = computed(() => deviceTypeMap[focusDevice.value?.device_type || ''] || focusDevice.value?.device_type || '热量表')
const focusEnergyType = computed(() => energyNameMap[focusDevice.value?.energy_type || ''] || focusDevice.value?.energy_type || '热力')
const focusArchive = computed(() => monitorOverview.value?.archive)
const focusRuntime = computed(() => monitorOverview.value?.runtime_status)
const focusRealtime = computed(() => monitorOverview.value?.realtime)
const focusIngestion = computed<Record<string, unknown>>(() => (monitorOverview.value?.ingestion_health as Record<string, unknown>) || {})
const focusStatusLabel = computed(() => focusRuntime.value?.label || (focusDevice.value?.is_active ? '在线运行' : '离线待机'))
const focusStatusTone = computed(() => {
  const code = focusRuntime.value?.code
  if (code === 'offline' || code === 'stopped') return 'offline'
  if (code === 'alarm') return 'alarm'
  return 'online'
})
const focusRatedCapacity = computed(() => Number(focusArchive.value?.rated_capacity || focusDevice.value?.rated_capacity || 0))
const focusCapacityUtilization = computed(() => {
  if (focusRatedCapacity.value <= 0) return null
  return Math.min(100, Math.max(0, (displayPower.value / focusRatedCapacity.value) * 100))
})
const focusEnergyShare = computed(() => {
  const energyType = focusDevice.value?.energy_type || focusArchive.value?.energy_type
  const total = Number(energyStats[energyType || '']?.total_consumption || 0)
  if (total <= 0) return null
  return Math.min(100, Math.max(0, (displayEnergy.value / total) * 100))
})
const focusSuccessRate = computed(() => {
  const value = Number(focusIngestion.value.success_rate || 0)
  return Number.isFinite(value) ? value : 0
})
const focusMeasurementLabel = computed(() => analysisSnapshot.value?.current_value_label || '当前瞬时值')
const focusMeasurementUnit = computed(() => analysisSnapshot.value?.current_value_unit || focusArchive.value?.unit || 'kW')
const focusTodayLabel = computed(() => analysisSnapshot.value?.today_consumption_label || `今日${focusEnergyType.value}累计`)
const focusTodayUnit = computed(() => analysisSnapshot.value?.today_consumption_unit || 'kWh')
const focusTodayCost = computed(() => Number(analysisSnapshot.value?.today_cost || 0))
const focusElectricalApplicable = computed(() => Boolean(analysisSnapshot.value?.electrical_fields_applicable))

const summaryMetrics = computed(() => [
  {
    label: '今日总能耗',
    value: formatNumber(todayEnergy.value),
    unit: 'kWh',
    caption: '覆盖电 / 水 / 气 / 冷 / 热'
  },
  {
    label: '本月总能耗',
    value: formatNumber(monthlyEnergy.value),
    unit: 'kWh',
    caption: '自然月累计'
  },
  {
    label: '实时负荷',
    value: formatNumber(displayPower.value),
    unit: 'kW',
    caption: `${resolveShiftLabel(currentTime.value)}`
  },
  {
    label: '在线设备',
    value: String(onlineDevices.value),
    unit: `/ ${totalDevices.value || 0}`,
    caption: `在线率 ${onlineRate.value}%`
  }
])

const trendValues = computed(() => energyTrendData.values.map((value) => Math.abs(Number(value) || 0)))
const trendCurrent = computed(() => trendValues.value.at(-1) || 0)
const trendPeak = computed(() => (trendValues.value.length ? Math.max(...trendValues.value) : 0))
const trendValley = computed(() => (trendValues.value.length ? Math.min(...trendValues.value) : 0))
const trendAverage = computed(() => {
  if (trendValues.value.length === 0) return 0
  return trendValues.value.reduce((sum, value) => sum + value, 0) / trendValues.value.length
})

const trendStats = computed(() => [
  { label: '当前值', value: `${formatNumber(trendCurrent.value)} kW` },
  { label: '峰值', value: `${formatNumber(trendPeak.value)} kW` },
  { label: '谷值', value: `${formatNumber(trendValley.value)} kW` },
  { label: '均值', value: `${formatNumber(trendAverage.value)} kW` }
])

const trendPath = computed(() => createSmoothPath(trendValues.value, 920, 260))
const headerTrendPath = computed(() => createSmoothPath(trendValues.value, 280, 92))

const trendAxisLabels = computed(() => {
  const times = energyTrendData.times
  if (times.length <= 6) return times
  return [times[0], times[Math.floor(times.length * 0.25)], times[Math.floor(times.length * 0.5)], times[Math.floor(times.length * 0.75)], times.at(-1) || '']
})

const energyMixItems = computed(() => {
  const items = [
    { key: 'electricity', color: '#00e0b0', value: energyStats.electricity?.total_consumption || 0 },
    { key: 'water', color: '#5bc0ff', value: energyStats.water?.total_consumption || 0 },
    { key: 'gas', color: '#ffb86b', value: energyStats.gas?.total_consumption || 0 },
    { key: 'heat', color: '#ff7b9c', value: energyStats.heat?.total_consumption || 0 },
    { key: 'cooling', color: '#b390ff', value: energyStats.cooling?.total_consumption || 0 }
  ].filter((item) => item.value > 0)

  const total = items.reduce((sum, item) => sum + item.value, 0)
  return {
    total,
    items: items.map((item) => ({
      ...item,
      label: energyNameMap[item.key],
      percent: total > 0 ? (item.value / total) * 100 : 0
    }))
  }
})

const energyMixRingStyle = computed(() => {
  if (energyMixItems.value.items.length === 0) {
    return { background: 'conic-gradient(from 180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04))' }
  }

  let cursor = 0
  const segments = energyMixItems.value.items.map((item) => {
    const start = cursor
    cursor += item.percent
    return `${item.color} ${start.toFixed(2)}% ${cursor.toFixed(2)}%`
  })

  return {
    background: `conic-gradient(from 180deg, ${segments.join(', ')})`
  }
})

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

function buildMicroSeries(base: number, deltas: number[]) {
  return deltas.map((delta) => Math.max(0, Number((base + delta).toFixed(1))))
}

const powerSeries = computed(() => {
  if (trendValues.value.length >= 8) return trendValues.value.slice(-8)
  return buildMicroSeries(displayPower.value || 18.3, [-2.4, -1.8, -1.2, -0.4, 0.6, 1.4, 0.8, 0.2])
})

const voltageSeries = computed(() => {
  const base = realTimeData.voltage || 215.1
  return buildMicroSeries(base, [-1.8, -0.6, 0.4, -0.2, 0.8, 1.1, 0.5, 0.2])
})

const currentSeries = computed(() => {
  const base = displayCurrent.value || 84.2
  return buildMicroSeries(base, [-7.2, -4.5, -2.8, -0.7, 2.4, 4.8, 2.1, 1.2])
})

const sparklineWidth = 180
const sparklineHeight = 46
const focusRecentEvents = computed(() => monitorStatusHistory.value.slice(0, 3))
const focusOverviewStats = computed(() => {
  const totalMessages = Number(focusIngestion.value.total_messages || 0)
  const unresolvedAlarms = Number(focusRuntime.value?.unresolved_alarm_count || 0)

  return [
    {
      label: '运行状态',
      value: focusRuntime.value?.label || focusStatusLabel.value,
      caption: focusRuntime.value?.is_online ? '采集链路在线' : '采集链路待恢复'
    },
    {
      label: '采集成功率',
      value: `${focusSuccessRate.value.toFixed(1)}%`,
      caption: totalMessages > 0 ? `${totalMessages} 次消息采样` : '暂无采样记录'
    },
    {
      label: '活动告警',
      value: `${unresolvedAlarms} 条`,
      caption: unresolvedAlarms > 0 ? '需优先关注设备告警' : '当前无未处理告警'
    },
    {
      label: '额定容量',
      value: focusRatedCapacity.value > 0 ? `${formatNumber(focusRatedCapacity.value)} ${focusArchive.value?.unit || focusMeasurementUnit.value}` : '--',
      caption: focusCapacityUtilization.value !== null ? `利用率 ${focusCapacityUtilization.value.toFixed(0)}%` : '后端暂未配置额定值'
    }
  ]
})

const focusTelemetryCards = computed(() => {
  const powerSpark = createSmoothPath(powerSeries.value, sparklineWidth, sparklineHeight)
  const currentSpark = createSmoothPath(currentSeries.value, sparklineWidth, sparklineHeight)
  const voltageSpark = createSmoothPath(voltageSeries.value, sparklineWidth, sparklineHeight)
  const totalMessages = Number(focusIngestion.value.total_messages || 0)
  const lastSuccessAt = String(focusRuntime.value?.last_success_at || focusRuntime.value?.latest_timestamp || '')

  const cards = [
    {
      label: focusMeasurementLabel.value,
      value: `${formatNumber(displayPower.value)} ${focusMeasurementUnit.value}`,
      icon: '⚡',
      helper: '过去 1 小时波动',
      spark: powerSpark,
      footer: `峰值 ${formatNumber(trendPeak.value)} kW`,
      meta: [
        { label: '均值', value: `${formatNumber(trendAverage.value)} kW` },
        { label: '谷值', value: `${formatNumber(trendValley.value)} kW` }
      ]
    },
    {
      label: focusTodayLabel.value,
      value: `${formatNumber(displayEnergy.value)} ${focusTodayUnit.value}`,
      icon: '◔',
      helper: '占园区同介质当日总量',
      progress: focusEnergyShare.value ?? 0,
      footer: focusTodayCost.value > 0 ? `当日成本 ¥${focusTodayCost.value.toFixed(2)}` : '后端已返回成本口径',
      meta: [
        { label: '占比', value: `${(focusEnergyShare.value ?? 0).toFixed(0)}%` },
        { label: '成本', value: `¥${focusTodayCost.value.toFixed(2)}` }
      ]
    },
    {
      label: focusCapacityUtilization.value !== null ? '额定容量利用率' : '采集健康度',
      value: focusCapacityUtilization.value !== null ? `${focusCapacityUtilization.value.toFixed(0)}%` : `${focusSuccessRate.value.toFixed(1)}%`,
      icon: focusCapacityUtilization.value !== null ? '◫' : '◎',
      helper: focusCapacityUtilization.value !== null ? '当前瞬时值 / 额定容量' : '近阶段消息接入成功率',
      progress: focusCapacityUtilization.value ?? focusSuccessRate.value,
      footer: focusCapacityUtilization.value !== null
        ? `额定值 ${formatNumber(focusRatedCapacity.value)} ${focusArchive.value?.unit || focusMeasurementUnit.value}`
        : `连续失败 ${Number(focusIngestion.value.consecutive_failures || 0)} 次`,
      meta: focusCapacityUtilization.value !== null
        ? [
            { label: '额定值', value: `${formatNumber(focusRatedCapacity.value)}` },
            { label: '状态', value: focusRuntime.value?.label || '--' }
          ]
        : [
            { label: '采样数', value: `${totalMessages}` },
            { label: '失败数', value: `${Number(focusIngestion.value.total_failures || 0)}` }
          ]
    }
  ]

  if (focusElectricalApplicable.value || realTimeData.voltage > 0 || displayCurrent.value > 0) {
    cards.push({
      label: '电气质量',
      value: realTimeData.voltage > 0 ? `${formatNumber(realTimeData.voltage)} V` : `${formatNumber(displayCurrent.value)} A`,
      icon: '🛡',
      helper: realTimeData.voltage > 0 ? '母线电压最近走势' : '电流与负荷同步变化',
      spark: realTimeData.voltage > 0 ? voltageSpark : currentSpark,
      footer: realTimeData.voltage > 0
        ? `最近电流 ${formatNumber(displayCurrent.value)} A`
        : `最近上报 ${formatDateTime(String(focusRuntime.value?.latest_timestamp || ''))}`,
      meta: realTimeData.voltage > 0
        ? [
            { label: '电流', value: `${formatNumber(displayCurrent.value)} A` },
            { label: '上报', value: lastSuccessAt ? formatDateTime(lastSuccessAt).split(' ')[1] || formatDateTime(lastSuccessAt) : '--' }
          ]
        : [
            { label: '成功率', value: `${focusSuccessRate.value.toFixed(1)}%` },
            { label: '上报', value: lastSuccessAt ? formatDateTime(lastSuccessAt).split(' ')[1] || formatDateTime(lastSuccessAt) : '--' }
          ]
    })
  } else {
    cards.push({
      label: '最近上报',
      value: focusRuntime.value?.latest_timestamp ? formatDateTime(String(focusRuntime.value.latest_timestamp)) : '暂无上报',
      icon: '↻',
      helper: '采集链路最近成功写入时间',
      footer: focusIngestion.value.last_failure_reason ? String(focusIngestion.value.last_failure_reason) : '当前没有失败原因记录',
      meta: [
        { label: '成功率', value: `${focusSuccessRate.value.toFixed(1)}%` },
        { label: '采样数', value: `${totalMessages}` }
      ]
    })
  }

  return cards
})

const statusLabel = computed(() => (isConnected.value ? '系统正常运行' : '通讯链路中断'))
const dashboardSubtitle = computed(() => {
  if (!locationScope.value) return '面向园区、区域、楼栋与设备表计的综合能源驾驶舱'
  return `当前范围：${locationScope.value}`
})
const headerHighlights = computed(() => [
  {
    label: '当前时段',
    value: resolveShiftLabel(currentTime.value)
  },
  {
    label: '重点设备',
    value: focusDeviceName.value
  }
])

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
})

watch(currentDeviceId, (deviceId, previousId) => {
  if (!deviceId || deviceId === previousId) return
  void loadDeviceData()
  void loadFocusMonitorData()
})
</script>

<template>
  <div class="ems-cockpit">
    <div class="cockpit-noise" />

    <header class="top-header">
      <div class="top-header__main">
        <div class="brand-block">
          <div class="brand-mark">
            <span class="brand-mark__dot" />
          </div>
          <div>
            <p class="brand-kicker">
              Park Energy Cockpit
            </p>
            <h1>园区综合能源管理系统</h1>
            <p class="brand-subtitle">
              {{ dashboardSubtitle }}
            </p>
          </div>
        </div>
      </div>

      <div class="top-header__panel">
        <div class="header-strip">
          <article
            v-for="item in headerHighlights"
            :key="item.label"
            class="header-highlights__item"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </article>

          <article class="header-highlights__item header-highlights__item--load">
            <span>当前负荷</span>
            <div class="header-load">
              <strong>{{ formatNumber(displayPower) }}</strong>
              <small>kW</small>
            </div>
          </article>
        </div>
        <div class="header-meta">
          <div class="time-panel">
            <span class="time-panel__date">{{ currentDate }}</span>
            <strong>{{ currentTime }}</strong>
          </div>
          <div
            class="run-badge"
            :class="{ 'run-badge--offline': !isConnected }"
          >
            <span class="run-badge__dot" />
            <span>{{ statusLabel }}</span>
          </div>
        </div>
      </div>
    </header>

    <main class="bento-layout">
      <aside class="left-column">
        <section class="glass-card overview-card">
          <div class="card-head">
            <span class="card-eyebrow">Campus Device Pulse</span>
            <span class="card-title">园区设备在线率总览</span>
          </div>
          <div class="overview-compact">
            <div class="overview-rate">
              <span class="overview-rate__label">当前在线率</span>
              <strong>{{ onlineRate }}%</strong>
              <div class="overview-rate__hint">
                <span>在线 {{ onlineDevices }}</span>
                <span>离线 {{ offlineDevices }}</span>
                <span>总数 {{ totalDevices }}</span>
              </div>
            </div>
            <div class="overview-split">
              <div class="overview-stat">
                <div class="overview-stat__label">
                  <span>在线设备</span>
                  <small>active devices</small>
                </div>
                <div class="overview-stat__value">
                  <strong>{{ onlineDevices }}</strong>
                  <small>台</small>
                </div>
              </div>
              <div class="overview-stat">
                <div class="overview-stat__label">
                  <span>离线设备</span>
                  <small>offline devices</small>
                </div>
                <div class="overview-stat__value">
                  <strong>{{ offlineDevices }}</strong>
                  <small>台</small>
                </div>
              </div>
              <div class="overview-stat">
                <div class="overview-stat__label">
                  <span>设备总数</span>
                  <small>total devices</small>
                </div>
                <div class="overview-stat__value">
                  <strong>{{ totalDevices }}</strong>
                  <small>台</small>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="glass-card energy-card">
          <div class="card-head">
            <span class="card-eyebrow">Energy Mix</span>
            <span class="card-title">能源介质占比</span>
          </div>

          <div class="energy-mix">
            <div
              class="energy-ring"
              :class="{ 'energy-ring--dense': energyMixItems.items.length >= 4 }"
              :style="energyMixRingStyle"
            >
              <div class="energy-ring__halo" />
              <div class="energy-ring__core">
                <span>总能耗</span>
                <strong>{{ formatNumber(energyMixItems.total) }}</strong>
                <small>kWh</small>
              </div>
            </div>

            <div v-if="energyMixItems.items.length" class="energy-legend energy-legend--grid">
              <div
                v-for="item in energyMixItems.items"
                :key="item.key"
                class="energy-legend__item"
              >
                <div class="energy-legend__topline">
                  <span class="energy-legend__swatch" :style="{ background: item.color }" />
                  <span class="energy-legend__name">{{ item.label }}</span>
                </div>
                <div class="energy-legend__main">
                  <strong>{{ item.percent.toFixed(1) }}%</strong>
                  <div class="energy-legend__value">
                    <span>{{ formatNumber(item.value) }}</span>
                    <small>kWh</small>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="card-empty">
              当前暂无有效能耗分布数据
            </div>
          </div>

          <div class="energy-summary">
            <div class="energy-summary__item">
              <span>今日总能耗</span>
              <div class="energy-summary__main">
                <strong>{{ formatNumber(todayEnergy) }}</strong>
                <small>kWh</small>
              </div>
            </div>
            <div class="energy-summary__item">
              <span>本月总能耗</span>
              <div class="energy-summary__main">
                <strong>{{ formatNumber(monthlyEnergy) }}</strong>
                <small>kWh</small>
              </div>
            </div>
          </div>
        </section>

        <section class="glass-card alarm-card">
          <div class="card-head">
            <span class="card-eyebrow">Pending Alerts</span>
            <span class="card-title">未处理告警信息</span>
          </div>

          <div v-if="unresolvedAlarms.length" class="alarm-stack">
            <article
              v-for="alarm in unresolvedAlarms"
              :key="alarm.id"
              class="alarm-row"
            >
              <div class="alarm-row__pulse" />
              <div class="alarm-row__copy">
                <strong>{{ alarm.message }}</strong>
                <span>{{ alarm.time }}</span>
              </div>
            </article>
          </div>

          <div v-else class="card-empty card-empty--success">
            当前没有未处理告警，园区运行稳定。
          </div>
        </section>
      </aside>

      <section class="center-column">
        <div class="metric-grid">
          <section
            v-for="metric in summaryMetrics"
            :key="metric.label"
            class="glass-card metric-card"
          >
            <span class="metric-card__label">{{ metric.label }}</span>
            <div class="metric-card__value">
              <strong>{{ metric.value }}</strong>
              <small>{{ metric.unit }}</small>
            </div>
            <span class="metric-card__caption">{{ metric.caption }}</span>
          </section>
        </div>

        <section class="glass-card trend-card">
          <div class="card-head card-head--split">
            <div class="trend-head">
              <span class="card-eyebrow">Park Load Trend</span>
              <span class="card-title">园区负荷趋势</span>
            </div>
            <div class="trend-stat-row">
              <div
                v-for="item in trendStats"
                :key="item.label"
                class="trend-stat-pill"
              >
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </div>

          <div class="trend-canvas">
            <svg viewBox="0 0 920 260" preserveAspectRatio="none" class="trend-svg" aria-hidden="true">
              <defs>
                <linearGradient id="loadAreaGradient" x1="0%" x2="0%" y1="0%" y2="100%">
                  <stop offset="0%" stop-color="#7fb4ff" stop-opacity="0.22" />
                  <stop offset="65%" stop-color="#7fb4ff" stop-opacity="0.08" />
                  <stop offset="100%" stop-color="#7fb4ff" stop-opacity="0" />
                </linearGradient>
                <linearGradient id="loadStrokeGradient" x1="0%" x2="100%" y1="0%" y2="0%">
                  <stop offset="0%" stop-color="#8dc5ff" />
                  <stop offset="55%" stop-color="#5d97f7" />
                  <stop offset="100%" stop-color="#4d82dc" />
                </linearGradient>
              </defs>

              <g class="trend-grid">
                <line x1="0" y1="32" x2="920" y2="32" />
                <line x1="0" y1="98" x2="920" y2="98" />
                <line x1="0" y1="164" x2="920" y2="164" />
                <line x1="0" y1="230" x2="920" y2="230" />
              </g>

              <path :d="trendPath.area" fill="url(#loadAreaGradient)" />
              <path :d="trendPath.line" fill="none" stroke="url(#loadStrokeGradient)" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" />
              <path :d="trendPath.line" fill="none" stroke="#d9e7ff" stroke-opacity="0.62" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>

            <div class="trend-axis">
              <span v-for="label in trendAxisLabels" :key="label">{{ label || '--:--:--' }}</span>
            </div>
          </div>
        </section>

        <section class="glass-card focus-card">
          <div class="card-head card-head--split">
            <div>
              <span class="card-eyebrow">Key Device Live Panel</span>
              <span class="card-title">重点设备 · {{ focusDeviceName }}</span>
            </div>
            <div class="focus-status" :class="`focus-status--${focusStatusTone}`">
              <span class="focus-status__dot" />
              <span>{{ focusStatusLabel }}</span>
            </div>
          </div>

          <div class="focus-layout">
            <div class="focus-main">
              <div class="focus-identity">
                <span>{{ focusDeviceType }}</span>
                <span>{{ focusEnergyType }}</span>
                <span>{{ focusDevice?.location || '园区主供热回路' }}</span>
              </div>

              <div class="focus-story">
                <div class="focus-story__head">
                  <span>运行概览</span>
                  <small>{{ focusArchive?.location || resolveShiftLabel(currentTime) }}</small>
                </div>
                <div class="focus-story__stats">
                  <div
                    v-for="item in focusOverviewStats"
                    :key="item.label"
                    class="focus-story__stat"
                  >
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }}</strong>
                    <small>{{ item.caption }}</small>
                  </div>
                </div>
                <div class="focus-story__timeline">
                  <div class="focus-story__timeline-head">
                    <span>最近事件</span>
                    <small>{{ formatDateTime(String(focusRuntime?.last_success_at || focusRuntime?.latest_timestamp || '')) }}</small>
                  </div>
                  <div v-if="focusRecentEvents.length" class="focus-story__timeline-list">
                    <article
                      v-for="event in focusRecentEvents"
                      :key="`${event.timestamp}-${event.event_type}`"
                      class="focus-story__timeline-item"
                    >
                      <span class="focus-story__timeline-dot" />
                      <div>
                        <strong>{{ event.title }}</strong>
                        <small>{{ event.detail || '设备状态变化' }}</small>
                      </div>
                      <time>{{ formatDateTime(event.timestamp) }}</time>
                    </article>
                  </div>
                  <div v-else class="focus-story__timeline-empty">
                    当前暂无告警或启停事件，采集链路保持稳定。
                  </div>
                </div>
              </div>

              <div class="focus-hero">
                <div>
                  <small>{{ focusMeasurementLabel }}</small>
                  <strong>{{ formatNumber(displayPower) }}</strong>
                  <span>{{ focusMeasurementUnit }}</span>
                </div>
                <div class="focus-hero__side">
                  <small>数据状态</small>
                  <strong>{{ realtimeLoading.device ? '同步中' : (focusRuntime?.label || '实时联动') }}</strong>
                </div>
              </div>
            </div>

            <div class="focus-grid">
              <article
                v-for="item in focusTelemetryCards"
                :key="item.label"
                class="focus-grid__item"
              >
                <div class="focus-grid__head">
                  <span class="focus-grid__icon">{{ item.icon }}</span>
                  <div>
                    <span>{{ item.label }}</span>
                    <small>{{ item.helper }}</small>
                  </div>
                </div>
                <strong>{{ item.value }}</strong>

                <svg
                  v-if="item.spark"
                  :viewBox="`0 0 ${sparklineWidth} ${sparklineHeight}`"
                  class="focus-sparkline"
                  preserveAspectRatio="none"
                  aria-hidden="true"
                >
                  <path :d="item.spark.area" fill="rgba(107, 184, 255, 0.10)" />
                  <path :d="item.spark.line" fill="none" stroke="#73adff" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" />
                </svg>

                <div
                  v-else-if="typeof item.progress === 'number'"
                  class="focus-progress"
                >
                  <span class="focus-progress__track">
                    <span class="focus-progress__fill" :style="{ width: `${item.progress}%` }" />
                  </span>
                  <small>{{ item.progress.toFixed(0) }}%</small>
                </div>

                <div
                  v-else-if="typeof item.range === 'number'"
                  class="focus-range"
                >
                  <span class="focus-range__track">
                    <span class="focus-range__safe" />
                    <span class="focus-range__pointer" :style="{ left: `${item.range}%` }" />
                  </span>
                </div>

                <div
                  v-if="item.meta?.length"
                  class="focus-grid__meta"
                >
                  <div
                    v-for="meta in item.meta"
                    :key="`${item.label}-${meta.label}`"
                    class="focus-grid__meta-item"
                  >
                    <span>{{ meta.label }}</span>
                    <strong>{{ meta.value }}</strong>
                  </div>
                </div>

                <small class="focus-grid__footer">{{ item.footer }}</small>
              </article>
            </div>
          </div>
        </section>
      </section>

      <aside class="right-column">
        <section class="glass-card scada-card">
          <div class="card-head card-head--split">
            <div>
              <span class="card-eyebrow">SCADA Device Board</span>
              <span class="card-title">SCADA 设备导航</span>
            </div>
            <span class="scada-summary">{{ onlineDevices }}/{{ totalDevices }} 在线</span>
          </div>

          <div class="scada-list scrollbar-hidden">
            <details
              v-for="group in scadaDeviceGroups"
              :key="group.key"
              class="scada-group"
              :open="group.devices.some((device) => device.id === currentDeviceId)"
            >
              <summary class="scada-group__head">
                <div class="scada-group__title">
                  <span>{{ group.label }}</span>
                  <small>{{ group.devices.length }} 台设备</small>
                </div>
                <div class="scada-group__meta">
                  <small>{{ group.online }}/{{ group.devices.length }} 在线</small>
                  <span class="scada-group__caret" />
                </div>
              </summary>

              <div class="scada-group__body">
                <button
                  v-for="device in group.devices"
                  :key="device.id"
                  type="button"
                  class="scada-item"
                  :class="{ active: device.id === currentDeviceId, offline: !device.is_active }"
                  @click="selectDevice(device.id)"
                >
                  <span class="scada-item__dot" />
                  <div class="scada-item__copy">
                    <strong>{{ device.name }}</strong>
                    <span>{{ device.location || '未标注位置' }}</span>
                  </div>
                  <small>{{ energyNameMap[device.energy_type || ''] || device.energy_type || device.device_type }}</small>
                </button>
              </div>
            </details>
          </div>
        </section>

        <section class="glass-card ranking-card">
          <div class="card-head">
            <span class="card-eyebrow">Regional Ranking</span>
            <span class="card-title">各区域能耗排行 Top 5</span>
          </div>

          <div class="ranking-list">
            <article
              v-for="(item, index) in regionRankings"
              :key="item.name"
              class="ranking-row"
            >
              <span class="ranking-row__index">{{ index + 1 }}</span>
              <div class="ranking-row__copy">
                <strong>{{ item.name }}</strong>
                <span>{{ item.online }}/{{ item.total }} 台在线</span>
              </div>
              <strong class="ranking-row__value">{{ formatNumber(item.score) }} kW</strong>
            </article>

            <div v-if="regionRankings.length === 0" class="card-empty">
              暂无区域排行数据
            </div>
          </div>
        </section>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.ems-cockpit {
  position: relative;
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 18px;
  overflow: hidden;
  color: #f5f7fa;
  background:
    radial-gradient(circle at top left, rgba(107, 184, 255, 0.08), transparent 24%),
    radial-gradient(circle at top right, rgba(91, 192, 255, 0.06), transparent 22%),
    #0a0a0a;
  box-sizing: border-box;
}

.ems-cockpit::before,
.ems-cockpit::after {
  display: none;
}

.cockpit-noise {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.015), transparent 24%, transparent 76%, rgba(255, 255, 255, 0.015));
  opacity: 0.28;
}

.top-header,
.glass-card {
  position: relative;
  z-index: 1;
}

.top-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: 14px;
  min-height: 108px;
  padding: 10px 16px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.045);
  backdrop-filter: blur(20px) saturate(135%);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.06),
    0 16px 38px rgba(0, 0, 0, 0.2);
  overflow: visible;
}

.top-header::before {
  display: none;
}

.top-header__main,
.top-header__panel {
  position: relative;
  z-index: 1;
}

.top-header__main {
  display: grid;
  grid-template-rows: auto auto;
  align-content: start;
  gap: 6px;
  min-height: 0;
  min-width: 0;
}

.top-header__panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  min-height: 0;
}

.brand-block {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
  min-height: 0;
}

.brand-block > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: rgba(107, 184, 255, 0.12);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.brand-mark__dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #6bb8ff;
  box-shadow: none;
}

.brand-kicker {
  margin: 0 0 2px;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.56);
}

.brand-block h1 {
  margin: 0;
  font-size: clamp(18px, 1.65vw, 23px);
  font-weight: 650;
  line-height: 1;
  letter-spacing: -0.04em;
}

.brand-subtitle {
  margin: 0;
  max-width: 520px;
  font-size: 10px;
  line-height: 1.15;
  color: rgba(255, 255, 255, 0.62);
}

.header-highlights {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  align-self: start;
}

.header-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  min-width: 0;
}

.header-highlights__item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-height: 42px;
  padding: 6px 9px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  justify-content: center;
}

.header-highlights__item span {
  font-size: 9px;
  letter-spacing: 0.04em;
  color: rgba(255, 255, 255, 0.42);
}

.header-highlights__item strong {
  font-size: clamp(11px, 0.92vw, 14px);
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: #f5f8ff;
}

.header-highlights__item--load {
  justify-content: center;
}

.header-load {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.header-load strong {
  font-size: clamp(20px, 1.55vw, 26px);
  line-height: 0.96;
  letter-spacing: -0.06em;
  color: #e7f2ff;
}

.header-load small {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.56);
}

.header-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: space-between;
  gap: 6px;
}

.time-panel {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.time-panel__date {
  font-size: 9px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.54);
}

.time-panel strong {
  font-size: clamp(15px, 1.35vw, 20px);
  line-height: 1;
  letter-spacing: -0.03em;
}

.run-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(0, 224, 176, 0.12);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
  color: #d9fff5;
  font-size: 11px;
  font-weight: 600;
}

.run-badge__dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #00e0b0;
  box-shadow: 0 0 14px rgba(0, 224, 176, 0.5);
}

.run-badge--offline {
  background: rgba(255, 140, 140, 0.12);
  color: #ffe2e2;
}

.run-badge--offline .run-badge__dot {
  background: #ff7b9c;
  box-shadow: 0 0 14px rgba(255, 123, 156, 0.5);
}

.bento-layout {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(216px, 0.86fr) minmax(0, 1.72fr) minmax(210px, 0.8fr);
  gap: 14px;
}

.left-column,
.center-column,
.right-column {
  min-height: 0;
}

.left-column {
  grid-column: auto;
  display: grid;
  grid-template-rows: auto auto auto;
  gap: 14px;
}

.center-column {
  grid-column: auto;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 14px;
}

.right-column {
  grid-column: auto;
  display: grid;
  grid-template-rows: minmax(0, 0.88fr) auto;
  gap: 12px;
}

.glass-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 14px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(18px) saturate(145%);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.06),
    0 14px 30px rgba(0, 0, 0, 0.18);
  overflow: hidden;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

.glass-card::before {
  display: none;
}

.glass-card:hover {
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.08),
    0 16px 32px rgba(0, 0, 0, 0.2);
}

.card-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.card-head--split {
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-eyebrow {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: rgba(255, 255, 255, 0.42);
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.03em;
}

.overview-compact {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: stretch;
}

.overview-card {
  justify-content: flex-start;
}

.overview-card .card-head {
  margin-bottom: 4px;
}

.overview-rate {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 96px;
  padding: 10px 12px 8px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.045);
}

.overview-rate__label {
  font-size: 10px;
  letter-spacing: 0.04em;
  color: rgba(255, 255, 255, 0.5);
}

.overview-rate strong {
  display: block;
  font-size: clamp(34px, 3.3vw, 46px);
  line-height: 0.92;
  letter-spacing: -0.07em;
  color: #78bcff;
}

.overview-rate__hint {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px 10px;
  max-width: 100%;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.46);
}

.overview-split {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.overview-stat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.overview-stat__label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.overview-stat__label span {
  font-size: 11px;
  line-height: 1.1;
  color: rgba(255, 255, 255, 0.82);
}

.overview-stat__label small {
  font-size: 9px;
  line-height: 1;
  color: rgba(255, 255, 255, 0.48);
}

.overview-stat__value {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  flex: 0 0 auto;
}

.overview-stat__value strong {
  font-size: 18px;
  line-height: 1;
  letter-spacing: -0.04em;
  color: #eef5ff;
}

.overview-stat__value small {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.48);
}

.energy-card {
  min-height: 0;
  padding: 11px 11px 10px;
}

.energy-card .card-head {
  gap: 3px;
  margin-bottom: 6px;
}

.energy-card .card-title {
  font-size: 14px;
}

.energy-mix {
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
  align-items: stretch;
  min-height: 0;
  flex: 1 1 auto;
}

.energy-ring {
  position: relative;
  width: 140px;
  height: 140px;
  min-width: 140px;
  min-height: 140px;
  max-width: 140px;
  max-height: 140px;
  margin: 0 auto;
  flex: 0 0 140px;
  border-radius: 999px;
  padding: 6px;
  box-sizing: border-box;
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.06),
    0 6px 14px rgba(0, 0, 0, 0.08);
}

.energy-ring::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  opacity: 0.28;
}

.energy-ring--dense::before {
  inset: -4px;
  border-color: rgba(255, 255, 255, 0.06);
}

.energy-ring::after {
  content: '';
  position: absolute;
  inset: 24%;
  border-radius: 999px;
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.045), transparent 54%),
    rgba(10, 10, 10, 0.94);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.06),
    inset 0 8px 18px rgba(255, 255, 255, 0.02);
}

.energy-ring__halo {
  position: absolute;
  inset: 4px;
  border-radius: 999px;
  box-shadow:
    inset 0 0 0 4px rgba(255, 255, 255, 0.012),
    inset 0 0 8px rgba(255, 255, 255, 0.018);
  pointer-events: none;
}

.energy-ring__core {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.energy-ring__core span,
.energy-ring__core small {
  color: rgba(255, 255, 255, 0.5);
}

.energy-ring__core strong {
  font-size: 18px;
  color: #f8fffd;
  letter-spacing: -0.05em;
}

.energy-ring__core span,
.energy-ring__core small {
  font-size: 9px;
}

.energy-legend {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-height: 0;
}

.energy-legend--grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}

.energy-legend__item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: 66px;
  padding: 7px 8px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.045);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.055);
}

.energy-legend__topline {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 12px;
}

.energy-legend__swatch {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  flex: 0 0 auto;
}

.energy-legend__name {
  font-size: 9px;
  line-height: 1;
  color: rgba(255, 255, 255, 0.78);
}

.energy-legend__main {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-between;
  gap: 3px;
  min-height: 0;
}

.energy-legend__main strong {
  font-size: 19px;
  line-height: 0.95;
  letter-spacing: -0.04em;
  color: #6bb8ff;
}

.energy-legend__value {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  color: rgba(255, 255, 255, 0.58);
}

.energy-legend__value span {
  font-size: 11px;
  line-height: 1;
  color: rgba(255, 255, 255, 0.72);
}

.energy-legend__value small {
  font-size: 8px;
  color: rgba(255, 255, 255, 0.46);
}

.energy-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  margin-top: 0;
}

.energy-summary__item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
  padding: 8px 9px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.06),
    inset 0 -12px 18px rgba(255, 255, 255, 0.012);
}

.energy-summary__item span {
  font-size: 9px;
  line-height: 1.1;
  color: rgba(255, 255, 255, 0.42);
}

.energy-summary__main {
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
}

.energy-summary__main strong {
  font-size: 16px;
  line-height: 1;
  letter-spacing: -0.04em;
  color: #eef5ff;
}

.energy-summary__main small {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.48);
}

.alarm-card {
  min-height: 0;
}

.alarm-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.alarm-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 10px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.alarm-row__pulse {
  width: 10px;
  height: 10px;
  margin-top: 7px;
  border-radius: 999px;
  background: #ff7b9c;
  box-shadow: 0 0 12px rgba(255, 123, 156, 0.48);
}

.alarm-row__copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.alarm-row__copy strong {
  font-size: 12px;
  line-height: 1.4;
}

.alarm-row__copy span {
  color: rgba(255, 255, 255, 0.46);
  font-size: 10px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.metric-card {
  gap: 8px;
  justify-content: center;
  min-height: 78px;
}

.metric-card__label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.44);
  letter-spacing: 0.05em;
}

.metric-card__value {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.metric-card__value strong {
  font-size: clamp(22px, 1.7vw, 30px);
  line-height: 1;
  letter-spacing: -0.06em;
  color: #6bb8ff;
}

.metric-card__value small {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.56);
}

.metric-card__caption {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.46);
}

.trend-card {
  min-height: 0;
}

.trend-head {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.trend-stat-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  width: 100%;
  max-width: 396px;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.035);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.trend-stat-pill {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 7px 9px;
  min-height: 54px;
  justify-content: center;
  background: transparent;
}

.trend-stat-pill + .trend-stat-pill {
  border-left: 1px solid rgba(255, 255, 255, 0.06);
}

.trend-stat-pill span {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.44);
}

.trend-stat-pill strong {
  font-size: 13px;
  letter-spacing: -0.03em;
}

.trend-canvas {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.trend-svg {
  width: 100%;
  height: 100%;
  min-height: 148px;
}

.trend-grid line {
  stroke: rgba(255, 255, 255, 0.06);
  stroke-width: 1;
}

.trend-axis {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin-top: 8px;
}

.trend-axis span {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.36);
}

.trend-axis span:nth-child(2),
.trend-axis span:nth-child(3),
.trend-axis span:nth-child(4) {
  text-align: center;
}

.trend-axis span:last-child {
  text-align: right;
}

.focus-card {
  min-height: 0;
}

.focus-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
  font-size: 11px;
}

.focus-status__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #6bb8ff;
  box-shadow: 0 0 10px rgba(107, 184, 255, 0.45);
}

.focus-status--alarm .focus-status__dot {
  background: #ffb86b;
  box-shadow: 0 0 10px rgba(255, 184, 107, 0.35);
}

.focus-status--offline .focus-status__dot {
  background: #9aa4b2;
  box-shadow: none;
}

.focus-layout {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: auto auto;
  gap: 12px;
  align-items: stretch;
}

.focus-main,
.focus-grid {
  min-height: 0;
}

.focus-main {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 10px;
}

.focus-story {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.focus-story__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.focus-story__head span {
  font-size: 12px;
  font-weight: 600;
}

.focus-story__head small,
.focus-story__timeline-head small,
.focus-story__timeline-item small,
.focus-story__timeline-item time,
.focus-story__timeline-empty {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
}

.focus-story__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.focus-story__stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
}

.focus-story__stat span {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.42);
}

.focus-story__stat strong {
  font-size: 15px;
  color: #dbe8ff;
}

.focus-story__stat small {
  font-size: 10px;
  line-height: 1.35;
  color: rgba(255, 255, 255, 0.46);
}

.focus-story__timeline {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.focus-story__timeline-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.focus-story__timeline-head span {
  font-size: 12px;
  font-weight: 600;
}

.focus-story__timeline-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.focus-story__timeline-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.focus-story__timeline-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #6bb8ff;
}

.focus-story__timeline-item div {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.focus-story__timeline-item strong {
  font-size: 12px;
}

.focus-story__timeline-item time {
  white-space: nowrap;
}

.focus-story__timeline-empty {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.focus-identity {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.focus-identity span {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.74);
  font-size: 11px;
}

.focus-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: end;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.05);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
}

.focus-hero small,
.focus-hero__side small {
  display: block;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.48);
}

.focus-hero strong {
  font-size: clamp(30px, 2.4vw, 38px);
  line-height: 1;
  letter-spacing: -0.06em;
  color: #6bb8ff;
}

.focus-hero span {
  margin-left: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.focus-hero__side {
  text-align: right;
}

.focus-hero__side strong {
  display: block;
  margin-top: 6px;
  font-size: 16px;
  color: #f3fffb;
}

.focus-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  align-content: start;
  grid-auto-rows: minmax(132px, auto);
}

.focus-grid__item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: flex-start;
  padding: 12px 12px 10px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.focus-grid__head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.focus-grid__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  background: rgba(107, 184, 255, 0.12);
  color: #8fc7ff;
  font-size: 11px;
}

.focus-grid__head div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.focus-grid__head span,
.focus-grid__head small {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.44);
}

.focus-grid__head small {
  font-size: 10px;
}

.focus-grid__item strong {
  font-size: 19px;
  letter-spacing: -0.04em;
}

.focus-sparkline {
  width: 100%;
  height: 30px;
}

.focus-progress,
.focus-range {
  display: flex;
  align-items: center;
  gap: 10px;
}

.focus-progress__track,
.focus-range__track {
  position: relative;
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.focus-progress__fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: 999px;
  background: linear-gradient(90deg, #6bb8ff, #98d1ff);
}

.focus-range__safe {
  position: absolute;
  inset: 0 18% 0 18%;
  border-radius: 999px;
  background: rgba(107, 184, 255, 0.28);
}

.focus-range__pointer {
  position: absolute;
  top: 50%;
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #dcecff;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 0 2px rgba(107, 184, 255, 0.2);
}

.focus-progress small,
.focus-grid__footer {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.46);
}

.focus-grid__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}

.focus-grid__meta-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 6px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.035);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
}

.focus-grid__meta-item span {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.4);
}

.focus-grid__meta-item strong {
  font-size: 11px;
  line-height: 1.2;
  letter-spacing: -0.02em;
  color: #e3efff;
}

.scada-summary {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.07);
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
}

.scada-list {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scada-group {
  display: flex;
  flex-direction: column;
  gap: 0;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.025);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  overflow: hidden;
}

.scada-group__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  list-style: none;
}

.scada-group__head::-webkit-details-marker {
  display: none;
}

.scada-group__title,
.scada-group__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.scada-group__head span {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.84);
}

.scada-group__head small {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.42);
}

.scada-group__caret {
  width: 8px;
  height: 8px;
  border-right: 1.5px solid rgba(255, 255, 255, 0.46);
  border-bottom: 1.5px solid rgba(255, 255, 255, 0.46);
  transform: rotate(45deg);
  transition: transform 0.18s ease;
}

.scada-group[open] .scada-group__caret {
  transform: rotate(225deg);
}

.scada-group__body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 8px 8px;
}

.scada-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 0;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

.scada-item:hover {
  background: rgba(255, 255, 255, 0.065);
}

.scada-item.active {
  background: rgba(107, 184, 255, 0.07);
  box-shadow:
    inset 0 0 0 1px rgba(107, 184, 255, 0.12),
    0 8px 18px rgba(0, 0, 0, 0.12);
}

.scada-item__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #6bb8ff;
  box-shadow: 0 0 10px rgba(107, 184, 255, 0.4);
}

.scada-item.offline .scada-item__dot {
  background: #9aa4b2;
  box-shadow: none;
}

.scada-item__copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.scada-item__copy strong {
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.scada-item__copy span,
.scada-item small {
  color: rgba(255, 255, 255, 0.46);
  font-size: 10px;
}

.scada-item small {
  justify-self: end;
  white-space: nowrap;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.ranking-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.ranking-row__index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: #6bb8ff;
  font-size: 11px;
  font-weight: 700;
}

.ranking-row__copy {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.ranking-row__copy strong {
  font-size: 12px;
}

.ranking-row__copy span {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.46);
}

.ranking-row__value {
  font-size: 14px;
  letter-spacing: -0.04em;
  color: #6bb8ff;
}

.card-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  padding: 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
}

.card-empty--success {
  color: rgba(214, 255, 241, 0.72);
}

.scrollbar-hidden {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.scrollbar-hidden::-webkit-scrollbar {
  width: 0;
  height: 0;
}

@media (max-width: 1600px) {
  .top-header {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .header-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .trend-stat-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    max-width: 280px;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1536px) and (min-width: 1281px) {
  .ems-cockpit {
    gap: 14px;
    padding: 14px;
  }

  .top-header {
    min-height: 132px;
    padding: 16px 18px;
  }

  .bento-layout {
    grid-template-columns: minmax(196px, 0.8fr) minmax(0, 1.78fr) minmax(192px, 0.76fr);
    gap: 14px;
  }

  .left-column,
  .center-column,
  .right-column {
    gap: 14px;
  }

  .glass-card {
    padding: 14px;
    border-radius: 18px;
  }

  .trend-svg {
    min-height: 136px;
  }

  .right-column {
    grid-template-rows: minmax(0, 0.82fr) auto;
  }

  .focus-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-rows: minmax(118px, auto);
  }
}

@media (max-width: 1440px) and (min-width: 1281px), (max-height: 820px) and (min-width: 1281px) {
  .ems-cockpit {
    gap: 12px;
    padding: 12px;
  }

  .top-header {
    min-height: 92px;
    padding: 8px 12px;
  }

  .top-header__panel {
    grid-template-columns: auto auto;
    justify-content: end;
  }

  .header-highlights {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .header-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .header-highlights__item {
    min-height: 0;
    padding: 5px 8px;
  }

  .bento-layout {
    grid-template-columns: minmax(182px, 0.74fr) minmax(0, 1.94fr) minmax(182px, 0.72fr);
    gap: 12px;
  }

  .left-column,
  .center-column,
  .right-column {
    gap: 12px;
  }

  .glass-card {
    padding: 12px;
    border-radius: 16px;
  }

  .metric-card {
    min-height: 74px;
  }

  .trend-svg {
    min-height: 118px;
  }

  .focus-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
    gap: 10px;
  }

  .focus-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-rows: minmax(112px, auto);
  }

  .scada-group__head {
    padding: 8px 10px;
  }

  .scada-group__body {
    padding: 0 6px 6px;
  }

  .scada-item {
    padding: 7px 8px;
    grid-template-columns: auto minmax(0, 1fr);
  }

  .scada-item small {
    display: none;
  }
}

@media (max-width: 1280px) {
  .ems-cockpit {
    min-height: auto;
  }

  .bento-layout {
    grid-template-columns: 1fr;
  }

  .left-column,
  .center-column,
  .right-column {
    grid-column: span 1;
  }

  .left-column,
  .center-column,
  .right-column {
    grid-template-rows: none;
  }

  .focus-layout,
  .energy-mix {
    grid-template-columns: 1fr;
  }

  .energy-legend--grid {
    grid-template-columns: 1fr;
  }

  .focus-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-rows: minmax(104px, auto);
  }

  .header-highlights {
    grid-template-columns: 1fr;
  }

  .header-strip {
    grid-template-columns: 1fr;
  }

  .top-header__panel {
    grid-template-columns: 1fr;
  }

  .header-meta {
    align-items: flex-start;
  }
}

@media (max-width: 768px) {
  .ems-cockpit {
    padding: 16px;
    gap: 16px;
  }

  .top-header {
    padding: 20px;
  }

  .header-meta {
    width: 100%;
    justify-content: flex-start;
  }

  .brand-block {
    align-items: flex-start;
  }

  .brand-mark {
    width: 40px;
    height: 40px;
  }

  .overview-split,
  .metric-grid,
  .header-highlights,
  .focus-story__stats,
  .trend-stat-row {
    grid-template-columns: 1fr;
  }

  .focus-grid {
    grid-template-columns: 1fr;
    grid-auto-rows: minmax(96px, auto);
  }

  .card-head--split {
    flex-direction: column;
  }

  .focus-hero {
    grid-template-columns: 1fr;
  }

  .focus-hero__side {
    text-align: left;
  }
}
</style>
