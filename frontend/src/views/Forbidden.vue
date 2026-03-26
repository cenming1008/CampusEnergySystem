<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="forbidden-container">
    <div class="forbidden-content">
      <div class="error-code">403</div>
      <div class="error-title">无访问权限</div>
      <div class="error-description">
        您的角色无权访问该页面，如需权限请联系管理员
      </div>
      <el-button type="primary" size="large" @click="router.push('/')">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.forbidden-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
}
.forbidden-content {
  text-align: center;
}
.error-code {
  font-size: 120px;
  font-weight: 700;
  color: var(--el-color-warning);
  line-height: 1;
  opacity: 0.8;
}
.error-title {
  font-size: 24px;
  color: var(--el-text-color-primary);
  margin: 16px 0 8px;
}
.error-description {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 32px;
}
</style>
