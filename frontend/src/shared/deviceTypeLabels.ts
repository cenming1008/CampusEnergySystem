import type { Device, DeviceTypeConfig } from '@/api/device'

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
  svg: 'SVG',
  capacitor_bank_controller: '电容补偿控制器',
}

export const DEVICE_CATEGORY_LABELS: Record<string, string> = {
  load: '用电设备',
  compensation: '无功功率补偿设备',
  solar: '光伏发电',
  wind: '风力发电',
  storage: '储能设备',
  charger: '充电桩',
  water_meter: '水表',
  gas_meter: '燃气表',
  heat_meter: '热量表',
  cooling_meter: '冷量表',
}

export const ENERGY_TYPE_LABELS: Record<string, string> = {
  electricity: '电力',
  water: '水务',
  gas: '燃气',
  heat: '热力',
  cooling: '冷量',
  steam: '蒸汽',
}

export function buildDeviceTypeLabelMap(deviceTypes: DeviceTypeConfig[]) {
  const map = { ...DEVICE_TYPE_LABELS }
  for (const item of deviceTypes) {
    map[item.device_type] = item.name_zh
  }
  return map
}

export function getDeviceTypeLabel(deviceType?: string | null, deviceTypes: DeviceTypeConfig[] = []) {
  if (!deviceType) return ''

  const matched = deviceTypes.find((item) => item.device_type === deviceType)
  if (matched?.name_zh) return matched.name_zh

  return DEVICE_TYPE_LABELS[deviceType] || deviceType
}

export function getDeviceSubtypeLabel(deviceType?: string | null, deviceTypes: DeviceTypeConfig[] = []) {
  if (!deviceType) return ''

  const matched = deviceTypes.find((item) => item.device_type === deviceType)
  if (matched?.subtype_name_zh) return matched.subtype_name_zh
  if (matched?.name_zh) return matched.name_zh

  return DEVICE_TYPE_LABELS[deviceType] || deviceType
}

export function getDeviceCategoryLabel(category?: string | null, deviceTypes: DeviceTypeConfig[] = []) {
  if (!category) return ''

  const exactType = deviceTypes.find((item) => item.device_type === category)
  if (exactType?.name_zh) return exactType.name_zh

  const matchedCategory = deviceTypes.find((item) => item.category === category)
  if (matchedCategory?.device_type) {
    return DEVICE_CATEGORY_LABELS[category] || getDeviceTypeLabel(matchedCategory.device_type, deviceTypes)
  }

  return DEVICE_CATEGORY_LABELS[category] || getDeviceTypeLabel(category, deviceTypes) || category
}

export function getEnergyTypeLabel(energyType?: string | null) {
  if (!energyType) return ''
  return ENERGY_TYPE_LABELS[energyType] || energyType
}

export interface DeviceGroupMeta {
  key: string
  label: string
  source: 'device_category' | 'energy_type' | 'device_type' | 'fallback'
}

export function resolveDeviceGroupMeta(device: Pick<Device, 'device_category' | 'energy_type' | 'device_type'>, deviceTypes: DeviceTypeConfig[] = []): DeviceGroupMeta {
  const categoryKey = device.device_category?.trim()
  if (categoryKey) {
    return {
      key: categoryKey,
      label: getDeviceCategoryLabel(categoryKey, deviceTypes) || categoryKey,
      source: 'device_category',
    }
  }

  const energyKey = device.energy_type?.trim()
  if (energyKey) {
    return {
      key: energyKey,
      label: getEnergyTypeLabel(energyKey) || energyKey,
      source: 'energy_type',
    }
  }

  const typeKey = device.device_type?.trim()
  if (typeKey) {
    return {
      key: typeKey,
      label: getDeviceTypeLabel(typeKey, deviceTypes) || typeKey,
      source: 'device_type',
    }
  }

  return {
    key: 'uncategorized',
    label: '未分类设备',
    source: 'fallback',
  }
}
