<template>
  <div class="min-h-screen flex items-center justify-center bg-background p-4">
    <div class="card w-full max-w-md">
      <div class="card-header text-center">
        <h1 class="card-title text-3xl font-bold">AI助手</h1>
        <p class="card-description">登录到您的账户</p>
      </div>
      
      <div class="card-content space-y-4">
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- 用户名/邮箱输入 -->
          <div class="space-y-2">
            <label for="username" class="text-sm font-medium leading-none">
              用户名或邮箱
            </label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              class="input"
              placeholder="请输入用户名或邮箱"
              :disabled="isLoading"
              required
            />
            <div v-if="errors.username" class="text-sm text-destructive">
              {{ errors.username }}
            </div>
          </div>

          <!-- 密码输入 -->
          <div class="space-y-2">
            <label for="password" class="text-sm font-medium leading-none">
              密码
            </label>
            <div class="relative">
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                class="input pr-10"
                placeholder="请输入密码"
                :disabled="isLoading"
                required
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 pr-3 flex items-center"
                @click="togglePassword"
                :disabled="isLoading"
              >
                <component 
                  :is="showPassword ? EyeOffIcon : EyeIcon" 
                  class="h-4 w-4 text-muted-foreground" 
                />
              </button>
            </div>
            <div v-if="errors.password" class="text-sm text-destructive">
              {{ errors.password }}
            </div>
          </div>

          <!-- 记住登录状态 -->
          <div class="flex items-center space-x-2">
            <input
              id="remember"
              v-model="form.rememberMe"
              type="checkbox"
              class="h-4 w-4 rounded border-input"
              :disabled="isLoading"
            />
            <label for="remember" class="text-sm font-medium leading-none">
              记住登录状态
            </label>
          </div>

          <!-- 错误提示 -->
          <div v-if="submitError" class="p-3 rounded-md bg-destructive/10 border border-destructive/20">
            <p class="text-sm text-destructive">{{ submitError }}</p>
          </div>

          <!-- 登录按钮 -->
          <button
            type="submit"
            class="btn btn-primary btn-md w-full"
            :disabled="isLoading || !isFormValid"
          >
            <div v-if="isLoading" class="loading-spinner w-4 h-4 mr-2"></div>
            {{ isLoading ? '登录中...' : '登录' }}
          </button>
        </form>

        <!-- 分割线 -->
        <div class="relative">
          <div class="absolute inset-0 flex items-center">
            <span class="w-full border-t border-border" />
          </div>
          <div class="relative flex justify-center text-xs uppercase">
            <span class="bg-background px-2 text-muted-foreground">或</span>
          </div>
        </div>

        <!-- 注册链接 -->
        <div class="text-center">
          <p class="text-sm text-muted-foreground">
            还没有账户？
            <RouterLink
              to="/register"
              class="font-medium text-primary hover:underline"
            >
              立即注册
            </RouterLink>
          </p>
        </div>

        <!-- 忘记密码链接 -->
        <div class="text-center">
          <a
            href="#"
            class="text-sm text-muted-foreground hover:text-primary hover:underline"
            @click="handleForgotPassword"
          >
            忘记密码？
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { RouterLink } from 'vue-router'
import { EyeIcon, EyeOffIcon } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useNotification } from '@/composables/useNotification'

// 路由和状态
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { showError, showSuccess } = useNotification()

// 响应式状态
const showPassword = ref(false)
const isLoading = ref(false)
const submitError = ref('')

// 表单数据
const form = reactive({
  username: '',
  password: '',
  rememberMe: false
})

// 表单验证错误
const errors = reactive({
  username: '',
  password: ''
})

// 计算属性
const isFormValid = computed(() => {
  return form.username.trim().length > 0 && 
         form.password.length >= 6 &&
         !errors.username && 
         !errors.password
})

// 切换密码显示
const togglePassword = () => {
  showPassword.value = !showPassword.value
}

// 验证表单
const validateForm = () => {
  let isValid = true
  
  // 重置错误
  errors.username = ''
  errors.password = ''
  
  // 验证用户名
  if (!form.username.trim()) {
    errors.username = '请输入用户名或邮箱'
    isValid = false
  } else if (form.username.length < 3) {
    errors.username = '用户名至少3个字符'
    isValid = false
  }
  
  // 验证密码
  if (!form.password) {
    errors.password = '请输入密码'
    isValid = false
  } else if (form.password.length < 6) {
    errors.password = '密码至少6个字符'
    isValid = false
  }
  
  return isValid
}

// 处理表单提交
const handleSubmit = async () => {
  if (!validateForm() || isLoading.value) {
    return
  }

  isLoading.value = true
  submitError.value = ''

  try {
    await authStore.login({
      username: form.username.trim(),
      password: form.password
    })

    // 登录成功
    showSuccess('登录成功，欢迎回来！')
    
    // 跳转到原来的页面或首页
    const redirectTo = route.query.redirect as string || '/'
    
    // 确保状态更新后再跳转
    await nextTick()
    await router.push(redirectTo)
    
  } catch (error: any) {
    console.error('登录失败:', error)
    
    // 使用通知系统显示错误
    let errorMessage = '登录失败，请稍后重试'
    
    if (error.message) {
      errorMessage = error.message
    } else if (error.detail) {
      errorMessage = error.detail
    }
    
    // 显示错误通知
    showError(errorMessage, '登录失败')
    
    // 同时保留本地错误显示作为备选
    submitError.value = errorMessage
  } finally {
    isLoading.value = false
  }
}

// 处理忘记密码
const handleForgotPassword = (event: Event) => {
  event.preventDefault()
  // TODO: 实现忘记密码功能
  alert('忘记密码功能即将上线，请联系管理员重置密码')
}

// 初始化时检查是否已登录
onMounted(async () => {
  if (authStore.isAuthenticated) {
    const redirectTo = route.query.redirect as string || '/'
    await router.push(redirectTo)
  }
  
  // 尝试从URL参数中获取用户名
  const username = route.query.username as string
  if (username) {
    form.username = username
  }
})

// 设置页面标题
document.title = '登录 - AI助手'
</script>

<style scoped>
/* 自定义样式 */
.loading-spinner {
  border-color: currentColor;
  border-right-color: transparent;
}

/* 输入框焦点效果 */
.input:focus {
  @apply ring-2 ring-primary ring-offset-2;
}

/* 复选框样式 */
input[type="checkbox"] {
  @apply text-primary focus:ring-primary border-input;
}

/* 链接悬停效果 */
a:hover {
  @apply transition-colors duration-200;
}

/* 按钮禁用状态 */
.btn:disabled {
  @apply cursor-not-allowed opacity-50;
}
</style>