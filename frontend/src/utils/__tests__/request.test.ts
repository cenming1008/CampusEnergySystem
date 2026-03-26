import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const mockState = vi.hoisted(() => {
  let requestFulfilled: ((config: Record<string, unknown>) => Record<string, unknown> | Promise<Record<string, unknown>>) | undefined
  let requestRejected: ((error: unknown) => unknown) | undefined
  let responseFulfilled: ((response: { data: unknown }) => unknown) | undefined
  let responseRejected: ((error: unknown) => unknown) | undefined

  const service = Object.assign(vi.fn(), {
    post: vi.fn(),
    interceptors: {
      request: {
        use: vi.fn((fulfilled: typeof requestFulfilled, rejected: typeof requestRejected) => {
          requestFulfilled = fulfilled
          requestRejected = rejected
        }),
      },
      response: {
        use: vi.fn((fulfilled: typeof responseFulfilled, rejected: typeof responseRejected) => {
          responseFulfilled = fulfilled
          responseRejected = rejected
        }),
      },
    },
  })

  return {
    service,
    pushMock: vi.fn(),
    disconnectMock: vi.fn(),
    errorMessageMock: vi.fn(),
    warningMessageMock: vi.fn(),
    frontendErrorMock: vi.fn(),
    currentRoute: { value: { name: 'Dashboard' } },
    getRequestFulfilled: () => requestFulfilled,
    getRequestRejected: () => requestRejected,
    getResponseFulfilled: () => responseFulfilled,
    getResponseRejected: () => responseRejected,
  }
})

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockState.service),
  },
  AxiosError: class AxiosError extends Error {},
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    error: mockState.errorMessageMock,
    warning: mockState.warningMessageMock,
  },
}))

vi.mock('@/router', () => ({
  default: {
    currentRoute: mockState.currentRoute,
    push: mockState.pushMock,
  },
}))

vi.mock('@/stores/useSocketStore', () => ({
  useSocketStore: () => ({
    disconnect: mockState.disconnectMock,
  }),
}))

vi.mock('@/observability/errorReporting', () => ({
  reportFrontendError: mockState.frontendErrorMock,
}))

async function loadRequestModule() {
  vi.resetModules()
  await import('../request')
  return {
    requestFulfilled: mockState.getRequestFulfilled(),
    requestRejected: mockState.getRequestRejected(),
    responseFulfilled: mockState.getResponseFulfilled(),
    responseRejected: mockState.getResponseRejected(),
  }
}

describe('request interceptors', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    mockState.service.mockReset()
    mockState.service.post.mockReset()
    mockState.service.interceptors.request.use.mockClear()
    mockState.service.interceptors.response.use.mockClear()
    mockState.pushMock.mockReset()
    mockState.disconnectMock.mockReset()
    mockState.errorMessageMock.mockReset()
    mockState.warningMessageMock.mockReset()
    mockState.frontendErrorMock.mockReset()
    mockState.currentRoute.value = { name: 'Dashboard' }
  })

  it('adds bearer token to outgoing requests', async () => {
    const { useAuthStore } = await import('@/stores/useAuthStore')
    const store = useAuthStore()
    store.token = 'access-token'
    const handlers = await loadRequestModule()

    const config = await handlers.requestFulfilled?.({ headers: {} })

    expect(config?.headers).toMatchObject({
      Authorization: 'Bearer access-token',
    })
  })

  it('returns response data directly on success', async () => {
    const handlers = await loadRequestModule()
    const result = handlers.responseFulfilled?.({ data: { ok: true } })
    expect(result).toEqual({ ok: true })
  })

  it('refreshes the access token and retries the original request on 401', async () => {
    const { useAuthStore } = await import('@/stores/useAuthStore')
    const store = useAuthStore()
    store.refreshToken = 'refresh-old'
    mockState.service.post.mockResolvedValue({
      access_token: 'access-new',
      refresh_token: 'refresh-new',
      role: 'admin',
      must_change_password: false,
    })
    mockState.service.mockResolvedValue({ retried: true })

    const handlers = await loadRequestModule()
    const result = await handlers.responseRejected?.({
      response: { status: 401, data: { detail: 'token expired' } },
      message: 'Unauthorized',
      config: {
        method: 'get',
        url: '/devices/',
        headers: {},
      },
    })

    expect(mockState.service.post).toHaveBeenCalledWith(
      '/auth/refresh',
      { refresh_token: 'refresh-old' },
      expect.objectContaining({ silent: true, skipAuthRefresh: true })
    )
    expect(store.token).toBe('access-new')
    expect(store.refreshToken).toBe('refresh-new')
    expect(mockState.service).toHaveBeenCalledWith(expect.objectContaining({
      _retry: true,
      headers: expect.objectContaining({
        Authorization: 'Bearer access-new',
      }),
    }))
    expect(result).toEqual({ retried: true })
  })

  it('logs out and redirects to login when refresh is unavailable', async () => {
    const { useAuthStore } = await import('@/stores/useAuthStore')
    const store = useAuthStore()
    store.token = 'expired-token'
    store.refreshToken = null

    const handlers = await loadRequestModule()
    const error = {
      response: { status: 401, data: { detail: 'session expired' } },
      message: 'Unauthorized',
      config: {
        method: 'get',
        url: '/users/me',
        headers: {},
      },
    }

    await expect(handlers.responseRejected?.(error)).rejects.toBe(error)
    expect(store.token).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(mockState.errorMessageMock).toHaveBeenCalledWith('登录已过期或无效，请重新登录')
    expect(mockState.disconnectMock).toHaveBeenCalledTimes(1)
    expect(mockState.pushMock).toHaveBeenCalledWith({ name: 'Login' })
    expect(mockState.frontendErrorMock).toHaveBeenCalledWith(expect.objectContaining({
      category: 'http',
    }))
  })

  it('redirects to account security when backend requires password change', async () => {
    const { useAuthStore } = await import('@/stores/useAuthStore')
    const store = useAuthStore()
    store.mustChangePassword = false

    const handlers = await loadRequestModule()
    const error = {
      response: { status: 403, data: { detail: '首次登录后必须先修改密码' } },
      message: 'Forbidden',
      config: {
        method: 'post',
        url: '/devices/1/toggle',
        headers: {},
      },
    }

    await expect(handlers.responseRejected?.(error)).rejects.toBe(error)
    expect(store.mustChangePassword).toBe(true)
    expect(mockState.warningMessageMock).toHaveBeenCalledWith('请先完成密码修改后再继续使用系统')
    expect(mockState.pushMock).toHaveBeenCalledWith({ name: 'AccountSecurity' })
  })

  it('shows error message for non-silent server errors and reports them', async () => {
    const handlers = await loadRequestModule()
    const error = {
      response: { status: 500, data: { detail: '服务器内部错误' } },
      message: 'Internal Server Error',
      config: {
        method: 'get',
        url: '/reports/export_csv',
        headers: {},
      },
    }

    await expect(handlers.responseRejected?.(error)).rejects.toBe(error)
    expect(mockState.errorMessageMock).toHaveBeenCalledWith('服务器内部错误')
    expect(mockState.frontendErrorMock).toHaveBeenCalledWith(expect.objectContaining({
      category: 'http',
      message: expect.stringContaining('/reports/export_csv'),
    }))
  })
})
