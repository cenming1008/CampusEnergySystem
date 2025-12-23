import request from '@/utils/request'

// 定义登录成功后的返回结构
export interface LoginResult {
  access_token: string
  token_type: string
}

/**
 * 登录接口
 * 后端要求 Content-Type: application/x-www-form-urlencoded
 * 所以这里参数类型是 URLSearchParams
 */
export function loginApi(data: URLSearchParams) {
  return request.post<any, LoginResult>('/auth/login', data, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })
}