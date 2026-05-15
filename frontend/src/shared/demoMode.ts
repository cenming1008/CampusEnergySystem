const DEMO_MODE_KEY = 'campus-ems-demo-mode'
const DEMO_SUPPRESSED_KEY = 'campus-ems-demo-suppressed'

export function isDemoSuppressed() {
  return !isDemoModeEnabled()
}

export function isDemoModeEnabled() {
  if (typeof window === 'undefined') return false
  return window.localStorage.getItem(DEMO_MODE_KEY) === '1'
}

export function suppressDemoMode() {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(DEMO_MODE_KEY, '0')
  window.localStorage.setItem(DEMO_SUPPRESSED_KEY, '1')
}

export function allowDemoMode() {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(DEMO_MODE_KEY, '1')
  window.localStorage.removeItem(DEMO_SUPPRESSED_KEY)
}

export function setDemoModeEnabled(enabled: boolean) {
  if (enabled) {
    allowDemoMode()
  } else {
    suppressDemoMode()
  }
}
