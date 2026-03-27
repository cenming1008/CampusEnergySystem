<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-code">
        404
      </div>
      <div class="error-title">
        页面未找到
      </div>
      <div class="error-description">
        您访问的页面不存在或已被移除
      </div>
      <el-button
        type="primary"
        size="large"
        @click="router.push('/')"
      >
        返回首页
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
}
.not-found-content {
  text-align: center;
}
.error-code {
  font-size: 120px;
  font-weight: 700;
  color: var(--el-color-primary);
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
