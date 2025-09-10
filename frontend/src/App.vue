<template>
  <div id="app" class="min-h-screen bg-white">
    <!-- 调试信息 -->
    <div class="p-4 bg-red-100 text-red-800">
      <p>Debug: App组件已加载</p>
      <p>当前路由: {{ $route.path }}</p>
    </div>
    
    <RouterView />
    
    <!-- 通知容器暂时禁用
    <NotificationContainer />
    -->
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
// import NotificationContainer from '@/components/ui/NotificationContainer.vue'

// 初始化主题
onMounted(() => {
  // 检查本地存储的主题设置或系统偏好
  const theme = localStorage.getItem('theme') || 
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
  
  document.documentElement.classList.toggle('dark', theme === 'dark')
})
</script>