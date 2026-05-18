export type CompensationTone = 'success' | 'info' | 'warning' | 'danger' | 'neutral'
export type CompensationDataState = 'live' | 'mock' | 'missing' | 'offline' | 'unconfigured' | 'na'
export type CompensationWorkbenchTab =
  | 'runtime'
  | 'curves'
  | 'parameter-settings'
  | 'event-records'
export type CompensationTrendTab =
  | 'effect'
  | 'voltage'
  | 'current'
  | 'health'
  | 'phase_power'
  | 'phase_active_power'
  | 'phase_reactive_power'
  | 'phase_power_factor'
  | 'phase_voltage'
  | 'phase_current'
  | 'harmonic'
  | 'switching'
export type ModuleStateTone = 'running' | 'standby' | 'alarm' | 'fault'

export interface CompensationTag {
  label: string
  tone: CompensationTone
}

export interface CompensationMetric {
  key: string
  label: string
  value: string
  unit?: string
  hint: string
  tone?: CompensationTone
  state: CompensationDataState
  emphasized?: boolean
}

export interface CompensationPowerFactorTrend {
  values: number[]
  timestamps?: string[]
  target: number | null
}

export interface ModuleStatusModel {
  title: string
  unitLabel: string
  runningModuleCount: number
  totalModuleCount: number
  moduleStates: ModuleStateTone[]
  hint: string
}

export interface CompensationHeaderModel {
  title: string
  serial: string
  location: string
  deviceStatus: string
  deviceStatusTone: CompensationTone
  tags: CompensationTag[]
}

export interface CompensationTrendOption {
  label: string
  value: CompensationTrendTab
}

export interface CompensationWorkbenchTabOption {
  label: string
  value: CompensationWorkbenchTab
  tone?: 'normal' | 'warning' | 'danger'
}

export interface CompensationTrendAxis {
  name: string
  min?: number
  max?: number
  position?: 'left' | 'right'
}

export type CompensationTrendPoint = number | null | [string, number | null]

export interface CompensationTrendSeries {
  name: string
  data: CompensationTrendPoint[]
  color: string
  yAxisIndex?: number
  area?: boolean
}

export interface CompensationTrendSummaryItem {
  label: string
  value: string
}

export interface CompensationTrendModel {
  labels: string[]
  legend: string[]
  axes: CompensationTrendAxis[]
  series: CompensationTrendSeries[]
  xAxisType?: 'category' | 'time'
  xAxisMin?: string
  xAxisMax?: string
  summary: CompensationTrendSummaryItem[]
  empty: boolean
  emptyText: string
  hint?: string
  isMock: boolean
}

export interface CompensationEventItem {
  time: string
  title: string
  detail: string
  tone: CompensationTone
  tag?: string
  isMock?: boolean
}

export interface CompensationStatusItem {
  label: string
  value: string
  tone?: CompensationTone
  hint?: string
}

export interface CompensationProfileItem {
  label: string
  value: string
}

export type HarmonicSpectrumKind = 'voltage' | 'current'
export type HarmonicSpectrumPhase = 'a' | 'b' | 'c'

export interface HarmonicSpectrumBar {
  order: number
  value: number
  exceeded: boolean
  placeholder?: boolean
}

export interface HarmonicSpectrumSummary {
  phaseLabel: string
  kindLabel: string
  unit: string
  peakOrder: number | null
  peakValue: number | null
  threshold: number | null
  statusText: string
  statusTone: CompensationTone
  timestamp: string | null
}

export interface HarmonicSpectrumModel {
  bars: HarmonicSpectrumBar[]
  unit: string
  threshold: number | null
  summary: HarmonicSpectrumSummary
  empty: boolean
  emptyText: string
}
