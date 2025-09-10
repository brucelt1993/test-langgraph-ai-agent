<template>
  <div class="min-h-screen flex items-center justify-center bg-background p-4">
    <div class="card w-full max-w-md">
      <div class="card-header text-center">
        <h1 class="card-title text-3xl font-bold">创建账户</h1>
        <p class="card-description">加入AI助手，开始智能对话</p>
      </div>
      
      <div class="card-content space-y-4">
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- 用户名输入 -->
          <div class="space-y-2">
            <label for="username" class="text-sm font-medium leading-none">
              用户名 <span class="text-destructive">*</span>
            </label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              class="input"
              placeholder="请输入用户名"
              :disabled="isLoading"
              @blur="validateField('username')"
              required
            />
            <div v-if="errors.username" class="text-sm text-destructive">
              {{ errors.username }}
            </div>
            <div v-else class="text-xs text-muted-foreground">
              3-20个字符，支持字母、数字和下划线
            </div>
          </div>

          <!-- 邮箱输入 -->
          <div class="space-y-2">
            <label for="email" class="text-sm font-medium leading-none">
              邮箱地址 <span class="text-destructive">*</span>
            </label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              class="input"
              placeholder="请输入邮箱地址"
              :disabled="isLoading"
              @blur="validateField('email')"
              required
            />
            <div v-if="errors.email" class="text-sm text-destructive">
              {{ errors.email }}
            </div>
          </div>

          <!-- 全名输入 -->
          <div class="space-y-2">
            <label for="fullName" class="text-sm font-medium leading-none">
              真实姓名
            </label>
            <input
              id="fullName"
              v-model="form.fullName"
              type="text"
              class="input"
              placeholder="请输入真实姓名（可选）"
              :disabled="isLoading"
            />
            <div class="text-xs text-muted-foreground">
              可选，用于个性化体验
            </div>
          </div>

          <!-- 密码输入 -->
          <div class="space-y-2">
            <label for="password" class="text-sm font-medium leading-none">
              密码 <span class="text-destructive">*</span>
            </label>
            <div class="relative">
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                class="input pr-10"
                placeholder="请输入密码"
                :disabled="isLoading"
                @blur="validateField('password')"
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
            <div v-else class="text-xs text-muted-foreground">
              至少8个字符，包含字母和数字
            </div>
            
            <!-- 密码强度指示器 -->
            <div v-if="form.password" class="space-y-1">
              <div class="text-xs text-muted-foreground">密码强度：</div>
              <div class="flex space-x-1">
                <div 
                  v-for="i in 4" 
                  :key="i"
                  class="h-1 flex-1 rounded-full"
                  :class="getPasswordStrengthBarClass(i)"
                ></div>
              </div>
              <div class="text-xs" :class="getPasswordStrengthTextClass()">
                {{ getPasswordStrengthText() }}
              </div>
            </div>
          </div>

          <!-- 确认密码输入 -->
          <div class="space-y-2">
            <label for="confirmPassword" class="text-sm font-medium leading-none">
              确认密码 <span class="text-destructive">*</span>
            </label>
            <div class="relative">
              <input
                id="confirmPassword"
                v-model="form.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                class="input pr-10"
                placeholder="请再次输入密码"
                :disabled="isLoading"
                @blur="validateField('confirmPassword')"
                required
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 pr-3 flex items-center"
                @click="toggleConfirmPassword"
                :disabled="isLoading"
              >
                <component 
                  :is="showConfirmPassword ? EyeOffIcon : EyeIcon" 
                  class="h-4 w-4 text-muted-foreground" 
                />
              </button>
            </div>
            <div v-if="errors.confirmPassword" class="text-sm text-destructive">
              {{ errors.confirmPassword }}
            </div>
          </div>

          <!-- 服务条款和隐私政策 -->
          <div class="flex items-start space-x-2">
            <input
              id="agreement"
              v-model="form.agreeToTerms"
              type="checkbox"
              class="h-4 w-4 rounded border-input mt-0.5"
              :disabled="isLoading"
              required
            />
            <label for="agreement" class="text-sm leading-relaxed">
              我已阅读并同意
              <a href="#" class="text-primary hover:underline" @click="showTerms">服务条款</a>
              和
              <a href="#" class="text-primary hover:underline" @click="showPrivacy">隐私政策</a>
            </label>
          </div>
          <div v-if="errors.agreeToTerms" class="text-sm text-destructive">
            {{ errors.agreeToTerms }}
          </div>

          <!-- 错误提示 -->
          <div v-if="submitError" class="p-3 rounded-md bg-destructive/10 border border-destructive/20">
            <p class="text-sm text-destructive">{{ submitError }}</p>
          </div>

          <!-- 注册按钮 -->
          <button
            type="submit"
            class="btn btn-primary btn-md w-full"
            :disabled="isLoading || !isFormValid"
          >
            <div v-if="isLoading" class="loading-spinner w-4 h-4 mr-2"></div>
            {{ isLoading ? '注册中...' : '创建账户' }}
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

        <!-- 登录链接 -->
        <div class="text-center">
          <p class="text-sm text-muted-foreground">
            已有账户？
            <RouterLink
              to="/login"
              class="font-medium text-primary hover:underline"
            >
              立即登录
            </RouterLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
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
const showConfirmPassword = ref(false)
const isLoading = ref(false)
const submitError = ref('')

// 表单数据
const form = reactive({
  username: '',
  email: '',
  fullName: '',
  password: '',
  confirmPassword: '',
  agreeToTerms: false
})

// 表单验证错误
const errors = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreeToTerms: ''
})

// 计算属性
const isFormValid = computed(() => {
  return form.username.trim().length >= 3 && 
         form.email.trim().length > 0 &&
         form.password.length >= 8 &&
         form.confirmPassword === form.password &&
         form.agreeToTerms &&
         Object.values(errors).every(error => !error)
})

// 密码强度计算
const passwordStrength = computed(() => {
  const password = form.password
  if (!password) return 0
  
  let strength = 0
  if (password.length >= 8) strength++
  if (/[a-z]/.test(password)) strength++
  if (/[A-Z]/.test(password)) strength++
  if (/[0-9]/.test(password)) strength++
  if (/[^A-Za-z0-9]/.test(password)) strength++
  
  return Math.min(strength, 4)
})

// 切换密码显示
const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const toggleConfirmPassword = () => {
  showConfirmPassword.value = !showConfirmPassword.value
}

// 密码强度样式
const getPasswordStrengthBarClass = (index: number) => {
  if (index <= passwordStrength.value) {
    if (passwordStrength.value <= 1) return 'bg-destructive'
    if (passwordStrength.value <= 2) return 'bg-yellow-500'
    if (passwordStrength.value <= 3) return 'bg-blue-500'
    return 'bg-green-500'
  }
  return 'bg-muted'
}

const getPasswordStrengthTextClass = () => {
  if (passwordStrength.value <= 1) return 'text-destructive'
  if (passwordStrength.value <= 2) return 'text-yellow-600'
  if (passwordStrength.value <= 3) return 'text-blue-600'
  return 'text-green-600'
}

const getPasswordStrengthText = () => {
  if (passwordStrength.value <= 1) return '弱'
  if (passwordStrength.value <= 2) return '一般'
  if (passwordStrength.value <= 3) return '良好'
  return '强'
}

// 邮箱验证正则
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// 用户名验证正则
const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/

// 字段验证
const validateField = (fieldName: string) => {
  switch (fieldName) {
    case 'username':
      if (!form.username.trim()) {
        errors.username = '请输入用户名'
      } else if (!usernameRegex.test(form.username)) {
        errors.username = '用户名格式不正确'
      } else {
        errors.username = ''
      }
      break
      
    case 'email':
      if (!form.email.trim()) {
        errors.email = '请输入邮箱地址'
      } else if (!emailRegex.test(form.email)) {
        errors.email = '邮箱格式不正确'
      } else {
        errors.email = ''
      }
      break
      
    case 'password':
      if (!form.password) {
        errors.password = '请输入密码'
      } else if (form.password.length < 8) {
        errors.password = '密码至少8个字符'
      } else if (!/[a-zA-Z]/.test(form.password) || !/[0-9]/.test(form.password)) {
        errors.password = '密码必须包含字母和数字'
      } else {
        errors.password = ''
      }
      
      // 重新验证确认密码
      if (form.confirmPassword) {
        validateField('confirmPassword')
      }
      break
      
    case 'confirmPassword':
      if (!form.confirmPassword) {
        errors.confirmPassword = '请确认密码'
      } else if (form.confirmPassword !== form.password) {
        errors.confirmPassword = '两次输入的密码不一致'
      } else {
        errors.confirmPassword = ''
      }
      break
  }
}

// 验证整个表单
const validateForm = () => {
  validateField('username')
  validateField('email')
  validateField('password')
  validateField('confirmPassword')
  
  // 验证服务条款
  if (!form.agreeToTerms) {
    errors.agreeToTerms = '请同意服务条款和隐私政策'
  } else {
    errors.agreeToTerms = ''
  }
  
  return Object.values(errors).every(error => !error)
}

// 处理表单提交
const handleSubmit = async () => {
  if (!validateForm() || isLoading.value) {
    return
  }

  isLoading.value = true
  submitError.value = ''

  try {
    await authStore.register({
      username: form.username.trim(),
      email: form.email.trim(),
      password: form.password,
      full_name: form.fullName.trim() || undefined
    })

    // 注册成功
    showSuccess('注册成功！欢迎加入AI助手')
    
    // 跳转到首页
    await router.push('/')
    
  } catch (error: any) {
    console.error('注册失败:', error)
    
    // 使用通知系统显示错误
    let errorMessage = '注册失败，请稍后重试'
    
    if (error.message) {
      errorMessage = error.message
    } else if (error.detail) {
      if (Array.isArray(error.detail)) {
        errorMessage = error.detail.map((err: any) => err.msg).join(', ')
      } else {
        errorMessage = error.detail
      }
    }
    
    // 显示错误通知
    showError(errorMessage, '注册失败')
    
    // 同时保留本地错误显示作为备选
    submitError.value = errorMessage
  } finally {
    isLoading.value = false
  }
}

// 显示服务条款
const showTerms = (event: Event) => {
  event.preventDefault()
  // TODO: 实现服务条款弹窗
  alert('服务条款内容即将上线')
}

// 显示隐私政策
const showPrivacy = (event: Event) => {
  event.preventDefault()
  // TODO: 实现隐私政策弹窗
  alert('隐私政策内容即将上线')
}

// 初始化时检查是否已登录
onMounted(async () => {
  if (authStore.isAuthenticated) {
    await router.push('/')
  }
})

// 设置页面标题
document.title = '注册 - AI助手'
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

/* 密码强度指示器动画 */
.h-1 {
  @apply transition-colors duration-200;
}
</style>