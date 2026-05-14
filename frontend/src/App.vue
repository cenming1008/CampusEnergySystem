<script setup lang="ts">
// 根组件逻辑很简单，主要是为了应用全局样式
</script>

<template>
  <router-view />
</template>

<style>
/* 🌍 全局样式定义 (复用原项目的配色变量) */
:root {
  --bg-body: #0f172a;       /* 整体背景深色 */
  --bg-sidebar: #1e293b;    /* 侧边栏/卡片背景 */
  --border-color: #334155;  /* 边框色 */

  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --brand-color: #3b82f6;   /* 主品牌色 */
  --danger-color: #ef4444;  /* 报警红 */
  --success-color: #10b981; /* 正常绿 */

  /* 设计 token：标签色 / 分隔线 / 触控目标 / 最小字号（WCAG AA） */
  --text-label: #8aa0bf;
  --divider: rgba(148, 163, 184, 0.12);
  --touch-target: 24px;
  --font-caption: 12px;
}

html, body, #app {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  font-family: 'Inter', sans-serif;
  background-color: var(--bg-body);
  color: var(--text-primary);
  overflow: hidden; /* 防止双重滚动条 */
  box-sizing: border-box;
}

*, *::before, *::after {
  box-sizing: border-box;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-body);
}

::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}
</style>
