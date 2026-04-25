import { computed, type ComputedRef, type Ref } from 'vue'
import type { Alarm } from '@/api/alarm'
import type { Device } from '@/api/device'
import type { EnergyStatistics } from '@/api/energy'

type StatTone = 'cyan' | 'green' | 'blue' | 'red' | 'purple'
type AlarmTone = 'critical' | 'warning' | 'notice'
type DeviceOption = Device & { id: number }

interface DashboardRealtimeSnapshot {
  voltage: number
}

interface DashboardAlarmItem {
  id: number
  message: string
  deviceName: string
  time: string
  label: string
  tone: AlarmTone
  action: string
}

function resolveAlarmLevel(message: string): Pick<DashboardAlarmItem, 'label' | 'tone' | 'action'> {
  if (/中断|离线|断开|故障/.test(message)) {
    return { label: '严重', tone: 'critical', action: '立即排查通讯与设备状态' }
  }

  if (/异常|超限|过高|偏高|偏低/.test(message)) {
    return { label: '重要', tone: 'warning', action: '检查负荷阈值与现场参数' }
  }

  return { label: '提醒', tone: 'notice', action: '建议关注后续趋势变化' }
}

function formatAlarmTime(timestamp: string) {
  const diffMinutes = Math.max(0, Math.round((Date.now() - new Date(timestamp).getTime()) / 60000))
  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes} 分钟前`

  const diffHours = Math.round(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours} 小时前`
  return new Date(timestamp).toLocaleString('zh-CN', { hour12: false })
}

function resolveShiftLabel(currentTime: string) {
  const hour = Number(currentTime.split(':')[0] || Number.NaN)
  if (!Number.isFinite(hour)) return '白天时段'
  if (hour >= 8 && hour < 18) return '白天时段'
  if (hour >= 18 && hour < 23) return '晚间时段'
  return '夜间时段'
}

export function useDashboardViewModel(options: {
  currentTime: Ref<string>
  locationScope: ComputedRef<string | undefined>
  isConnected: Ref<boolean>
  currentDevice: ComputedRef<Device | undefined>
  currentDeviceId: Ref<number | undefined>
  deviceList: Ref<Device[]>
  selectableDevices: ComputedRef<DeviceOption[]>
  totalDevices: ComputedRef<number>
  onlineDevices: ComputedRef<number>
  alarmCount: Ref<number>
  alarmList: Ref<Alarm[]>
  energyStats: Record<string, EnergyStatistics>
  todayEnergy: ComputedRef<number>
  monthlyEnergy: ComputedRef<number>
  displayPower: ComputedRef<number>
  displayCurrent: ComputedRef<number>
  displayEnergy: ComputedRef<number>
  energyTrendData: { times: string[]; values: number[] }
  realTimeData: DashboardRealtimeSnapshot
}) {
  const overview = computed(() => ({
    totalDevices: options.totalDevices.value,
    onlineDevices: options.onlineDevices.value
  }))

  const regionRankings = computed(() => {
    const regions = new Map<string, { score: number; total: number; online: number }>()

    for (const device of options.deviceList.value) {
      const region = device.location?.trim() || '未分区'
      const current = regions.get(region) || { score: 0, total: 0, online: 0 }
      const capacity = Number(device.rated_capacity || 0)

      current.total += 1
      if (device.is_active) current.online += 1
      current.score += capacity > 0 ? capacity : (device.is_active ? 1.2 : 0.6)
      regions.set(region, current)
    }

    return Array.from(regions.entries())
      .map(([name, stats], index) => ({
        name,
        rank: index + 1,
        score: stats.score,
        total: stats.total,
        online: stats.online,
        hasCapacity: stats.score >= stats.total
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 5)
      .map((item, index) => ({ ...item, rank: index + 1 }))
  })

  const onlineRate = computed(() => {
    if (options.totalDevices.value === 0) return 0
    return Math.round((options.onlineDevices.value / options.totalDevices.value) * 100)
  })
  const offlineDevices = computed(() => Math.max(0, options.totalDevices.value - options.onlineDevices.value))

  const overviewCards = computed(() => [
    {
      label: '园区设备',
      value: overview.value.totalDevices,
      caption: '已接入设备与表计',
      tone: 'cyan' as StatTone
    },
    {
      label: '启用率',
      value: `${onlineRate.value}%`,
      caption: `${overview.value.onlineDevices} 台启用`,
      tone: 'green' as StatTone
    },
    {
      label: '覆盖区域',
      value: regionRankings.value.length,
      caption: regionRankings.value.length ? '已形成区域能耗视图' : '待补充区域映射',
      tone: 'blue' as StatTone
    },
    {
      label: '停用设备',
      value: offlineDevices.value,
      caption: offlineDevices.value ? '部分设备已停用' : '当前设备全部启用',
      tone: (offlineDevices.value ? 'red' : 'green') as StatTone
    }
  ])

  const trendValues = computed(() => options.energyTrendData.values.map((value) => Math.abs(Number(value) || 0)))
  const peakLoad = computed(() => (trendValues.value.length ? Math.max(...trendValues.value) : 0))
  const valleyLoad = computed(() => (trendValues.value.length ? Math.min(...trendValues.value) : 0))
  const warningThreshold = computed(() => {
    const base = Math.max(peakLoad.value, Math.abs(options.displayPower.value))
    return Number((base > 0 ? base * 0.9 : 1).toFixed(1))
  })
  const trendCurrentValue = computed(() => trendValues.value.at(-1) || 0)

  const hasEnergyDistributionData = computed(() => [
    options.energyStats.electricity?.total_consumption || 0,
    options.energyStats.water?.total_consumption || 0,
    options.energyStats.gas?.total_consumption || 0,
    options.energyStats.heat?.total_consumption || 0,
    options.energyStats.cooling?.total_consumption || 0,
  ].some((value) => value > 0))

  const shiftLabel = computed(() => resolveShiftLabel(options.currentTime.value))
  const runtimeTone = computed(() => (options.isConnected.value ? 'green' : 'red') as Exclude<StatTone, 'cyan' | 'purple'>)
  const dashboardScopeHint = computed(() => {
    if (!options.locationScope.value) {
      return '当前驾驶舱展示的是当前账号可访问的全部园区设备与能耗汇总。'
    }
    return `当前驾驶舱已按位置范围 ${options.locationScope.value} 过滤，统计结果不代表全部园区全量数据。`
  })

  const selectedDeviceSummary = computed(() => ({
    name: options.currentDevice.value?.name || '暂无设备',
    type: options.currentDevice.value?.device_type || '未选择',
    energyType: options.currentDevice.value?.energy_type || '未知',
    status: options.currentDevice.value?.is_active ? '启用' : '停用'
  }))

  const selectedDeviceLabel = computed(() => {
    if (!options.currentDevice.value) return '未选择设备'
    const location = options.currentDevice.value.location?.trim()
    return location ? `${options.currentDevice.value.name} · ${location}` : options.currentDevice.value.name
  })

  const selectableDeviceCount = computed(() => options.selectableDevices.value.length)
  const selectedDeviceStatusTone = computed(() => (options.currentDevice.value?.is_active ? 'online' : 'offline'))
  const focusMetrics = computed(() => [
    { label: '实时功率', value: `${options.displayPower.value.toFixed(1)} kW` },
    { label: '母线电压', value: `${options.realTimeData.voltage.toFixed(1)} V` },
    { label: 'A相电流', value: `${options.displayCurrent.value.toFixed(1)} A` },
    { label: '今日用电', value: `${options.displayEnergy.value.toFixed(1)} kWh` }
  ])

  const trendHighlights = computed(() => [
    { label: '当前值', value: `${trendCurrentValue.value.toFixed(1)} kW` },
    { label: '峰值', value: `${peakLoad.value.toFixed(1)} kW` },
    { label: '谷值', value: `${valleyLoad.value.toFixed(1)} kW` },
    { label: '阈值', value: `${warningThreshold.value.toFixed(1)} kW` }
  ])

  const latestAlarmItems = computed<DashboardAlarmItem[]>(() => (
    options.alarmList.value.slice(0, 4).map((alarm) => {
      const level = resolveAlarmLevel(alarm.message)
      const deviceName = options.deviceList.value.find((device) => device.id === alarm.device_id)?.name || `设备 ${alarm.device_id}`

      return {
        id: alarm.id,
        message: alarm.message,
        deviceName,
        time: formatAlarmTime(alarm.timestamp),
        ...level
      }
    })
  ))

  const selectedDeviceAlarmItems = computed<DashboardAlarmItem[]>(() => {
    if (!options.currentDevice.value?.id) return latestAlarmItems.value.slice(0, 3)

    return options.alarmList.value
      .filter((alarm) => alarm.device_id === options.currentDevice.value?.id)
      .slice(0, 3)
      .map((alarm) => {
        const level = resolveAlarmLevel(alarm.message)
        return {
          id: alarm.id,
          message: alarm.message,
          deviceName: options.currentDevice.value?.name || `设备 ${alarm.device_id}`,
          time: formatAlarmTime(alarm.timestamp),
          ...level
        }
      })
  })

  const scadaStatusCards = computed(() => [
    {
      label: '今日总能耗',
      value: `${options.todayEnergy.value.toFixed(1)} kWh`,
      meta: '覆盖电/水/气/冷/热',
      tone: 'cyan' as StatTone
    },
    {
      label: '本月总能耗',
      value: `${options.monthlyEnergy.value.toFixed(1)} kWh`,
      meta: '按自然月累计',
      tone: 'purple' as StatTone
    },
    {
      label: '实时负荷',
      value: `${options.displayPower.value.toFixed(1)} kW`,
      meta: `峰谷 ${peakLoad.value.toFixed(1)} / ${valleyLoad.value.toFixed(1)} kW`,
      tone: 'blue' as StatTone
    },
    {
      label: '当前监测',
      value: options.currentDevice.value?.name || '未选择设备',
      meta: selectedDeviceSummary.value.status,
      tone: 'green' as StatTone
    },
    {
      label: '通讯状态',
      value: options.isConnected.value ? '正常' : '中断',
      meta: `当前时段 ${shiftLabel.value}`,
      tone: runtimeTone.value
    }
  ])

  const selectedDeviceProfile = computed(() => [
    { label: '设备类型', value: selectedDeviceSummary.value.type },
    { label: '能源介质', value: selectedDeviceSummary.value.energyType },
    { label: '运行状态', value: selectedDeviceSummary.value.status },
    { label: '预警阈值', value: `${warningThreshold.value.toFixed(1)} kW` }
  ])

  const deviceBoardItems = computed(() => options.selectableDevices.value.slice(0, 12))

  const selectDevice = (deviceId?: number) => {
    if (typeof deviceId !== 'number' || deviceId === options.currentDeviceId.value) return
    options.currentDeviceId.value = deviceId
  }

  return {
    dashboardScopeHint,
    deviceBoardItems,
    focusMetrics,
    hasEnergyDistributionData,
    latestAlarmItems,
    offlineDevices,
    onlineRate,
    overviewCards,
    regionRankings,
    scadaStatusCards,
    selectableDeviceCount,
    selectDevice,
    selectedDeviceAlarmItems,
    selectedDeviceLabel,
    selectedDeviceProfile,
    selectedDeviceStatusTone,
    selectedDeviceSummary,
    shiftLabel,
    trendHighlights,
    warningThreshold
  }
}
