<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowRight,
  Key,
  Lightning,
  Lock,
  Opportunity,
  User,
  Warning,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/useAuthStore'
import { loginApi } from '@/api/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const showPassword = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const currentYear = computed(() => new Date().getFullYear())

const handleLogin = async () => {
  if (!loginForm.username.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }

  if (!loginForm.password.trim()) {
    ElMessage.warning('请输入密码')
    return
  }

  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('username', loginForm.username)
    params.append('password', loginForm.password)

    const res = await loginApi(params)
    authStore.setSession(res, loginForm.username)

    ElMessage.success('登录成功，欢迎进入系统')
    router.push(res.must_change_password ? '/account/security' : '/')
  } catch {
    // 登录失败由 axios 拦截器统一提示
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="stitch-login-page">
    <section class="visual-panel">
      <div class="visual-grid" />
      <div class="visual-glow visual-glow-primary" />
      <div class="visual-glow visual-glow-secondary" />

      <div class="visual-content">
        <div class="status-chip">
          <span class="status-dot" />
          <span>运行状态：正常</span>
        </div>

        <div class="hero-copy">
          <h1>矿山运营 <span>卓越中心</span></h1>
          <p>
            通过一体化能源调度、设备健康监测和实时告警体系，支撑高风险工业现场的稳定运行与精细化管理。
          </p>
        </div>

        <div class="dashboard-grid">
          <article class="dashboard-card card-primary">
            <div class="card-head">
              <span>能源调度</span>
              <el-icon><Lightning /></el-icon>
            </div>

            <div class="energy-body">
              <div class="metric-line">
                <strong>1,248.5</strong>
                <span>兆瓦 / 峰值负载</span>
              </div>

              <div class="energy-chart">
                <div
                  v-for="height in [42, 58, 50, 78, 68, 46, 90, 57]"
                  :key="height"
                  class="energy-bar"
                  :style="{ height: `${height}%` }"
                />
              </div>
            </div>
          </article>

          <article class="dashboard-card card-alert">
            <div class="card-head">
              <span>健康警报</span>
              <el-icon><Warning /></el-icon>
            </div>

            <div class="alert-list">
              <div class="alert-item active">
                <p>临界温度</p>
                <span>7-G 区 04 号挖掘机</span>
              </div>
              <div class="alert-item">
                <p>压力下降</p>
                <span>B-12 传送带连接</span>
              </div>
            </div>
          </article>

          <article class="dashboard-card card-fleet">
            <div class="card-head">
              <span>车队负载</span>
              <el-icon><Opportunity /></el-icon>
            </div>

            <div class="fleet-body">
              <strong>84%</strong>
              <span>活跃产能</span>
            </div>
          </article>

          <article class="dashboard-card card-efficiency">
            <div class="efficiency-ring">
              <span>92.4</span>
            </div>
            <div class="efficiency-copy">
              <p>系统效率</p>
              <span>检测到 1-5 区的最佳吞吐量。</span>
            </div>
          </article>
        </div>
      </div>
    </section>

    <main class="auth-panel-wrap">
      <div class="mobile-brand">
        <div class="brand-mark">
          <el-icon><Lightning /></el-icon>
        </div>
        <span>Kinetic Command</span>
      </div>

      <div class="auth-panel">
        <div class="desktop-brand">
          <div class="brand-mark">
            <el-icon><Lightning /></el-icon>
          </div>
          <span>Kinetic Command</span>
        </div>

        <div class="auth-copy">
          <h2>访问终端</h2>
          <p>仅限授权工业人员。安全访问会话。</p>
        </div>

        <form
          class="auth-form"
          @submit.prevent="handleLogin"
        >
          <div class="field-group">
            <label for="username">用户名</label>
            <div class="input-shell">
              <el-icon><User /></el-icon>
              <input
                id="username"
                v-model="loginForm.username"
                autocomplete="username"
                placeholder="输入操作员 ID"
                type="text"
              >
            </div>
          </div>

          <div class="field-group">
            <div class="field-meta">
              <label for="password">密码</label>
              <button
                class="forgot-link"
                type="button"
              >
                忘记了？
              </button>
            </div>

            <div class="input-shell">
              <el-icon><Lock /></el-icon>
              <input
                id="password"
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder=""
              >
              <button
                class="visibility-btn"
                type="button"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>

          <button
            class="submit-btn"
            type="submit"
          >
            <span>{{ loading ? '建立连接中...' : '建立连接' }}</span>
            <el-icon class="submit-icon">
              <ArrowRight />
            </el-icon>
          </button>

          <div class="divider">
            <span>二次验证</span>
          </div>

          <button
            class="card-login-btn"
            type="button"
          >
            <el-icon><Key /></el-icon>
            <span>使用智能卡登录</span>
          </button>
        </form>

        <div class="panel-footer">
          <div class="footer-meta">
            <span class="footer-indicator" />
            <span>V4.8.2-稳定版</span>
          </div>
          <span>工业能源控制入口</span>
        </div>

        <p class="panel-disclaimer">
          © {{ currentYear }} 工业能源系统。保留所有权利。机密基础设施。未经授权的访问将受到严格监控，并依照相关行业规范进行处置。
        </p>
      </div>

      <div class="corner-glow" />
    </main>

    <footer class="page-footer">
      <span>© {{ currentYear }} Industrial Energy Systems. All rights reserved. Confidential Infrastructure.</span>
      <div class="footer-links">
        <a href="javascript:void(0)">安全策略</a>
        <a href="javascript:void(0)">操作条款</a>
      </div>
    </footer>
  </div>
</template>

<style>
.stitch-login-page {
  min-height: 100vh;
  display: flex;
  position: relative;
  overflow: hidden;
  background: #0e131f;
  color: #dee2f3;
}

.visual-panel {
  position: relative;
  width: 60%;
  padding: 3rem;
  display: none;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #090e19;
  border-right: 1px solid rgba(60, 74, 70, 0.2);
}

.visual-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(68, 221, 193, 0.07) 1px, transparent 1px);
  background-size: 40px 40px;
}

.visual-glow {
  position: absolute;
  border-radius: 999px;
  pointer-events: none;
  filter: blur(120px);
}

.visual-glow-primary {
  top: -10%;
  left: -10%;
  width: 37.5rem;
  height: 37.5rem;
  background: rgba(68, 221, 193, 0.08);
}

.visual-glow-secondary {
  right: -5%;
  bottom: -5%;
  width: 25rem;
  height: 25rem;
  background: rgba(255, 183, 120, 0.08);
}

.visual-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 68rem;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 0.875rem;
  background: rgba(26, 31, 43, 0.85);
  border-left: 2px solid #44ddc1;
  color: #44ddc1;
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.status-dot {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 999px;
  background: #44ddc1;
  box-shadow: 0 0 12px rgba(68, 221, 193, 0.7);
}

.hero-copy {
  margin-top: 1.75rem;
  margin-bottom: 3rem;
}

.hero-copy h1 {
  margin: 0;
  font-size: 4rem;
  line-height: 1.05;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.hero-copy h1 span {
  color: #44ddc1;
}

.hero-copy p {
  max-width: 40rem;
  margin-top: 1rem;
  color: #bbcac4;
  font-size: 1.1rem;
  line-height: 1.7;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 1.25rem;
  height: 26.25rem;
}

.dashboard-card {
  position: relative;
  overflow: hidden;
  border-radius: 0.35rem;
  background: #1a1f2b;
  transition: background-color 0.25s ease, transform 0.25s ease;
}

.dashboard-card:hover {
  transform: translateY(-2px);
  background: #252a36;
}

.dashboard-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
}

.card-primary {
  grid-column: span 4;
  padding: 1.5rem;
}

.card-primary::before {
  background: #44ddc1;
}

.card-alert {
  grid-column: span 2;
  padding: 1.5rem;
}

.card-alert::before {
  background: #ffb778;
}

.card-fleet {
  grid-column: span 2;
  padding: 1.5rem;
  background:
    linear-gradient(180deg, rgba(26, 31, 43, 0.96), rgba(26, 31, 43, 0.88)),
    radial-gradient(circle at top right, rgba(68, 221, 193, 0.1), transparent 40%);
}

.card-fleet::before {
  background: rgba(255, 255, 255, 0.14);
}

.card-efficiency {
  grid-column: span 4;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
  background: #252a36;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  color: #bbcac4;
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.card-head .el-icon {
  font-size: 1.2rem;
}

.card-primary .card-head .el-icon {
  color: #44ddc1;
}

.card-alert .card-head .el-icon {
  color: #ffb778;
}

.energy-body {
  height: calc(100% - 2rem);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.metric-line {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.metric-line strong {
  font-size: 3rem;
  font-weight: 800;
}

.metric-line span {
  color: #bbcac4;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.energy-chart {
  height: 6rem;
  margin-top: 1.1rem;
  padding: 0 0.5rem;
  display: flex;
  align-items: flex-end;
  gap: 0.18rem;
  background: rgba(9, 14, 25, 0.5);
}

.energy-bar {
  flex: 1;
  background: linear-gradient(180deg, rgba(104, 250, 221, 0.95), rgba(68, 221, 193, 0.3));
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.alert-item {
  padding: 0.85rem;
  border-radius: 0.25rem;
  background: rgba(9, 14, 25, 0.55);
}

.alert-item.active {
  border-left: 2px solid #ffb778;
  background: rgba(48, 53, 65, 0.75);
}

.alert-item p {
  margin: 0 0 0.35rem;
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.alert-item.active p {
  color: #ffb778;
}

.alert-item span {
  color: #dee2f3;
  font-size: 0.78rem;
}

.fleet-body {
  position: absolute;
  left: 1.5rem;
  right: 1.5rem;
  bottom: 1.5rem;
}

.fleet-body strong {
  display: block;
  font-size: 2rem;
  font-weight: 800;
}

.fleet-body span {
  color: #bbcac4;
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.efficiency-ring {
  width: 6rem;
  height: 6rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  border: 4px solid rgba(68, 221, 193, 0.2);
  box-shadow: inset 0 0 0 3px rgba(68, 221, 193, 0.12);
  position: relative;
}

.efficiency-ring::before {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 999px;
  border-top: 4px solid #44ddc1;
  animation: spin 4s linear infinite;
}

.efficiency-ring span {
  color: #44ddc1;
  font-size: 1.35rem;
  font-weight: 800;
}

.efficiency-copy p {
  margin: 0 0 0.45rem;
  color: #bbcac4;
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.efficiency-copy span {
  font-size: 0.9rem;
  color: #dee2f3;
}

.auth-panel-wrap {
  width: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #1a1f2b;
}

.mobile-brand,
.desktop-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.mobile-brand {
  position: absolute;
  left: 2rem;
  top: 2rem;
}

.desktop-brand {
  margin-bottom: 2rem;
}

.brand-mark {
  width: 2.5rem;
  height: 2.5rem;
  display: grid;
  place-items: center;
  border-radius: 0.25rem;
  background: #00bfa5;
  color: #00382f;
  font-size: 1.35rem;
}

.mobile-brand span,
.desktop-brand span {
  color: #44ddc1;
  font-size: 1.65rem;
  font-weight: 900;
  letter-spacing: -0.04em;
  text-transform: uppercase;
}

.mobile-brand {
  display: flex;
}

.desktop-brand {
  display: none;
}

.auth-panel {
  width: 100%;
  max-width: 30rem;
  position: relative;
  z-index: 1;
}

.auth-copy h2 {
  margin: 0;
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.auth-copy p {
  margin: 0.65rem 0 0;
  color: #bbcac4;
  font-size: 0.92rem;
}

.auth-form {
  margin-top: 2.5rem;
}

.field-group + .field-group {
  margin-top: 1.5rem;
}

.field-group label {
  display: block;
  margin-bottom: 0.6rem;
  color: #bbcac4;
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.field-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.forgot-link {
  border: none;
  background: transparent;
  color: #ffb778;
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  cursor: pointer;
}

.input-shell {
  height: 3.6rem;
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0 1rem;
  border: 1px solid rgba(60, 74, 70, 0.35);
  background: #090e19;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.input-shell:focus-within {
  border-color: #44ddc1;
}

.input-shell .el-icon {
  color: #85948f;
  font-size: 1.05rem;
}

.input-shell input {
  flex: 1;
  width: 100%;
  margin: 0;
  padding: 0;
  border: none;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
  background: transparent;
  color: #dee2f3;
  font-size: 0.92rem;
  box-shadow: none;
}

.input-shell input::placeholder {
  color: #6e7d89;
}

.input-shell input:-webkit-autofill,
.input-shell input:-webkit-autofill:hover,
.input-shell input:-webkit-autofill:focus,
.input-shell input:-webkit-autofill:active {
  -webkit-text-fill-color: #dee2f3;
  caret-color: #dee2f3;
  box-shadow: 0 0 0 1000px #090e19 inset;
  -webkit-box-shadow: 0 0 0 1000px #090e19 inset;
  transition: background-color 9999s ease-out 0s;
}

.visibility-btn {
  border: none;
  background: transparent;
  color: #85948f;
  font-size: 0.78rem;
  cursor: pointer;
}

.submit-btn,
.card-login-btn {
  width: 100%;
  min-height: 3.65rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: transform 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
}

.submit-btn {
  margin-top: 2rem;
  border: none;
  background: #00bfa5;
  color: #00382f;
  font-size: 1rem;
  font-weight: 800;
  box-shadow: 0 12px 24px rgba(0, 191, 165, 0.15);
}

.submit-btn:hover {
  transform: translateY(-1px);
  background: #14ccb4;
}

.submit-icon {
  font-size: 1.1rem;
}

.divider {
  margin: 1.25rem 0;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(60, 74, 70, 0.35);
}

.divider span {
  color: #bbcac4;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.card-login-btn {
  border: 1px solid rgba(133, 148, 143, 0.4);
  background: transparent;
  color: #dee2f3;
  font-size: 0.8rem;
  font-weight: 700;
}

.card-login-btn:hover {
  background: rgba(48, 53, 65, 0.5);
}

.panel-footer {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(60, 74, 70, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  color: #bbcac4;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.footer-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.footer-indicator {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 999px;
  background: #44ddc1;
}

.panel-disclaimer {
  margin-top: 1rem;
  color: #85948f;
  font-size: 0.62rem;
  line-height: 1.8;
  text-align: center;
}

.corner-glow {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 16rem;
  height: 16rem;
  background: rgba(255, 183, 120, 0.06);
  filter: blur(100px);
  pointer-events: none;
}

.page-footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 3rem;
  color: #bbcac4;
  font-size: 0.62rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  pointer-events: none;
}

.footer-links {
  display: flex;
  gap: 1.5rem;
  pointer-events: auto;
}

.footer-links a {
  color: #bbcac4;
  text-decoration: none;
}

.footer-links a:hover {
  color: #fff;
}

@media (min-width: 1024px) {
  .visual-panel {
    display: flex;
  }

  .auth-panel-wrap {
    width: 40%;
  }

  .mobile-brand {
    display: none;
  }

  .desktop-brand {
    display: flex;
  }
}

@media (max-width: 1023px) {
  .page-footer {
    position: static;
    flex-direction: column;
    gap: 0.75rem;
    padding: 1.25rem 1.25rem 1.75rem;
    text-align: center;
  }

  .stitch-login-page {
    display: block;
  }

  .auth-panel-wrap {
    min-height: 100vh;
    padding-top: 6rem;
    padding-bottom: 2rem;
  }
}

@media (max-width: 640px) {
  .auth-panel-wrap {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .mobile-brand {
    left: 1rem;
    top: 1rem;
  }

  .mobile-brand span,
  .desktop-brand span {
    font-size: 1.2rem;
  }

  .auth-copy h2 {
    font-size: 1.6rem;
  }

  .panel-footer {
    flex-direction: column;
    align-items: flex-start;
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
