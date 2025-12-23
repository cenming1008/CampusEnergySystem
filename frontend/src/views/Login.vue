<script setup lang="ts">
    import { reactive, ref } from 'vue'
    import { useRouter } from 'vue-router'
    import { useAuthStore } from '@/stores/useAuthStore'
    import { loginApi } from '@/api/auth'
    import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
    import { User, Lock, Loading } from '@element-plus/icons-vue'
    
    const router = useRouter()
    const authStore = useAuthStore()
    
    // --- 状态定义 ---
    const formRef = ref<FormInstance>()
    const loading = ref(false)
    
    const loginForm = reactive({
      username: '',
      password: ''
    })
    
    // --- 表单验证规则 ---
    const loginRules = reactive<FormRules>({
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
    })
    
    // --- 登录动作 ---
    const handleLogin = async (formEl: FormInstance | undefined) => {
      if (!formEl) return
      
      // 1. 先校验表单
      await formEl.validate(async (valid) => {
        if (valid) {
          loading.value = true
          try {
            // 2. 构造 OAuth2 表单数据 (FormData 格式)
            const params = new URLSearchParams()
            params.append('username', loginForm.username)
            params.append('password', loginForm.password)
    
            // 3. 发送请求
            const res = await loginApi(params)
            
            // 4. 保存 Token 到 Pinia
            // 注意：后端返回结构是 { access_token, token_type }
            // 用户名直接用填写的即可
            authStore.setToken(res.access_token, loginForm.username)
            
            ElMessage.success('登录成功，欢迎回来！')
            
            // 5. 跳转到主页
            router.push('/')
            
          } catch (error: any) {
            // 错误已经在 request.ts 拦截器里弹窗了，这里只负责停止 loading
            console.error(error)
          } finally {
            loading.value = false
          }
        }
      })
    }
    </script>
    
    <template>
      <div class="login-container">
        <div class="login-box">
          <div class="header">
            <div class="logo-icon"><el-icon><Odometer /></el-icon></div>
            <h2>MINE EMS</h2>
            <p class="subtitle">煤矿综合能源管理系统 v2.0</p>
          </div>
    
          <el-form
            ref="formRef"
            :model="loginForm"
            :rules="loginRules"
            class="login-form"
            @keyup.enter="handleLogin(formRef)"
          >
            <el-form-item prop="username">
              <el-input 
                v-model="loginForm.username" 
                placeholder="请输入用户名" 
                :prefix-icon="User"
                size="large"
              />
            </el-form-item>
    
            <el-form-item prop="password">
              <el-input 
                v-model="loginForm.password" 
                type="password" 
                placeholder="请输入密码" 
                :prefix-icon="Lock"
                show-password
                size="large"
              />
            </el-form-item>
    
            <el-button 
              type="primary" 
              class="login-btn" 
              :loading="loading"
              size="large"
              @click="handleLogin(formRef)"
            >
              {{ loading ? '登 录 中...' : '立 即 登 录' }}
            </el-button>
            
            <div class="tips">
              <span>默认账号: admin</span>
              <span>默认密码: 123456</span>
            </div>
          </el-form>
        </div>
        
        <div class="copyright">
          © 2024 Intelligent Mine Energy System. All Rights Reserved.
        </div>
      </div>
    </template>
    
    <style scoped>
    /* 继承原项目的深色背景 */
    .login-container {
      height: 100vh;
      width: 100%;
      background-color: #0f172a; /* var(--bg-body) */
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      position: relative;
      overflow: hidden;
    }
    
    /* 增加一点背景装饰 */
    .login-container::before {
      content: '';
      position: absolute;
      width: 100%; height: 100%;
      background: radial-gradient(circle at 50% 30%, #1e293b 0%, #0f172a 70%);
      z-index: 0;
    }
    
    .login-box {
      width: 360px;
      padding: 40px;
      background: #1e293b; /* var(--bg-sidebar) */
      border-radius: 12px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
      border: 1px solid #334155; /* var(--border-color) */
      z-index: 1;
      transition: transform 0.3s;
    }
    
    .login-box:hover {
      transform: translateY(-5px);
      border-color: #3b82f6; /* var(--brand-color) */
    }
    
    .header {
      text-align: center;
      margin-bottom: 30px;
    }
    
    .logo-icon {
      font-size: 48px;
      color: #3b82f6;
      margin-bottom: 10px;
    }
    
    h2 {
      color: #fff;
      margin: 0;
      font-size: 24px;
      font-weight: 800;
      letter-spacing: 2px;
    }
    
    .subtitle {
      color: #64748b; /* var(--text-muted) */
      font-size: 13px;
      margin-top: 8px;
    }
    
    /* 覆盖 Element Input 样式以适配暗黑主题 */
    :deep(.el-input__wrapper) {
      background-color: #0f172a;
      box-shadow: 0 0 0 1px #334155 inset;
    }
    :deep(.el-input__wrapper.is-focus) {
      box-shadow: 0 0 0 1px #3b82f6 inset;
    }
    :deep(.el-input__inner) {
      color: #fff;
      height: 44px;
    }
    
    .login-btn {
      width: 100%;
      margin-top: 10px;
      font-weight: bold;
      letter-spacing: 2px;
      background-color: #3b82f6;
      border: none;
      height: 44px;
    }
    .login-btn:hover {
      background-color: #2563eb;
    }
    
    .tips {
      margin-top: 20px;
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: #475569;
    }
    
    .copyright {
      position: absolute;
      bottom: 30px;
      color: #334155;
      font-size: 12px;
      z-index: 1;
    }
    </style>