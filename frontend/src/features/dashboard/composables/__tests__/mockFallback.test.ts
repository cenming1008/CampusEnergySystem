import { describe, expect, it } from 'vitest'
import {
  FALLBACK_ALERTS,
  FALLBACK_DEVICES,
  FALLBACK_INGESTION_HEALTH,
  FALLBACK_OVERVIEW,
  FALLBACK_PREVIOUS_OVERVIEW,
  FALLBACK_RANKING,
  FALLBACK_TREND,
  FALLBACK_TREND_BY_RANGE,
} from '../mockFallback'

describe('dashboard mock fallback', () => {
  it('provides non-empty dashboard fallback data with 24 hourly trend points', () => {
    expect(FALLBACK_OVERVIEW.analysis_summary.realtime_load).toBeGreaterThan(0)
    expect(FALLBACK_PREVIOUS_OVERVIEW.analysis_summary.total_consumption)
      .toBeLessThan(FALLBACK_OVERVIEW.analysis_summary.total_consumption)
    expect(FALLBACK_OVERVIEW.energy_category_summary.length).toBeGreaterThan(0)
    expect(FALLBACK_ALERTS.length).toBeGreaterThan(0)
    expect(FALLBACK_DEVICES.length).toBeGreaterThan(0)
    expect(FALLBACK_INGESTION_HEALTH.length).toBeGreaterThan(0)
    expect(FALLBACK_RANKING.length).toBeGreaterThan(0)

    for (const points of Object.values(FALLBACK_TREND)) {
      expect(points).toHaveLength(24)
      expect(points.some((point) => point.v > 0)).toBe(true)
    }
    for (const range of ['today', 'yest', 'week', 'month'] as const) {
      expect(FALLBACK_TREND_BY_RANGE[range].electricity).toHaveLength(24)
    }
    expect(FALLBACK_TREND_BY_RANGE.yest.electricity[12].v)
      .not.toBe(FALLBACK_TREND_BY_RANGE.today.electricity[12].v)
  })

  it('covers all dashboard matrix groups with fallback devices', () => {
    expect(FALLBACK_DEVICES.some((device) => device.energy_type === 'electricity')).toBe(true)
    expect(FALLBACK_DEVICES.some((device) => device.device_type === 'pv')).toBe(true)
    expect(FALLBACK_DEVICES.some((device) => device.device_type === 'storage')).toBe(true)
    expect(FALLBACK_DEVICES.some((device) => device.energy_type === 'cooling')).toBe(true)
    expect(FALLBACK_DEVICES.some((device) => device.energy_type === 'heat')).toBe(true)
    expect(FALLBACK_DEVICES.some((device) => device.energy_type === 'water')).toBe(true)
    expect(FALLBACK_DEVICES.some((device) => device.energy_type === 'gas')).toBe(true)
  })
})
