import type { CompensationTrendTab } from './types'

export interface TimestampedPoint {
  timestamp: string
}

const SECOND = 1000
const HOUR = 60 * 60 * SECOND
const DAY = 24 * HOUR

const MIN_HISTORY_LIMIT = 600
const MAX_HISTORY_LIMIT = 1000

function getDurationMs(start: Date, end: Date) {
  return Math.max(0, end.getTime() - start.getTime())
}

function getRequestSampleSeconds(durationMs: number) {
  if (durationMs <= 2 * HOUR) return 2
  if (durationMs <= 12 * HOUR) return 10
  if (durationMs <= DAY) return 30
  if (durationMs <= 3 * DAY) return 120
  return 300
}

export function getTrendMaxPoints(
  start: Date,
  end: Date,
  tab: CompensationTrendTab = 'effect',
) {
  const durationMs = getDurationMs(start, end)
  const base = durationMs <= 2 * HOUR
    ? 720
    : durationMs <= 12 * HOUR
      ? 600
      : durationMs <= DAY
        ? 480
        : durationMs <= 3 * DAY
          ? 360
          : 240

  if (tab === 'switching') return Math.min(900, Math.round(base * 1.25))
  if (tab === 'phase_power' || tab === 'harmonic') return Math.min(780, Math.round(base * 1.1))
  if (tab === 'health') return Math.max(180, Math.round(base * 0.75))
  return base
}

export function calculateHistoryLimit(start: Date, end: Date) {
  const durationMs = getDurationMs(start, end)
  const sampleSeconds = getRequestSampleSeconds(durationMs)
  const estimatedPoints = Math.ceil(durationMs / (sampleSeconds * SECOND)) + 1
  return Math.min(MAX_HISTORY_LIMIT, Math.max(MIN_HISTORY_LIMIT, estimatedPoints))
}

export function sampleTimeSeriesByTimestamp<T extends TimestampedPoint>(
  points: T[],
  maxPoints: number,
): T[] {
  if (points.length <= maxPoints || maxPoints < 3) {
    return points
  }

  const sampled: T[] = [points[0]]
  const interiorTarget = maxPoints - 2
  const lastIndex = points.length - 1

  for (let index = 1; index <= interiorTarget; index += 1) {
    const pointIndex = Math.round((index * lastIndex) / (interiorTarget + 1))
    const point = points[Math.min(lastIndex - 1, Math.max(1, pointIndex))]
    if (sampled[sampled.length - 1] !== point) {
      sampled.push(point)
    }
  }

  if (sampled[sampled.length - 1] !== points[lastIndex]) {
    sampled.push(points[lastIndex])
  }

  return sampled
}
