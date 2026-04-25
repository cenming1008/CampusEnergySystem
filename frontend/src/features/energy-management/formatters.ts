export const severityLabels: Record<string, string> = {
  critical: '严重',
  warning: '提示',
  info: '信息',
}

export const anomalyKindLabels: Record<string, string> = {
  data_gap: '接入断档',
  ingestion_failure: '连续失败',
  active_alarm: '未恢复告警',
}

export function formatBooleanRule(value?: boolean) {
  if (value == null) return '未声明'
  return value ? '允许' : '不允许'
}

export function formatMetricValue(value?: number, digits = 1) {
  return Number.isFinite(value) ? Number(value).toFixed(digits) : '0.0'
}

export function formatPercent(value: number | null | undefined, digits = 1) {
  if (value == null || Number.isNaN(value)) return '-'
  return `${(value * 100).toFixed(digits)}%`
}

export function formatSignedPercent(value: number | null | undefined, digits = 1) {
  if (value == null || Number.isNaN(value)) return '暂无环比'
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${(value * 100).toFixed(digits)}%`
}

export function formatTimestamp(value: string | null | undefined, granularity = 'day') {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return granularity === 'hour'
    ? date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
    : date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

export function getSeverityType(value: string) {
  if (value === 'critical') return 'danger'
  if (value === 'warning') return 'warning'
  return 'info'
}

export function getAnomalyKindLabel(value: string) {
  return anomalyKindLabels[value] || value
}
