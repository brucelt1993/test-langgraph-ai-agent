<template>
  <div class="min-h-screen flex items-center justify-center bg-background p-4">
    <div class="text-center space-y-8">
      <!-- 404图标 -->
      <div class="relative">
        <h1 class="text-9xl font-bold text-muted-foreground/20 select-none">404</h1>
        <div class="absolute inset-0 flex items-center justify-center">
          <svg 
            class="w-24 h-24 text-primary animate-pulse" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              stroke-width="2" 
              d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h.01M15 8h.01M12 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
            />
          </svg>
        </div>
      </div>

      <!-- 错误信息 -->
      <div class="space-y-4">
        <h2 class="text-3xl font-bold">页面不存在</h2>
        <p class="text-lg text-muted-foreground max-w-md mx-auto">
          抱歉，您访问的页面不存在。可能是链接错误或页面已被移除。
        </p>
      </div>

      <!-- 操作按钮 -->
      <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
        <button
          class="btn btn-primary btn-lg"
          @click="goHome"
        >
          返回首页
        </button>
        
        <button
          class="btn btn-outline btn-lg"
          @click="goBack"
        >
          返回上页
        </button>
        
        <RouterLink
          v-if="!authStore.isAuthenticated"
          to="/login"
          class="btn btn-ghost btn-lg"
        >
          登录账户
        </RouterLink>
        
        <RouterLink
          v-else
          to="/chat"
          class="btn btn-ghost btn-lg"
        >
          开始聊天
        </RouterLink>
      </div>

      <!-- 建议链接 -->
      <div class="pt-8">
        <p class="text-sm text-muted-foreground mb-4">您可能想要访问：</p>
        <div class="flex flex-wrap justify-center gap-4">
          <RouterLink
            to="/"
            class="text-sm text-primary hover:underline"
          >
            首页
          </RouterLink>
          <RouterLink
            v-if="authStore.isAuthenticated"
            to="/chat"
            class="text-sm text-primary hover:underline"
          >
            聊天
          </RouterLink>
          <RouterLink
            v-if="authStore.isAuthenticated"
            to="/profile"
            class="text-sm text-primary hover:underline"
          >
            个人资料
          </RouterLink>
          <RouterLink
            v-if="!authStore.isAuthenticated"
            to="/register"
            class="text-sm text-primary hover:underline"
          >
            注册账户
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 返回首页
const goHome = () => {
  router.push('/')
}

// 返回上一页
const goBack = () => {
  // 如果有历史记录就返回，否则去首页
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/')
  }
}

// 设置页面标题
document.title = '页面不存在 - AI助手'
</script>

<style scoped>
/* 添加一些微妙的动画效果 */
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: .5;
  }
}

/* 响应式文字大小 */
@media (max-width: 640px) {
  h1 {
    font-size: 6rem;
  }
}
</style>