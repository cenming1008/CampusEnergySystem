import { beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AccountSecurity from '../AccountSecurity.vue'
import { useAuthStore } from '@/stores/useAuthStore'

const {
  changeMyPasswordApiMock,
  logoutApiMock,
  pushMock,
  successMock,
  warningMock,
} = vi.hoisted(() => ({
  changeMyPasswordApiMock: vi.fn(),
  logoutApiMock: vi.fn(),
  pushMock: vi.fn(),
  successMock: vi.fn(),
  warningMock: vi.fn(),
}))

vi.mock('@/api/auth', () => ({
  changeMyPasswordApi: changeMyPasswordApiMock,
  logoutApi: logoutApiMock,
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
      error: vi.fn(),
    },
  }
})

function mountView() {
  return shallowMount(AccountSecurity, {
    global: {
      stubs: {
        'el-card': true,
        'el-tag': true,
        'el-form': true,
        'el-form-item': true,
        'el-input': true,
        'el-button': true,
      },
    },
  })
}

describe('AccountSecurity view', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    changeMyPasswordApiMock.mockReset()
    logoutApiMock.mockReset()
    pushMock.mockReset()
    successMock.mockReset()
    warningMock.mockReset()
  })

  it('warns when required password fields are incomplete', async () => {
    const wrapper = mountView()

    await (wrapper.vm as unknown as { submitChange: () => Promise<void> }).submitChange()

    expect(warningMock).toHaveBeenCalledWith('请完整填写当前密码和新密码')
    expect(changeMyPasswordApiMock).not.toHaveBeenCalled()
  })

  it('warns when the new password is too short', async () => {
    const wrapper = mountView()
    const vm = wrapper.vm as unknown as {
      form: { current_password: string; new_password: string; confirm_password: string }
      submitChange: () => Promise<void>
    }
    vm.form.current_password = 'old-password'
    vm.form.new_password = 'short'
    vm.form.confirm_password = 'short'

    await vm.submitChange()

    expect(warningMock).toHaveBeenCalledWith('新密码至少需要 6 位')
    expect(changeMyPasswordApiMock).not.toHaveBeenCalled()
  })

  it('warns when password confirmation does not match', async () => {
    const wrapper = mountView()
    const vm = wrapper.vm as unknown as {
      form: { current_password: string; new_password: string; confirm_password: string }
      submitChange: () => Promise<void>
    }
    vm.form.current_password = 'old-password'
    vm.form.new_password = 'VeryStrongPassword!'
    vm.form.confirm_password = 'DifferentPassword!'

    await vm.submitChange()

    expect(warningMock).toHaveBeenCalledWith('两次输入的新密码不一致')
    expect(changeMyPasswordApiMock).not.toHaveBeenCalled()
  })

  it('changes password, clears forced-reset state and redirects to login', async () => {
    const authStore = useAuthStore()
    authStore.setSession({
      access_token: 'access-token',
      refresh_token: 'refresh-token',
      token_type: 'bearer',
      role: 'admin',
      must_change_password: true,
    }, 'admin')
    changeMyPasswordApiMock.mockResolvedValue({ success: true, data: null })
    logoutApiMock.mockResolvedValue({ success: true, message: 'ok', token_version: 2 })

    const wrapper = mountView()
    const vm = wrapper.vm as unknown as {
      form: { current_password: string; new_password: string; confirm_password: string }
      submitChange: () => Promise<void>
    }
    vm.form.current_password = 'OldPassword!123'
    vm.form.new_password = 'VeryStrongPassword!456'
    vm.form.confirm_password = 'VeryStrongPassword!456'

    await vm.submitChange()

    expect(changeMyPasswordApiMock).toHaveBeenCalledWith({
      current_password: 'OldPassword!123',
      new_password: 'VeryStrongPassword!456',
    })
    expect(logoutApiMock).toHaveBeenCalledTimes(1)
    expect(authStore.mustChangePassword).toBe(false)
    expect(authStore.token).toBeNull()
    expect(localStorage.getItem('must_change_password')).toBeNull()
    expect(successMock).toHaveBeenCalledWith('密码修改成功，请重新登录')
    expect(pushMock).toHaveBeenCalledWith('/login')
  })

  it('still logs out locally when remote logout fails', async () => {
    const authStore = useAuthStore()
    authStore.setSession({
      access_token: 'access-token',
      refresh_token: 'refresh-token',
      token_type: 'bearer',
      role: 'viewer',
      must_change_password: true,
    }, 'viewer')
    changeMyPasswordApiMock.mockResolvedValue({ success: true, data: null })
    logoutApiMock.mockRejectedValue(new Error('logout failed'))

    const wrapper = mountView()
    const vm = wrapper.vm as unknown as {
      form: { current_password: string; new_password: string; confirm_password: string }
      submitChange: () => Promise<void>
    }
    vm.form.current_password = 'OldPassword!123'
    vm.form.new_password = 'VeryStrongPassword!456'
    vm.form.confirm_password = 'VeryStrongPassword!456'

    await vm.submitChange()

    expect(authStore.token).toBeNull()
    expect(pushMock).toHaveBeenCalledWith('/login')
  })
})
