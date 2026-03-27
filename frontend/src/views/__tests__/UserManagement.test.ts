import { beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import UserManagement from '../UserManagement.vue'

const {
  getUsersMock,
  createUserMock,
  changeUserPasswordMock,
  forceUserPasswordResetMock,
  revokeUserSessionsMock,
  unlockUserMock,
  updateUserRoleMock,
  updateUserScopeMock,
  updateUserStatusMock,
  successMock,
  warningMock,
  errorMock,
} = vi.hoisted(() => ({
  getUsersMock: vi.fn(),
  createUserMock: vi.fn(),
  changeUserPasswordMock: vi.fn(),
  forceUserPasswordResetMock: vi.fn(),
  revokeUserSessionsMock: vi.fn(),
  unlockUserMock: vi.fn(),
  updateUserRoleMock: vi.fn(),
  updateUserScopeMock: vi.fn(),
  updateUserStatusMock: vi.fn(),
  successMock: vi.fn(),
  warningMock: vi.fn(),
  errorMock: vi.fn(),
}))

vi.mock('@/api/users', () => ({
  getUsers: getUsersMock,
  createUser: createUserMock,
  changeUserPassword: changeUserPasswordMock,
  forceUserPasswordReset: forceUserPasswordResetMock,
  revokeUserSessions: revokeUserSessionsMock,
  unlockUser: unlockUserMock,
  updateUserRole: updateUserRoleMock,
  updateUserScope: updateUserScopeMock,
  updateUserStatus: updateUserStatusMock,
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

function mountView() {
  return shallowMount(UserManagement, {
    global: {
      stubs: {
        'el-button': true,
        'el-dialog': true,
        'el-form': true,
        'el-form-item': true,
        'el-input': true,
        'el-select': true,
        'el-option': true,
        'el-switch': true,
        'el-table': true,
        'el-table-column': true,
      },
    },
  })
}

async function flushAsync() {
  await Promise.resolve()
  await Promise.resolve()
}

describe('UserManagement view', () => {
  beforeEach(() => {
    getUsersMock.mockReset()
    createUserMock.mockReset()
    changeUserPasswordMock.mockReset()
    forceUserPasswordResetMock.mockReset()
    revokeUserSessionsMock.mockReset()
    unlockUserMock.mockReset()
    updateUserRoleMock.mockReset()
    updateUserScopeMock.mockReset()
    updateUserStatusMock.mockReset()
    successMock.mockReset()
    warningMock.mockReset()
    errorMock.mockReset()
  })

  it('loads users on mount', async () => {
    getUsersMock.mockResolvedValue([
      {
        id: 1,
        username: 'admin',
        role: 'admin',
        location_scope: null,
        is_active: true,
        must_change_password: false,
        failed_login_attempts: 0,
        locked_until: null,
      },
    ])

    const wrapper = mountView()
    await flushAsync()

    expect(getUsersMock).toHaveBeenCalledTimes(1)
    expect((wrapper.vm as unknown as { users: Array<{ username: string }> }).users).toHaveLength(1)
    expect((wrapper.vm as unknown as { users: Array<{ username: string }> }).users[0].username).toBe('admin')
  })

  it('creates a user and reloads the list', async () => {
    getUsersMock.mockResolvedValue([])
    createUserMock.mockResolvedValue({
      id: 2,
      username: 'operator',
    })

    const wrapper = mountView()
    await flushAsync()

    const vm = wrapper.vm as unknown as {
      form: {
        username: string
        password: string
        role: string
        location_scope: string
        is_active: boolean
      }
      dialogVisible: boolean
      submitCreate: () => Promise<void>
    }
    vm.form.username = 'operator'
    vm.form.password = 'StrongPassword!123'
    vm.form.role = 'operator'
    vm.form.location_scope = ''
    vm.form.is_active = true

    getUsersMock.mockResolvedValueOnce([]).mockResolvedValueOnce([
      {
        id: 2,
        username: 'operator',
        role: 'operator',
        location_scope: null,
        is_active: true,
        must_change_password: false,
        failed_login_attempts: 0,
        locked_until: null,
      },
    ])

    await vm.submitCreate()

    expect(createUserMock).toHaveBeenCalledWith({
      username: 'operator',
      password: 'StrongPassword!123',
      role: 'operator',
      location_scope: null,
      is_active: true,
    })
    expect(successMock).toHaveBeenCalledWith('用户创建成功')
    expect(vm.dialogVisible).toBe(false)
    expect(getUsersMock).toHaveBeenCalledTimes(2)
  })

  it('warns when admin password reset is shorter than 6 chars', async () => {
    getUsersMock.mockResolvedValue([])
    const wrapper = mountView()
    await flushAsync()

    const vm = wrapper.vm as unknown as {
      targetPasswordUser: { id: number; username: string } | null
      passwordForm: { new_password: string }
      handleChangePassword: () => Promise<void>
    }
    vm.targetPasswordUser = { id: 3, username: 'viewer' }
    vm.passwordForm.new_password = 'short'

    await vm.handleChangePassword()

    expect(warningMock).toHaveBeenCalledWith('新密码至少 6 位')
    expect(changeUserPasswordMock).not.toHaveBeenCalled()
  })

  it('updates a user password and closes the dialog', async () => {
    getUsersMock.mockResolvedValue([])
    changeUserPasswordMock.mockResolvedValue({ success: true, message: '密码已更新' })

    const wrapper = mountView()
    await flushAsync()

    const vm = wrapper.vm as unknown as {
      targetPasswordUser: { id: number; username: string } | null
      passwordForm: { new_password: string }
      passwordDialogVisible: boolean
      handleChangePassword: () => Promise<void>
    }
    vm.targetPasswordUser = { id: 3, username: 'viewer' }
    vm.passwordDialogVisible = true
    vm.passwordForm.new_password = 'VeryStrongPassword!'

    await vm.handleChangePassword()

    expect(changeUserPasswordMock).toHaveBeenCalledWith(3, 'VeryStrongPassword!')
    expect(successMock).toHaveBeenCalledWith('密码已更新')
    expect(vm.passwordDialogVisible).toBe(false)
    expect(vm.passwordForm.new_password).toBe('')
  })

  it('can unlock and force password reset for a user', async () => {
    const user = {
      id: 5,
      username: 'maintainer',
      role: 'maintainer',
      location_scope: '1,2',
      is_active: true,
      must_change_password: false,
      failed_login_attempts: 2,
      locked_until: '2026-03-26T12:00:00',
    }
    getUsersMock.mockResolvedValue([user])
    unlockUserMock.mockResolvedValue(user)
    forceUserPasswordResetMock.mockResolvedValue({ ...user, must_change_password: true })

    const wrapper = mountView()
    await flushAsync()
    const vm = wrapper.vm as unknown as {
      handleUnlock: (row: typeof user) => Promise<void>
      handleForceReset: (row: typeof user, mustChange: boolean) => Promise<void>
    }

    await vm.handleUnlock(user)
    await vm.handleForceReset(user, true)

    expect(unlockUserMock).toHaveBeenCalledWith(5)
    expect(forceUserPasswordResetMock).toHaveBeenCalledWith(5, true)
    expect(successMock).toHaveBeenCalledWith('账户已解锁')
    expect(successMock).toHaveBeenCalledWith('已要求用户下次登录改密')
  })
})
