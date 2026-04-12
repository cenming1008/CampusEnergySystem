import type { DeviceTypeConfig } from '@/api/device'

export const DEVICE_TYPE_LABELS: Record<string, string> = {
  load: '用电设备',
  solar: '光伏发电',
  wind: '风力发电',
  storage: '储能设备',
  charger: '充电桩',
  water_meter: '水表',
  gas_meter: '燃气表',
  heat_meter: '热量表',
  cooling_meter: '冷量表',
  steam_meter: '蒸汽表',
  reactive_power_compensator: '无功功率补偿器',
  svg: '静止无功发生器',
}

export function buildDeviceTypeLabelMap(deviceTypes: DeviceTypeConfig[]) {
  const map = { ...DEVICE_TYPE_LABELS }
  for (const item of deviceTypes) {
    map[item.device_type] = item.name_zh
  }
  return map
}

export function getDeviceTypeLabel(deviceType?: string | null) {
  if (!deviceType) return ''
  return DEVICE_TYPE_LABELS[deviceType] || deviceType
}
