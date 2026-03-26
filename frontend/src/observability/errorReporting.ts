export interface FrontendErrorEvent {
  category: 'runtime' | 'promise' | 'vue' | 'http'
  message: string
  url?: string
  route?: string
  stack?: string
  metadata?: Record<string, unknown>
}

const REPORT_ENDPOINT = '/frontend-errors'

function serializeError(value: unknown): { message: string; stack?: string } {
  if (value instanceof Error) {
    return { message: value.message, stack: value.stack }
  }
  if (typeof value === 'string') {
    return { message: value }
  }
  try {
    return { message: JSON.stringify(value) }
  } catch {
    return { message: 'Unknown frontend error' }
  }
}

export function reportFrontendError(event: FrontendErrorEvent) {
  const payload = JSON.stringify({
    ...event,
    user_agent: navigator.userAgent,
  })

  if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
    const blob = new Blob([payload], { type: 'application/json' })
    navigator.sendBeacon(REPORT_ENDPOINT, blob)
    return
  }

  void fetch(REPORT_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: payload,
    keepalive: true,
  })
}

export function installGlobalErrorReporting() {
  window.addEventListener('error', (event) => {
    const serialized = serializeError(event.error || event.message)
    reportFrontendError({
      category: 'runtime',
      message: serialized.message,
      stack: serialized.stack,
      url: window.location.href,
      route: window.location.pathname,
      metadata: {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      },
    })
  })

  window.addEventListener('unhandledrejection', (event) => {
    const serialized = serializeError(event.reason)
    reportFrontendError({
      category: 'promise',
      message: serialized.message,
      stack: serialized.stack,
      url: window.location.href,
      route: window.location.pathname,
    })
  })
}
