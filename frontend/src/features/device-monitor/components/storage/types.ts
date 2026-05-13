export type StorageTone = 'success' | 'info' | 'warning' | 'danger' | 'neutral'
export type StorageDataState = 'live' | 'mock' | 'missing' | 'offline'

export type StorageRunState = 'charging' | 'discharging' | 'idle' | 'standby' | 'fault' | 'unknown'

export interface StorageMetric {
  key: string
  label: string
  value: string
  unit?: string
  hint?: string
  tone?: StorageTone
  state: StorageDataState
}

export interface StorageTrendTab {
  label: string
  value: 'soc' | 'power' | 'temperature' | 'energy'
}

export interface StorageTrendSeries {
  name: string
  data: (number | null)[]
  color: string
  yAxisIndex?: number
}

export interface StorageTrendModel {
  labels: string[]
  series: StorageTrendSeries[]
  empty: boolean
  emptyText: string
  yAxisName?: string
  yAxisRight?: string
}
