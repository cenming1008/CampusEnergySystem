import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '../useAuthStore'

describe('useAuthStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('persists session fields when setting a new session', () => {
    const store = useAuthStore()

    store.setSession({
      access_token: 'access-1',
      refresh_token: 'refresh-1',
      token_type: 'bearer',
      role: 'admin',
      must_change_password: true,
    }, 'captain')

    expect(store.token).toBe('access-1')
    expect(store.refreshToken).toBe('refresh-1')
    expect(store.username).toBe('captain')
    expect(store.role).toBe('admin')
    expect(store.mustChangePassword).toBe(true)
    expect(localStorage.getItem('access_token')).toBe('access-1')
    expect(localStorage.getItem('refresh_token')).toBe('refresh-1')
    expect(localStorage.getItem('username')).toBe('captain')
    expect(localStorage.getItem('user_role')).toBe('admin')
    expect(localStorage.getItem('must_change_password')).toBe('true')
  })

  it('applies profile and clears empty location scope', () => {
    const store = useAuthStore()
    localStorage.setItem('location_scope', '1,2')

    store.applyProfile({
      id: 1,
      username: 'operator',
      role: 'operator',
      is_active: true,
      must_change_password: false,
      failed_login_attempts: 0,
      locked_until: null,
      location_scope: null,
    })

    expect(store.username).toBe('operator')
    expect(store.role).toBe('operator')
    expect(store.locationScope).toBeNull()
    expect(localStorage.getItem('location_scope')).toBeNull()
  })

  it('clears all auth state on logout', () => {
    const store = useAuthStore()
    store.setSession({
      access_token: 'access-1',
      refresh_token: 'refresh-1',
      token_type: 'bearer',
      role: 'maintainer',
      must_change_password: false,
    }, 'maintainer')
    localStorage.setItem('location_scope', '3')
    store.locationScope = '3'

    store.logout()

    expect(store.token).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.username).toBeNull()
    expect(store.role).toBeNull()
    expect(store.mustChangePassword).toBe(false)
    expect(store.locationScope).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
    expect(localStorage.getItem('username')).toBeNull()
    expect(localStorage.getItem('user_role')).toBeNull()
    expect(localStorage.getItem('must_change_password')).toBeNull()
    expect(localStorage.getItem('location_scope')).toBeNull()
  })
})
