const DEMO_SUPPRESSED_KEY = 'campus-ems-demo-suppressed'

export function isDemoSuppressed() {
  if (typeof window === 'undefined') return false
  return window.localStorage.getItem(DEMO_SUPPRESSED_KEY) === '1'
}

export function suppressDemoMode() {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(DEMO_SUPPRESSED_KEY, '1')
}

export function allowDemoMode() {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(DEMO_SUPPRESSED_KEY)
}
