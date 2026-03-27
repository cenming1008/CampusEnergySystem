<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  changeUserPassword,
  createUser,
  forceUserPasswordReset,
  getUsers,
  revokeUserSessions,
  unlockUser,
  updateUserRole,
  updateUserScope,
  updateUserStatus,
  type UserRecord,
} from '@/api/users'

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const passwordSaving = ref(false)
const users = ref<UserRecord[]>([])
const targetPasswordUser = ref<UserRecord | null>(null)

const form = reactive({
  username: '',
  password: '',
  role: 'viewer',
  location_scope: '',
  is_active: true,
})

const passwordForm = reactive({
  new_password: '',
})

const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await getUsers()
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  form.username = ''
  form.password = ''
  form.role = 'viewer'
  form.location_scope = ''
  form.is_active = true
  dialogVisible.value = true
}

const openPasswordDialog = (row: UserRecord) => {
  targetPasswordUser.value = row
  passwordForm.new_password = ''
  passwordDialogVisible.value = true
}

const submitCreate = async () => {
  saving.value = true
  try {
    await createUser({
      username: form.username,
      password: form.password,
      role: form.role,
      location_scope: form.location_scope || null,
      is_active: form.is_active,
    })
    ElMessage.success('用户创建成功')
    dialogVisible.value = false
    await loadUsers()
  } finally {
    saving.value = false
  }
}

const handleRoleChange = async (row: UserRecord, role: string) => {
  await updateUserRole(row.id, role)
  ElMessage.success('角色已更新')
  await loadUsers()
}

const handleStatusChange = async (row: UserRecord, is_active: boolean) => {
  await updateUserStatus(row.id, is_active)
  ElMessage.success('用户状态已更新')
  await loadUsers()
}

const handleScopeBlur = async (row: UserRecord) => {
  await updateUserScope(row.id, row.location_scope || null)
  ElMessage.success('位置范围已更新')
}

const handleUnlock = async (row: UserRecord) => {
  await unlockUser(row.id)
  ElMessage.success('账户已解锁')
  await loadUsers()
}

const handleRevoke = async (row: UserRecord) => {
  await revokeUserSessions(row.id)
  ElMessage.success('会话已强制失效')
}

const handleForceReset = async (row: UserRecord, mustChange: boolean) => {
  await forceUserPasswordReset(row.id, mustChange)
  ElMessage.success(mustChange ? '已要求用户下次登录改密' : '已取消强制改密')
  await loadUsers()
}

const handleChangePassword = async () => {
  if (!targetPasswordUser.value) return
  if (passwordForm.new_password.trim().length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }

  passwordSaving.value = true
  try {
    const response = await changeUserPassword(targetPasswordUser.value.id, passwordForm.new_password.trim())
    ElMessage.success(response.message || '密码已更新')
    passwordDialogVisible.value = false
    passwordForm.new_password = ''
  } finally {
    passwordSaving.value = false
  }
}

const onRoleSelect = (row: UserRecord, value: string | number | boolean) => {
  if (typeof value === 'string') {
    void handleRoleChange(row, value)
  }
}

const onStatusToggle = (row: UserRecord, value: string | number | boolean) => {
  if (typeof value === 'boolean') {
    void handleStatusChange(row, value)
  }
}

onMounted(loadUsers)
</script>

<template>
  <div class="page">
    <div class="toolbar">
      <div>
        <h2>用户管理</h2>
        <p>对齐后端 RBAC、锁定状态、位置范围和会话控制能力。</p>
      </div>
      <el-button
        type="primary"
        @click="openCreate"
      >
        新增用户
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="users"
      class="table"
    >
      <el-table-column
        prop="username"
        label="用户名"
        min-width="160"
      />
      <el-table-column
        label="角色"
        width="160"
      >
        <template #default="{ row }">
          <el-select
            :model-value="row.role"
            style="width: 130px"
            @change="onRoleSelect(row, $event)"
          >
            <el-option
              label="管理员"
              value="admin"
            />
            <el-option
              label="操作员"
              value="operator"
            />
            <el-option
              label="运维"
              value="maintainer"
            />
            <el-option
              label="只读"
              value="viewer"
            />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column
        label="位置范围"
        min-width="180"
      >
        <template #default="{ row }">
          <el-input
            v-model="row.location_scope"
            placeholder="例如 1,2,3"
            @blur="handleScopeBlur(row)"
          />
        </template>
      </el-table-column>
      <el-table-column
        label="启用"
        width="100"
      >
        <template #default="{ row }">
          <el-switch
            :model-value="row.is_active"
            @change="onStatusToggle(row, $event)"
          />
        </template>
      </el-table-column>
      <el-table-column
        label="锁定状态"
        width="180"
      >
        <template #default="{ row }">
          <div class="stack-cell">
            <span>{{ row.locked_until ? '已锁定' : '正常' }}</span>
            <small v-if="row.locked_until">{{ row.locked_until }}</small>
          </div>
        </template>
      </el-table-column>
      <el-table-column
        label="失败次数"
        width="100"
      >
        <template #default="{ row }">
          {{ row.failed_login_attempts }}
        </template>
      </el-table-column>
      <el-table-column
        label="操作"
        min-width="320"
        fixed="right"
      >
        <template #default="{ row }">
          <div class="actions">
            <el-button
              size="small"
              @click="handleUnlock(row)"
            >
              解锁
            </el-button>
            <el-button
              size="small"
              @click="handleRevoke(row)"
            >
              强制下线
            </el-button>
            <el-button
              size="small"
              type="info"
              @click="openPasswordDialog(row)"
            >
              重置密码
            </el-button>
            <el-button
              size="small"
              type="warning"
              @click="handleForceReset(row, !row.must_change_password)"
            >
              {{ row.must_change_password ? '取消强改' : '要求改密' }}
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      title="新增用户"
      width="520px"
    >
      <el-form label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="初始密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select
            v-model="form.role"
            style="width: 100%"
          >
            <el-option
              label="管理员"
              value="admin"
            />
            <el-option
              label="操作员"
              value="operator"
            />
            <el-option
              label="运维"
              value="maintainer"
            />
            <el-option
              label="只读"
              value="viewer"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="位置范围">
          <el-input
            v-model="form.location_scope"
            placeholder="例如 1,2,3，留空表示不限制"
          />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="submitCreate"
        >
          创建
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="passwordDialogVisible"
      title="管理员修改密码"
      width="460px"
    >
      <el-form label-position="top">
        <el-form-item label="目标用户">
          <el-input
            :model-value="targetPasswordUser?.username || ''"
            disabled
          />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            show-password
            placeholder="至少 6 位"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="passwordSaving"
          @click="handleChangePassword"
        >
          更新密码
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page {
  display: grid;
  gap: 16px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.toolbar h2, .toolbar p {
  margin: 0;
}

.toolbar p {
  color: #94a3b8;
  margin-top: 6px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stack-cell {
  display: flex;
  flex-direction: column;
}

.stack-cell small {
  color: #94a3b8;
}
</style>
