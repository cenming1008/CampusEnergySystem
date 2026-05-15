import { describe, expect, it } from 'vitest'
import { isTimestampFresh, REALTIME_FRESH_THRESHOLD_MS } from '../useCompensationMonitor'

describe('isTimestampFresh', () => {
  const now = Date.parse('2026-05-15T12:00:00Z')

  it('returns false when timestamp is missing', () => {
    expect(isTimestampFresh(undefined, REALTIME_FRESH_THRESHOLD_MS, now)).toBe(false)
    expect(isTimestampFresh(null, REALTIME_FRESH_THRESHOLD_MS, now)).toBe(false)
  })

  it('returns false when timestamp is unparseable', () => {
    expect(isTimestampFresh('not-a-date', REALTIME_FRESH_THRESHOLD_MS, now)).toBe(false)
  })

  it('returns true when timestamp is within threshold', () => {
    const recent = new Date(now - 30_000).toISOString()
    expect(isTimestampFresh(recent, REALTIME_FRESH_THRESHOLD_MS, now)).toBe(true)
  })

  it('returns false when timestamp is older than threshold', () => {
    const stale = new Date(now - 5 * 60_000).toISOString()
    expect(isTimestampFresh(stale, REALTIME_FRESH_THRESHOLD_MS, now)).toBe(false)
  })

  it('treats exact threshold as fresh', () => {
    const edge = new Date(now - REALTIME_FRESH_THRESHOLD_MS).toISOString()
    expect(isTimestampFresh(edge, REALTIME_FRESH_THRESHOLD_MS, now)).toBe(true)
  })
})
