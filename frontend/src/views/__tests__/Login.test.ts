import { beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Login from '../Login.vue'
import { useAuthStore } from '@/stores/useAuthStore'

const {
  pushMock,
  successMock,
  warningMock,
  errorMock,
  loginApiMock,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  successMock: vi.fn(),
  warningMock: vi.fn(),
  errorMock: vi.fn(),
  loginApiMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual<typeof import('element-plus')>('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: successMock,
      warning: warningMock,
      error: errorMock,
    },
  }
})

vi.mock('@/api/auth', () => ({
  loginApi: loginApiMock,
}))

function mountLogin() {
  return shallowMount(Login, {
    global: {
      stubs: {
        'el-icon': true,
      },
    },
  })
}

describe('Login view', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    pushMock.mockReset()
    successMock.mockReset()
    warningMock.mockReset()
    errorMock.mockReset()
    loginApiMock.mockReset()
  })

  it('warns when username is empty', async () => {
    const wrapper = mountLogin()

    await wrapper.find('form').trigger('submit.prevent')

    expect(warningMock).toHaveBeenCalledWith('请输入用户名')
    expect(loginApiMock).not.toHaveBeenCalled()
  })

  it('stores session and redirects to dashboard after successful login', async () => {
    loginApiMock.mockResolvedValue({
      access_token: 'access-1',
      refresh_token: 'refresh-1',
      token_type: 'bearer',
      role: 'admin',
      must_change_password: false,
    })
    const wrapper = mountLogin()

    await wrapper.find('#username').setValue('admin')
    await wrapper.find('#password').setValue('StrongPassword!123')
    await wrapper.find('form').trigger('submit.prevent')

    const authStore = useAuthStore()
    expect(loginApiMock).toHaveBeenCalledTimes(1)
    const submitted = loginApiMock.mock.calls[0][0] as URLSearchParams
    expect(submitted.get('username')).toBe('admin')
    expect(submitted.get('password')).toBe('StrongPassword!123')
    expect(authStore.token).toBe('access-1')
    expect(authStore.username).toBe('admin')
    expect(pushMock).toHaveBeenCalledWith('/')
    expect(successMock).toHaveBeenCalledWith('登录成功，欢迎进入系统')
  })

  it('redirects to account security when password change is required', async () => {
    loginApiMock.mockResolvedValue({
      access_token: 'access-2',
      refresh_token: 'refresh-2',
      token_type: 'bearer',
      role: 'operator',
      must_change_password: true,
    })
    const wrapper = mountLogin()

    await wrapper.find('#username').setValue('operator')
    await wrapper.find('#password').setValue('StrongPassword!123')
    await wrapper.find('form').trigger('submit.prevent')

    expect(pushMock).toHaveBeenCalledWith('/account/security')
  })
})
