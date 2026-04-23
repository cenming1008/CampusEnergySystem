import { describe, expect, it } from 'vitest'

import {
  calculateHistoryLimit,
  getTrendMaxPoints,
  sampleTimeSeriesByTimestamp,
} from '../trendSampling'

function buildPoints(count: number) {
  const base = new Date('2026-04-21T16:10:52')
  return Array.from({ length: count }, (_, index) => ({
    timestamp: new Date(base.getTime() + index * 1000).toISOString(),
    value: index,
  }))
}

describe('trendSampling helpers', () => {
  it('requests enough history points to cover the selected time range', () => {
    const start = new Date('2026-04-21T16:10:52')
    const end = new Date('2026-04-21T17:10:52')

    expect(calculateHistoryLimit(start, end)).toBeGreaterThan(500)
  })

  it('uses smaller chart point budgets for longer time ranges', () => {
    const shortStart = new Date('2026-04-21T16:10:52')
    const shortEnd = new Date('2026-04-21T17:10:52')
    const longStart = new Date('2026-04-14T16:10:52')
    const longEnd = new Date('2026-04-21T17:10:52')

    expect(getTrendMaxPoints(shortStart, shortEnd)).toBeGreaterThan(getTrendMaxPoints(longStart, longEnd))
  })

  it('allocates more points to switching tabs than smooth health tabs in the same range', () => {
    const start = new Date('2026-04-21T16:10:52')
    const end = new Date('2026-04-21T17:10:52')

    expect(getTrendMaxPoints(start, end, 'switching')).toBeGreaterThan(getTrendMaxPoints(start, end, 'health'))
  })

  it('samples dense time series while preserving the selected range boundaries', () => {
    const points = buildPoints(1535)

    const sampled = sampleTimeSeriesByTimestamp(points, 600)

    expect(sampled.length).toBeLessThanOrEqual(600)
    expect(sampled[0]).toEqual(points[0])
    expect(sampled.at(-1)).toEqual(points.at(-1))
    expect(new Date(sampled[Math.floor(sampled.length / 4)].timestamp).getTime())
      .toBeLessThanOrEqual(new Date(points[450].timestamp).getTime())
    expect(new Date(sampled[Math.floor((sampled.length * 3) / 4)].timestamp).getTime())
      .toBeGreaterThanOrEqual(new Date(points[1050].timestamp).getTime())
  })
})
