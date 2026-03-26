import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { installGlobalErrorReporting, reportFrontendError } from '../errorReporting'

describe('errorReporting', () => {
  const originalSendBeacon = navigator.sendBeacon
  const originalFetch = global.fetch

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    navigator.sendBeacon = originalSendBeacon
    global.fetch = originalFetch
  })

  it('prefers sendBeacon when available', () => {
    const sendBeaconMock = vi.fn(() => true)
    navigator.sendBeacon = sendBeaconMock

    reportFrontendError({
      category: 'http',
      message: 'GET /devices -> 500',
      route: '/devices',
    })

    expect(sendBeaconMock).toHaveBeenCalledTimes(1)
    expect(sendBeaconMock).toHaveBeenCalledWith('/frontend-errors', expect.any(Blob))
  })

  it('falls back to fetch when sendBeacon is unavailable', async () => {
    navigator.sendBeacon = undefined as unknown as typeof navigator.sendBeacon
    const fetchMock = vi.fn(() => Promise.resolve(new Response(null, { status: 202 })))
    global.fetch = fetchMock as typeof fetch

    reportFrontendError({
      category: 'runtime',
      message: 'boom',
      route: '/dashboard',
    })

    await Promise.resolve()

    expect(fetchMock).toHaveBeenCalledWith('/frontend-errors', expect.objectContaining({
      method: 'POST',
      keepalive: true,
    }))
  })

  it('registers global error handlers for runtime and promise errors', () => {
    const sendBeaconMock = vi.fn(() => true)
    navigator.sendBeacon = sendBeaconMock
    installGlobalErrorReporting()

    window.dispatchEvent(new ErrorEvent('error', {
      message: 'runtime failed',
      error: new Error('runtime failed'),
      filename: 'app.ts',
      lineno: 12,
      colno: 4,
    }))
    window.dispatchEvent(new PromiseRejectionEvent('unhandledrejection', {
      promise: Promise.resolve(),
      reason: new Error('promise failed'),
    }))

    expect(sendBeaconMock).toHaveBeenCalledTimes(2)
    expect(sendBeaconMock).toHaveBeenNthCalledWith(1, '/frontend-errors', expect.any(Blob))
    expect(sendBeaconMock).toHaveBeenNthCalledWith(2, '/frontend-errors', expect.any(Blob))
  })
})
