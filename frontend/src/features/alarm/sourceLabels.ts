export function alarmSourceLabel(source?: string | null) {
  const labels: Record<string, string> = {
    device_native: '设备原生',
    platform_rule: '平台规则',
    platform_comm: '平台通讯',
    telemetry: '历史遥测',
  }
  if (!source) return '-'
  return labels[source] ?? source
}
