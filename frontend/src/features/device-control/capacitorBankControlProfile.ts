import type { CompensationCapacitorBankControlProfile } from '@/api/compensation'

export interface CapacitorBankControlParameterMeta {
  key: keyof CompensationCapacitorBankControlProfile
  group: 'strategy' | 'circuits' | 'protection' | 'device'
  label: string
  register: string
  readWrite: '读/写'
  unit?: string
  description: string
  summary?: boolean
  editable?: boolean
  inputKind?: 'number' | 'boolean' | 'text' | 'select'
  min?: number
  max?: number
  step?: number
  options?: Array<{ label: string; value: string | number | boolean }>
}

export const capacitorBankControlParameterMeta: CapacitorBankControlParameterMeta[] = [
  {
    key: 'switch_on_power_factor',
    group: 'strategy',
    label: '投入功率因数',
    register: '0xD2',
    readWrite: '读/写',
    description: '功率因数低于该值时，控制器进入投入判定。',
    summary: true,
    editable: true,
    inputKind: 'number',
    min: 0.7,
    max: 1.25,
    step: 0.01,
  },
  {
    key: 'switch_off_power_factor',
    group: 'strategy',
    label: '切除功率因数',
    register: '0xD3',
    readWrite: '读/写',
    description: '功率因数高于该值时，控制器进入切除判定。',
    summary: true,
    editable: true,
    inputKind: 'number',
    min: 0.75,
    max: 1.3,
    step: 0.01,
  },
  {
    key: 'switch_on_delay_seconds',
    group: 'strategy',
    label: '投入延时',
    register: '0xD4',
    readWrite: '读/写',
    unit: '秒',
    description: '投入前的延迟时间。',
    summary: true,
    editable: true,
    inputKind: 'number',
    min: 0,
    max: 300,
    step: 1,
  },
  {
    key: 'switch_off_delay_seconds',
    group: 'strategy',
    label: '切除延时',
    register: '0xD5',
    readWrite: '读/写',
    unit: '秒',
    description: '切除前的延迟时间。',
    summary: true,
    editable: true,
    inputKind: 'number',
    min: 0,
    max: 100,
    step: 1,
  },
  {
    key: 'common_output_circuit_count',
    group: 'circuits',
    label: '共补输出回路',
    register: '0xD6',
    readWrite: '读/写',
    description: '共补输出路数配置。',
    editable: true,
    inputKind: 'number',
    min: 0,
    max: 24,
    step: 1,
  },
  {
    key: 'split_output_circuit_count',
    group: 'circuits',
    label: '分补输出回路',
    register: '0xD7',
    readWrite: '读/写',
    description: '分补输出路数配置。',
    editable: true,
    inputKind: 'number',
    min: 0,
    max: 8,
    step: 1,
  },
  {
    key: 'common_capacity_code',
    group: 'circuits',
    label: '共补容量编码',
    register: '0xD8',
    readWrite: '读/写',
    description: '共补输出容量编码。',
    editable: true,
    inputKind: 'text',
  },
  {
    key: 'split_capacity_code',
    group: 'circuits',
    label: '分补容量编码',
    register: '0xD9',
    readWrite: '读/写',
    description: '分补输出容量编码。',
    editable: true,
    inputKind: 'text',
  },
  {
    key: 'common_step_capacity_kvar',
    group: 'circuits',
    label: '共补阶梯容量',
    register: '0xDA',
    readWrite: '读/写',
    unit: 'kVar',
    description: '共补每阶容量。',
    editable: true,
    inputKind: 'number',
    min: 0.1,
    max: 150,
    step: 0.1,
  },
  {
    key: 'split_step_capacity_kvar',
    group: 'circuits',
    label: '分补阶梯容量',
    register: '0xDB',
    readWrite: '读/写',
    unit: 'kVar',
    description: '分补每阶容量。',
    editable: true,
    inputKind: 'number',
    min: 0.1,
    max: 50,
    step: 0.1,
  },
  {
    key: 'ct_primary_current',
    group: 'device',
    label: '互感器一次值',
    register: '0xDC',
    readWrite: '读/写',
    description: '电流互感器一次侧额定值。',
    editable: true,
    inputKind: 'number',
    min: 1,
    max: 1600,
    step: 1,
  },
  {
    key: 'overvoltage_threshold',
    group: 'protection',
    label: '过压保护门限',
    register: '0xDD',
    readWrite: '读/写',
    unit: 'V',
    description: '过压保护触发门限。',
    summary: true,
    editable: true,
    inputKind: 'number',
    min: 230,
    max: 265,
    step: 0.1,
  },
  {
    key: 'voltage_harmonic_threshold',
    group: 'protection',
    label: '电压谐波门限',
    register: '0xDE',
    readWrite: '读/写',
    unit: '%',
    description: '电压谐波告警门限。',
    editable: true,
    inputKind: 'number',
    min: 0,
    max: 50,
    step: 0.1,
  },
  {
    key: 'current_harmonic_threshold',
    group: 'protection',
    label: '电流谐波门限',
    register: '0xDF',
    readWrite: '读/写',
    unit: 'A',
    description: '电流谐波告警门限。',
    editable: true,
    inputKind: 'number',
    min: 0,
    max: 200,
    step: 0.1,
  },
  {
    key: 'temperature_upper_limit',
    group: 'protection',
    label: '温度上限门限',
    register: '0xE0',
    readWrite: '读/写',
    unit: '°C',
    description: '柜内温度保护阈值。',
    summary: true,
    editable: true,
    inputKind: 'number',
    min: 50,
    max: 100,
    step: 0.1,
  },
  {
    key: 'alarm_drive_event',
    group: 'device',
    label: '报警驱动事件',
    register: '0xE1',
    readWrite: '读/写',
    description: '告警驱动事件配置。',
    editable: true,
    inputKind: 'select',
    options: [
      { label: '0', value: '0' },
      { label: '1', value: '1' },
      { label: '2', value: '2' },
      { label: '3', value: '3' },
      { label: '4', value: '4' },
    ],
  },
  {
    key: 'baud_rate',
    group: 'device',
    label: '通讯速率',
    register: '0xE2',
    readWrite: '读/写',
    unit: 'bps',
    description: '控制器通讯波特率。',
    summary: true,
    editable: true,
    inputKind: 'select',
    options: [
      { label: '2400', value: 2400 },
      { label: '9600', value: 9600 },
      { label: '19200', value: 19200 },
      { label: '38400', value: 38400 },
      { label: '115200', value: 115200 },
    ],
  },
  {
    key: 'terminal_assignment_scheme',
    group: 'device',
    label: '端子分配方案',
    register: '0xE3',
    readWrite: '读/写',
    description: '控制器端子分配方案。',
    editable: true,
    inputKind: 'select',
    options: [
      { label: '方案 0', value: '0' },
      { label: '方案 1', value: '1' },
      { label: '方案 2', value: '2' },
      { label: '方案 3', value: '3' },
    ],
  },
  {
    key: 'current_polarity_identification_enabled',
    group: 'device',
    label: '电流极性识别',
    register: '0xE4',
    readWrite: '读/写',
    description: '电流极性识别功能状态。',
    editable: true,
    inputKind: 'boolean',
  },
]

export const capacitorBankControlGroupLabels = {
  strategy: '投切策略',
  circuits: '回路配置',
  protection: '保护门限',
  device: '设备配置',
} as const

export const capacitorBankEditableParameterMeta = capacitorBankControlParameterMeta
  .filter((item) => item.editable)

export function getCapacitorBankControlParameterMeta(key: string) {
  return capacitorBankControlParameterMeta.find((item) => item.key === key)
}

export function getCapacitorBankEditableParameterMeta(key: string) {
  return capacitorBankEditableParameterMeta.find((item) => item.key === key)
}

export function formatCapacitorBankControlValue(
  profile: CompensationCapacitorBankControlProfile | null | undefined,
  meta: CapacitorBankControlParameterMeta,
) {
  const rawValue = profile?.[meta.key]
  if (rawValue === null || rawValue === undefined || rawValue === '') {
    return '暂无参数'
  }
  if (typeof rawValue === 'boolean') {
    return rawValue ? '开启' : '关闭'
  }
  if (
    (meta.key === 'switch_on_power_factor' || meta.key === 'switch_off_power_factor')
    && typeof rawValue === 'number'
  ) {
    const normalized = rawValue > 2 ? rawValue / 100 : rawValue
    return normalized.toFixed(2)
  }
  return meta.unit ? `${rawValue} ${meta.unit}` : String(rawValue)
}

export function getCapacitorBankControlEditableValue(
  profile: CompensationCapacitorBankControlProfile | null | undefined,
  meta: CapacitorBankControlParameterMeta,
) {
  const rawValue = profile?.[meta.key] as string | number | boolean | null | undefined
  if (rawValue === null || rawValue === undefined || rawValue === '') {
    if (meta.inputKind === 'boolean') {
      return false
    }
    return null
  }
  if (
    (meta.key === 'switch_on_power_factor' || meta.key === 'switch_off_power_factor')
    && typeof rawValue === 'number'
  ) {
    const normalized = rawValue > 2 ? rawValue / 100 : rawValue
    return Number(normalized.toFixed(2))
  }
  return rawValue
}
