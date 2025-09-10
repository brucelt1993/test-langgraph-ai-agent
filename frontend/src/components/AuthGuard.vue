<template>
  <div>
    <!-- 认证通过时显示内容 -->
    <slot v-if="isAuthenticated" />
    
    <!-- 未认证时显示加载状态或重定向 -->
    <div v-else-if="isLoading" class="min-h-screen flex items-center justify-center">
      <div class="text-center space-y-4">
        <div class="loading-spinner w-8 h-8 mx-auto border-primary"></div>
        <p class="text-muted-foreground">验证登录状态...</p>
      </div>
    </div>
    
    <!-- 认证失败时的提示 -->
    <div v-else class="min-h-screen flex items-center justify-center">
      <div class="card max-w-md w-full">
        <div class="card-header text-center">
          <h1 class="card-title text-2xl">需要登录</h1>
          <p class="card-description">请登录后访问此页面</p>
        </div>
        <div class="card-content">
          <div class="flex flex-col space-y-3">
            <button
              class="btn btn-primary btn-md"
              @click="redirectToLogin"
            >
              前往登录
            </button>
            <button
              class="btn btn-outline btn-md"
              @click="redirectToHome"
            >
              返回首页
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Props
interface Props {
  requireAuth?: boolean
  redirectTo?: string
  fallbackComponent?: string
}

const props = withDefaults(defineProps<Props>(), {
  requireAuth: true,
  redirectTo: '/login',
  fallbackComponent: undefined
})

// 路由和状态
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 响应式状态
const isLoading = ref(true)

// 计算属性
const isAuthenticated = computed(() => {
  if (!props.requireAuth) {
    return true
  }
  return authStore.isAuthenticated
})

// 重定向到登录页
const redirectToLogin = () => {
  router.push({
    path: props.redirectTo,
    query: { redirect: route.fullPath }
  })
}

// 重定向到首页
const redirectToHome = () => {
  router.push('/')
}

// 初始化认证状态
onMounted(async () => {
  try {
    // 如果有token但没有用户信息，尝试初始化
    if (authStore.token && !authStore.user) {
      await authStore.initialize()
    }
  } catch (error) {
    console.error('初始化认证状态失败:', error)
    // 清除无效的认证信息
    authStore.clearAuth()
  } finally {
    isLoading.value = false
    
    // 如果需要认证但用户未登录，自动重定向
    if (props.requireAuth && !authStore.isAuthenticated) {
      redirectToLogin()
    }
  }
})
</script>

<style scoped>
.loading-spinner {
  border-color: currentColor;
  border-right-color: transparent;
}
</style>