import request from '@/utils/request'
import type { SuccessResponse } from '@/types/api'
import type { CompensationSvgOperationsProfile } from '@/api/compensation'
import { normalizeCompensationDevice } from '@/shared/compensationDevices'

// 对应后端 Device 模型
export interface Device {
  id?: number
  name: string
  sn: string
  device_type: string
  device_subtype?: string
  device_category?: string
  energy_type?: string
  archive_status?: 'pending' | 'complete'
  unit?: string
  rated_capacity?: number
  location_id?: number
  location?: string
  is_active: boolean
  description?: string
  created_at?: string
  updated_at?: string
}

export interface DeviceWritePayload extends Partial<Device> {
  svg_operations?: Partial<CompensationSvgOperationsProfile>
}

// 设备类型配置（来自后端注册表）
export interface DeviceTypeConfig {
  device_type: string
  category: string
  energy_type: string
  name_zh: string
  name_en: string
  subtype_name_zh?: string
  subtype_name_en?: string
  unit: string
  default_capacity: number
  required_fields: string[]
  optional_fields: string[]
  object_role?: string
  metering_role?: string
  point_kind?: string
  measurement_subject?: string
  public_data_fields?: string[]
  specialized_fields?: string[]
  compatible_aliases?: Record<string, string>
  icon: string
  color: string
}

export const DEVICES_UPDATED_EVENT = 'campus:devices-updated'

let deviceTypesCache: DeviceTypeConfig[] | null = null
let deviceTypesPromise: Promise<DeviceTypeConfig[]> | null = null

export const FALLBACK_DEVICE_TYPE_CONFIGS: DeviceTypeConfig[] = [
  { device_type: 'load', name_zh: '用电设备', icon: '⚡', category: 'load', energy_type: 'electricity', name_en: 'Load', unit: 'kW', default_capacity: 100, required_fields: [], optional_fields: [], color: '#FF9800' },
  { device_type: 'solar', name_zh: '光伏发电', icon: '☀️', category: 'solar', energy_type: 'electricity', name_en: 'Solar', unit: 'kW', default_capacity: 50, required_fields: [], optional_fields: [], color: '#FFC107' },
  { device_type: 'wind', name_zh: '风力发电', icon: '💨', category: 'wind', energy_type: 'electricity', name_en: 'Wind Turbine', unit: 'kW', default_capacity: 200, required_fields: [], optional_fields: [], color: '#00BFFF' },
  { device_type: 'storage', name_zh: '储能设备', icon: '🔋', category: 'storage', energy_type: 'electricity', name_en: 'Energy Storage', unit: 'kWh', default_capacity: 500, required_fields: [], optional_fields: [], color: '#4CAF50' },
  { device_type: 'charger', name_zh: '充电桩', icon: '🔌', category: 'charger', energy_type: 'electricity', name_en: 'EV Charger', unit: 'kW', default_capacity: 60, required_fields: [], optional_fields: [], color: '#9C27B0' },
  { device_type: 'water_meter', name_zh: '水表', icon: '💧', category: 'water_meter', energy_type: 'water', name_en: 'Water Meter', unit: 'm³/h', default_capacity: 50, required_fields: [], optional_fields: [], color: '#2196F3' },
  { device_type: 'gas_meter', name_zh: '燃气表', icon: '🔥', category: 'gas_meter', energy_type: 'gas', name_en: 'Gas Meter', unit: 'm³/h', default_capacity: 30, required_fields: [], optional_fields: [], color: '#FF5722' },
  { device_type: 'heat_meter', name_zh: '热量表', icon: '🌡️', category: 'heat_meter', energy_type: 'heat', name_en: 'Heat Meter', unit: 'GJ/h', default_capacity: 10, required_fields: [], optional_fields: [], color: '#E91E63' },
  { device_type: 'cooling_meter', name_zh: '冷量表', icon: '❄️', category: 'cooling_meter', energy_type: 'cooling', name_en: 'Cooling Meter', unit: 'kW', default_capacity: 200, required_fields: [], optional_fields: [], color: '#00BCD4' },
  { device_type: 'steam_meter', name_zh: '蒸汽表', icon: '💨', category: 'heat_meter', energy_type: 'steam', name_en: 'Steam Meter', unit: 't/h', default_capacity: 5, required_fields: [], optional_fields: [], color: '#607D8B' },
  {
    device_type: 'svg',
    name_zh: '无功功率补偿设备',
    subtype_name_zh: 'SVG',
    icon: '⚡',
    category: 'compensation',
    energy_type: 'electricity',
    name_en: 'Static Var Generator',
    subtype_name_en: 'Static Var Generator',
    unit: 'kVAR',
    default_capacity: 200,
    required_fields: ['reactive_power'],
    optional_fields: ['consumption', 'flow_rate', 'voltage', 'current', 'power_factor', 'temperature'],
    public_data_fields: ['timestamp', 'voltage', 'current', 'power_factor', 'reactive_power', 'flow_rate', 'temperature'],
    specialized_fields: [
      'svg_reactive_output', 'capacity_utilization', 'output_direction',
      'run_status', 'stop_status', 'auto_mode', 'local_mode', 'breaker_status',
      'module_status', 'fan_status', 'comm_status',
      'overvoltage_fault', 'undervoltage_fault', 'overcurrent_fault', 'overtemp_fault',
      'module_fault', 'fan_fault', 'comm_fault', 'current_fault_code', 'current_alarm_code',
      'cabinet_temp', 'module_temp', 'igbt_temp', 'dc_bus_voltage', 'heatsink_temp',
    ],
    compatible_aliases: { kvar: 'reactive_power', power: 'flow_rate', active_power: 'flow_rate' },
    color: '#FF6F00',
  },
  {
    device_type: 'capacitor_bank_controller',
    name_zh: '无功功率补偿设备',
    subtype_name_zh: '电容补偿控制器',
    icon: '⚙️',
    category: 'compensation',
    energy_type: 'electricity',
    name_en: 'Capacitor Bank Controller',
    subtype_name_en: 'Capacitor Bank Controller',
    unit: 'kVAR',
    default_capacity: 200,
    required_fields: ['reactive_power'],
    optional_fields: ['consumption', 'flow_rate', 'voltage', 'current', 'power_factor', 'temperature'],
    public_data_fields: ['timestamp', 'voltage', 'current', 'power_factor', 'reactive_power', 'flow_rate', 'temperature'],
    specialized_fields: [
      'power_factor_a', 'power_factor_b', 'power_factor_c',
      'active_power_a', 'active_power_b', 'active_power_c',
      'reactive_power_a', 'reactive_power_b', 'reactive_power_c',
      'apparent_power_a', 'apparent_power_b', 'apparent_power_c',
      'voltage_thd_a', 'voltage_thd_b', 'voltage_thd_c',
      'current_harmonic_a', 'current_harmonic_b', 'current_harmonic_c',
      'leading_a', 'leading_b', 'leading_c',
      'undercurrent_a', 'undercurrent_b', 'undercurrent_c',
      'overvoltage_alarm_a', 'overvoltage_alarm_b', 'overvoltage_alarm_c',
      'voltage_thd_alarm_a', 'voltage_thd_alarm_b', 'voltage_thd_alarm_c',
      'current_thd_alarm_a', 'current_thd_alarm_b', 'current_thd_alarm_c',
      'temp_alarm',
      'circuit_state_phase_a', 'circuit_state_phase_b', 'circuit_state_phase_c',
      'circuit_state_common_1', 'circuit_state_common_2', 'circuit_state_common_3',
    ],
    compatible_aliases: { kvar: 'reactive_power', power: 'flow_rate', active_power: 'flow_rate' },
    color: '#D97706',
  },
]

export function normalizeDeviceHierarchy(device: Device): Device {
  return normalizeCompensationDevice(device)
}

// 1. 获取所有设备
export function getDevices(options: { silent?: boolean } = {}) {
  return request
    .get<never, Device[]>('/devices/', { silent: options.silent })
    .then((devices) => devices.map(normalizeDeviceHierarchy))
}

// 2. 新增设备（智能创建）
export function createDevice(data: DeviceWritePayload) {
  return request.post<DeviceWritePayload, Device>('/devices/', data).then(normalizeDeviceHierarchy)
}

// 3. 修改设备 (Put)
export function updateDevice(id: number, data: DeviceWritePayload) {
  return request.put<DeviceWritePayload, Device>(`/devices/${id}`, data).then(normalizeDeviceHierarchy)
}

// 4. 删除设备
export function deleteDevice(id: number) {
  return request.delete<never, void>(`/devices/${id}`)
}

// 5. 启停控制 (反向控制)
export function toggleDeviceStatus(id: number, active: boolean, reason?: string) {
  const params = new URLSearchParams({ active: String(active) })
  if (reason?.trim()) params.set('reason', reason.trim())
  return request.post<never, Device>(`/devices/${id}/toggle?${params.toString()}`)
}

// 6. 获取支持的设备类型列表（从后端动态获取）
export function getDeviceTypes(options?: { force?: boolean; silent?: boolean }) {
  if (!options?.force && deviceTypesCache) {
    return Promise.resolve(deviceTypesCache)
  }

  if (!options?.force && deviceTypesPromise) {
    return deviceTypesPromise
  }

  deviceTypesPromise = request
    .get<never, SuccessResponse<DeviceTypeConfig[]>>('/devices/types', { silent: options?.silent })
    .then((response) => {
      deviceTypesCache = response.data
      return response.data
    })
    .finally(() => {
      deviceTypesPromise = null
    })

  return deviceTypesPromise
}

// 7. 获取单个设备类型详情
export function getDeviceTypeInfo(deviceType: string) {
  return request
    .get<never, SuccessResponse<DeviceTypeConfig>>(`/devices/types/${deviceType}`)
    .then((response) => response.data)
}

export function notifyDevicesUpdated(detail?: Record<string, unknown>) {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(DEVICES_UPDATED_EVENT, { detail }))
}
