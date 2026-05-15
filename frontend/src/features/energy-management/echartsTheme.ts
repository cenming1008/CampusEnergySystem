// Park EMS Design Tokens v1.0 · ECharts theme for Variant B (Report)
// 主题颜色从 :root 上的 --token-* CSS 变量读取，保证图表配色与全站 token 一一对应。
import { registerTheme } from 'echarts/core'

const TOKEN_NAMES = [
  '--token-medium-elec',
  '--token-medium-cool',
  '--token-medium-heat',
  '--token-medium-water',
  '--token-medium-gas',
] as const

function readToken(name: string, fallback: string): string {
  if (typeof document === 'undefined') return fallback
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}

let registered = false
export function registerParkEmsTheme() {
  if (registered) return
  registered = true

  const color = TOKEN_NAMES.map((n, i) => readToken(n, [
    '#3B82F6', '#06B6D4', '#EF4444', '#14B8A6', '#F59E0B',
  ][i]))

  const textSecondary = readToken('--text-secondary', '#94a3b8')
  const divider = readToken('--divider', 'rgba(148,163,184,0.12)')

  registerTheme('park-ems-report', {
    color,
    backgroundColor: 'transparent',
    textStyle: {
      fontFamily: '"JetBrains Mono", "IBM Plex Mono", "SF Mono", Menlo, monospace',
      color: textSecondary,
    },
    title: {
      textStyle: { color: textSecondary, fontWeight: 500 },
    },
    legend: {
      textStyle: { color: textSecondary, fontFamily: '"Inter", sans-serif' },
    },
    grid: { borderColor: divider },
    categoryAxis: {
      axisLine: { lineStyle: { color: divider } },
      axisTick: { lineStyle: { color: divider } },
      splitLine: { show: false, lineStyle: { color: divider } },
      axisLabel: { color: textSecondary, fontFamily: '"JetBrains Mono", monospace' },
    },
    valueAxis: {
      axisLine: { show: false, lineStyle: { color: divider } },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: divider, type: 'dashed' } },
      axisLabel: { color: textSecondary, fontFamily: '"JetBrains Mono", monospace' },
    },
    tooltip: {
      backgroundColor: 'rgba(22, 33, 51, 0.96)',
      borderColor: 'rgba(255,255,255,0.12)',
      textStyle: { color: '#e6edf5', fontFamily: '"JetBrains Mono", monospace', fontSize: 12 },
    },
  })
}
