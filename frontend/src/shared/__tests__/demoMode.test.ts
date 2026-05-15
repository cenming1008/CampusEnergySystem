import { beforeEach, describe, expect, it } from 'vitest'
import { allowDemoMode, isDemoSuppressed, suppressDemoMode } from '../demoMode'

describe('demoMode', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('persists demo suppression across page remounts', () => {
    expect(isDemoSuppressed()).toBe(false)

    suppressDemoMode()
    expect(isDemoSuppressed()).toBe(true)

    allowDemoMode()
    expect(isDemoSuppressed()).toBe(false)
  })
})
