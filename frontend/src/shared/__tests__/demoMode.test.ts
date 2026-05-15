import { beforeEach, describe, expect, it } from 'vitest'
import {
  allowDemoMode,
  isDemoModeEnabled,
  isDemoSuppressed,
  setDemoModeEnabled,
  suppressDemoMode,
} from '../demoMode'

describe('demoMode', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('persists demo suppression across page remounts', () => {
    expect(isDemoModeEnabled()).toBe(false)
    expect(isDemoSuppressed()).toBe(true)

    suppressDemoMode()
    expect(isDemoModeEnabled()).toBe(false)
    expect(isDemoSuppressed()).toBe(true)

    allowDemoMode()
    expect(isDemoModeEnabled()).toBe(true)
    expect(isDemoSuppressed()).toBe(false)
  })

  it('stores explicit demo mode selection', () => {
    setDemoModeEnabled(true)
    expect(isDemoModeEnabled()).toBe(true)
    expect(isDemoSuppressed()).toBe(false)

    setDemoModeEnabled(false)
    expect(isDemoModeEnabled()).toBe(false)
    expect(isDemoSuppressed()).toBe(true)
  })
})
