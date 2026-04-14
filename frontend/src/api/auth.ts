import request from '@/utils/request'
import type { AxiosRequestConfig } from 'axios'
import type { SuccessResponse } from '@/types/api'

export interface AuthSession {
  access_token: string
  refresh_token: string
  token_type: string
  role: string
  must_change_password: boolean
}

export interface CurrentUserProfile {
  id: number
  username: string
  role: string
  location_scope?: string | null
  is_active: boolean
  must_change_password: boolean
  failed_login_attempts: number
  locked_until?: string | null
}

/**
 * 登录接口
 * 后端要求 Content-Type: application/x-www-form-urlencoded
 * 所以这里参数类型是 URLSearchParams
 */
export function loginApi(data: URLSearchParams) {
  const config = {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    skipAuthRefresh: true,
    skipAuthHeader: true,
  } as AxiosRequestConfig & { skipAuthRefresh: true; skipAuthHeader: true }
  return request.post<URLSearchParams, AuthSession>('/auth/login', data, {
    ...config,
  })
}

export function logoutApi() {
  return request.post<Record<string, never>, { success: boolean; message: string; token_version: number }>(
    '/auth/logout',
    {},
    { silent: true, skipAuthRefresh: true }
  )
}

export function getCurrentUserApi() {
  return request
    .get<never, SuccessResponse<CurrentUserProfile>>('/users/me', { silent: true })
    .then((response) => response.data)
}

export function changeMyPasswordApi(payload: { current_password: string; new_password: string }) {
  return request.put<{ current_password: string; new_password: string }, SuccessResponse<null>>('/users/me/password', payload)
}
