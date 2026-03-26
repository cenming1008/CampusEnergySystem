import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AuthSession, CurrentUserProfile } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const role = ref<string | null>(localStorage.getItem('user_role'))
  const mustChangePassword = ref(localStorage.getItem('must_change_password') === 'true')
  const locationScope = ref<string | null>(localStorage.getItem('location_scope'))

  function setSession(session: AuthSession, newUser: string) {
    token.value = session.access_token
    refreshToken.value = session.refresh_token
    username.value = newUser
    role.value = session.role
    mustChangePassword.value = session.must_change_password
    locationScope.value = null
    localStorage.setItem('access_token', session.access_token)
    localStorage.setItem('refresh_token', session.refresh_token)
    localStorage.setItem('username', newUser)
    localStorage.setItem('user_role', session.role)
    localStorage.setItem('must_change_password', String(session.must_change_password))
    localStorage.removeItem('location_scope')
  }

  function applyProfile(profile: CurrentUserProfile) {
    username.value = profile.username
    role.value = profile.role
    mustChangePassword.value = profile.must_change_password
    locationScope.value = profile.location_scope || null
    localStorage.setItem('username', profile.username)
    localStorage.setItem('user_role', profile.role)
    localStorage.setItem('must_change_password', String(profile.must_change_password))
    if (profile.location_scope) {
      localStorage.setItem('location_scope', profile.location_scope)
    } else {
      localStorage.removeItem('location_scope')
    }
  }

  function updateTokens(session: Pick<AuthSession, 'access_token' | 'refresh_token' | 'role' | 'must_change_password'>) {
    token.value = session.access_token
    refreshToken.value = session.refresh_token
    role.value = session.role
    mustChangePassword.value = session.must_change_password
    localStorage.setItem('access_token', session.access_token)
    localStorage.setItem('refresh_token', session.refresh_token)
    localStorage.setItem('user_role', session.role)
    localStorage.setItem('must_change_password', String(session.must_change_password))
  }

  function logout() {
    token.value = null
    refreshToken.value = null
    username.value = null
    role.value = null
    mustChangePassword.value = false
    locationScope.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('username')
    localStorage.removeItem('user_role')
    localStorage.removeItem('must_change_password')
    localStorage.removeItem('location_scope')
  }

  return {
    token,
    refreshToken,
    username,
    role,
    mustChangePassword,
    locationScope,
    setSession,
    applyProfile,
    updateTokens,
    logout,
  }
})
