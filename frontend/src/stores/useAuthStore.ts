import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // 1. 状态：从 localStorage 初始化，保证刷新不掉线
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const username = ref<string | null>(localStorage.getItem('username'))

  // 2. 动作：登录成功，保存 Token
  function setToken(newToken: string, newUser: string) {
    token.value = newToken
    username.value = newUser
    localStorage.setItem('access_token', newToken)
    localStorage.setItem('username', newUser)
  }

  // 3. 动作：登出，清理 Token
  function logout() {
    token.value = null
    username.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')
  }

  return { token, username, setToken, logout }
})ss