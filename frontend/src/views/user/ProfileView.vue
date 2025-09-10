<template>
  <div class="container mx-auto px-4 py-8 max-w-4xl">
    <div class="bg-card rounded-lg shadow-lg p-6">
      <div class="flex items-center space-x-4 mb-6">
        <div class="w-16 h-16 bg-primary rounded-full flex items-center justify-center">
          <svg class="w-8 h-8 text-primary-foreground" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
          </svg>
        </div>
        <div>
          <h1 class="text-2xl font-bold">个人资料</h1>
          <p class="text-muted-foreground">管理您的账户信息</p>
        </div>
      </div>

      <div class="space-y-6">
        <!-- 基本信息 -->
        <div class="border-b pb-6">
          <h2 class="text-lg font-semibold mb-4">基本信息</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-2">用户名</label>
              <input 
                type="text" 
                class="input w-full" 
                :value="user?.username || ''"
                readonly
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">邮箱</label>
              <input 
                type="email" 
                class="input w-full" 
                :value="user?.email || ''"
                readonly
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">全名</label>
              <input 
                v-model="fullName"
                type="text" 
                class="input w-full" 
                placeholder="请输入您的全名"
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">角色</label>
              <input 
                type="text" 
                class="input w-full" 
                :value="user?.role?.display_name || ''"
                readonly
              />
            </div>
          </div>
        </div>

        <!-- 账户状态 -->
        <div class="border-b pb-6">
          <h2 class="text-lg font-semibold mb-4">账户状态</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex items-center space-x-2">
              <span class="text-sm">账户激活状态:</span>
              <span :class="user?.is_active ? 'text-green-600' : 'text-red-600'">
                {{ user?.is_active ? '已激活' : '未激活' }}
              </span>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm">邮箱验证状态:</span>
              <span :class="user?.is_verified ? 'text-green-600' : 'text-red-600'">
                {{ user?.is_verified ? '已验证' : '未验证' }}
              </span>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm">注册时间:</span>
              <span class="text-sm">{{ formatDate(user?.created_at) }}</span>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm">最后登录:</span>
              <span class="text-sm">{{ formatDate(user?.last_login_at) || '从未登录' }}</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex space-x-4">
          <button 
            class="btn btn-primary"
            @click="updateProfile"
            :disabled="isLoading"
          >
            {{ isLoading ? '保存中...' : '保存更改' }}
          </button>
          <button 
            class="btn btn-outline"
            @click="resetForm"
          >
            重置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNotification } from '@/composables/useNotification'

const authStore = useAuthStore()
const { showSuccess, showError } = useNotification()

const isLoading = ref(false)
const fullName = ref('')

const user = computed(() => authStore.user)

// 格式化日期
const formatDate = (dateString?: string) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 更新用户资料
const updateProfile = async () => {
  if (isLoading.value) return
  
  try {
    isLoading.value = true
    
    await authStore.updateProfile({
      full_name: fullName.value
    })
    
    showSuccess('个人资料更新成功')
  } catch (error: any) {
    showError(error.message || '更新失败，请重试')
  } finally {
    isLoading.value = false
  }
}

// 重置表单
const resetForm = () => {
  fullName.value = user.value?.full_name || ''
}

// 初始化
onMounted(() => {
  resetForm()
})
</script>