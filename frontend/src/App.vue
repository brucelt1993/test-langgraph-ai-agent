<template>
  <div id="app" class="min-h-screen bg-white">
    <RouterView />
    
    <!-- 通知容器暂时禁用
    <NotificationContainer />
    -->
    
    <!-- 调试组件 -->
    <AuthDebug v-if="isDevelopment" />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted, computed } from 'vue'
import AuthDebug from '@/components/AuthDebug.vue'
// import NotificationContainer from '@/components/ui/NotificationContainer.vue'

// 检查是否为开发环境
const isDevelopment = computed(() => import.meta.env.DEV)

// 初始化主题
onMounted(() => {
  // 检查本地存储的主题设置或系统偏好
  const theme = localStorage.getItem('theme') || 
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
  
  document.documentElement.classList.toggle('dark', theme === 'dark')
})
</script>