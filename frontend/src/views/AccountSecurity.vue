<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { changeMyPasswordApi, logoutApi } from '@/api/auth'
import { useAuthStore } from '@/stores/useAuthStore'
import { useSocketStore } from '@/stores/useSocketStore'

const router = useRouter()
const authStore = useAuthStore()
const socketStore = useSocketStore()
const submitting = ref(false)

const form = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const submitChange = async () => {
  if (!form.current_password || !form.new_password) {
    ElMessage.warning('请完整填写当前密码和新密码')
    return
  }
  if (form.new_password.length < 12) {
    ElMessage.warning('新密码至少需要 12 位')
    return
  }
  if (form.new_password !== form.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }

  submitting.value = true
  try {
    await changeMyPasswordApi({
      current_password: form.current_password,
      new_password: form.new_password,
    })
    authStore.mustChangePassword = false
    localStorage.setItem('must_change_password', 'false')
    ElMessage.success('密码修改成功，请重新登录')
    try {
      await logoutApi()
    } catch (_error) {
      // no-op
    }
    socketStore.disconnect()
    authStore.logout()
    await router.push('/login')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="security-page">
    <el-card
      class="security-card"
      shadow="never"
    >
      <template #header>
        <div class="header">
          <div>
            <h2>账户安全</h2>
            <p>当前后端已启用首次登录强制改密，请先完成密码更新。</p>
          </div>
          <el-tag
            v-if="authStore.mustChangePassword"
            type="warning"
            effect="dark"
          >
            必须处理
          </el-tag>
        </div>
      </template>

      <el-form label-position="top">
        <el-form-item label="当前密码">
          <el-input
            v-model="form.current_password"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input
            v-model="form.new_password"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input
            v-model="form.confirm_password"
            type="password"
            show-password
          />
        </el-form-item>
        <div class="actions">
          <el-button
            type="primary"
            :loading="submitting"
            @click="submitChange"
          >
            保存并重新登录
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.security-page {
  max-width: 760px;
}

.security-card {
  background: #111a28;
  border: 1px solid #243244;
  color: #dbe7f3;
}

.header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
}

.header h2 {
  margin: 0 0 8px;
}

.header p {
  margin: 0;
  color: #94a3b8;
}

.actions {
  display: flex;
  justify-content: flex-end;
}
</style>
