import request from '@/utils/request'

export interface UserRecord {
  id: number
  username: string
  role: string
  location_scope?: string | null
  is_active: boolean
  must_change_password: boolean
  failed_login_attempts: number
  locked_until?: string | null
}

export function getUsers() {
  return request.get<never, UserRecord[]>('/users/')
}

export function createUser(payload: {
  username: string
  password: string
  role: string
  location_scope?: string | null
  is_active: boolean
}) {
  return request.post<typeof payload, UserRecord>('/users/', payload)
}

export function updateUserRole(userId: number, role: string) {
  return request.put<{ role: string }, UserRecord>(`/users/${userId}/role`, { role })
}

export function updateUserStatus(userId: number, is_active: boolean) {
  return request.put<{ is_active: boolean }, UserRecord>(`/users/${userId}/status`, { is_active })
}

export function updateUserScope(userId: number, location_scope?: string | null) {
  return request.put<{ location_scope?: string | null }, UserRecord>(`/users/${userId}/scope`, { location_scope })
}

export function changeUserPassword(userId: number, new_password: string) {
  return request.put<{ new_password: string }, { success: boolean; message: string }>(
    `/users/${userId}/password`,
    { new_password }
  )
}

export function forceUserPasswordReset(userId: number, must_change_password: boolean) {
  return request.put<{ must_change_password: boolean }, UserRecord>(`/users/${userId}/force-password-reset`, { must_change_password })
}

export function revokeUserSessions(userId: number) {
  return request.post<Record<string, never>, { success: boolean; message: string }>(`/users/${userId}/revoke-sessions`, {})
}

export function unlockUser(userId: number) {
  return request.post<Record<string, never>, UserRecord>(`/users/${userId}/unlock`, {})
}
