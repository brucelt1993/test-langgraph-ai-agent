<template>
  <div class="container mx-auto px-4 py-8 max-w-4xl">
    <div class="bg-card rounded-lg shadow-lg p-6">
      <div class="flex items-center space-x-4 mb-6">
        <div class="w-16 h-16 bg-primary rounded-full flex items-center justify-center">
          <svg class="w-8 h-8 text-primary-foreground" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"/>
          </svg>
        </div>
        <div>
          <h1 class="text-2xl font-bold">设置</h1>
          <p class="text-muted-foreground">管理您的应用设置</p>
        </div>
      </div>

      <div class="space-y-8">
        <!-- 安全设置 -->
        <div class="border-b pb-6">
          <h2 class="text-lg font-semibold mb-4">安全设置</h2>
          <div class="space-y-4">
            <div>
              <h3 class="font-medium mb-2">修改密码</h3>
              <p class="text-sm text-muted-foreground mb-4">定期更改密码以保护账户安全</p>
              <div class="space-y-3 max-w-md">
                <input 
                  v-model="currentPassword"
                  type="password" 
                  class="input w-full" 
                  placeholder="当前密码"
                />
                <input 
                  v-model="newPassword"
                  type="password" 
                  class="input w-full" 
                  placeholder="新密码"
                />
                <input 
                  v-model="confirmPassword"
                  type="password" 
                  class="input w-full" 
                  placeholder="确认新密码"
                />
                <button 
                  class="btn btn-outline"
                  @click="changePassword"
                  :disabled="isChangingPassword"
                >
                  {{ isChangingPassword ? '修改中...' : '修改密码' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 会话管理 -->
        <div class="border-b pb-6">
          <h2 class="text-lg font-semibold mb-4">会话管理</h2>
          <div class="space-y-4">
            <div>
              <h3 class="font-medium mb-2">活跃会话</h3>
              <p class="text-sm text-muted-foreground mb-4">管理您的登录会话</p>
              
              <div class="space-y-3" v-if="sessions.length">
                <div 
                  v-for="session in sessions" 
                  :key="session.id"
                  class="flex items-center justify-between p-3 bg-muted rounded-lg"
                >
                  <div class="space-y-1">
                    <div class="font-medium">{{ session.device_info }}</div>
                    <div class="text-sm text-muted-foreground">
                      IP: {{ session.ip_address }}
                    </div>
                    <div class="text-sm text-muted-foreground">
                      最后活跃: {{ formatDate(session.last_used_at) }}
                    </div>
                  </div>
                  <button 
                    class="btn btn-destructive btn-sm"
                    @click="revokeSession(session.id)"
                    :disabled="isRevokingSession"
                  >
                    撤销
                  </button>
                </div>
              </div>
              
              <div v-else class="text-center py-4 text-muted-foreground">
                暂无活跃会话
              </div>
            </div>
          </div>
        </div>

        <!-- 应用偏好 -->
        <div class="border-b pb-6">
          <h2 class="text-lg font-semibold mb-4">应用偏好</h2>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-medium">主题模式</h3>
                <p class="text-sm text-muted-foreground">选择应用的显示主题</p>
              </div>
              <select v-model="theme" class="select">
                <option value="light">浅色</option>
                <option value="dark">深色</option>
                <option value="system">跟随系统</option>
              </select>
            </div>
            
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-medium">语言设置</h3>
                <p class="text-sm text-muted-foreground">选择应用显示语言</p>
              </div>
              <select v-model="language" class="select">
                <option value="zh-CN">简体中文</option>
                <option value="en-US">English</option>
              </select>
            </div>
            
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-medium">消息通知</h3>
                <p class="text-sm text-muted-foreground">接收新消息通知</p>
              </div>
              <label class="switch">
                <input 
                  type="checkbox" 
                  v-model="notifications"
                />
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </div>

        <!-- 数据管理 -->
        <div>
          <h2 class="text-lg font-semibold mb-4">数据管理</h2>
          <div class="space-y-4">
            <div>
              <h3 class="font-medium mb-2">清除数据</h3>
              <p class="text-sm text-muted-foreground mb-4">清除本地存储的应用数据</p>
              <div class="space-x-4">
                <button 
                  class="btn btn-outline"
                  @click="clearLocalData"
                >
                  清除缓存
                </button>
                <button 
                  class="btn btn-destructive"
                  @click="clearAllData"
                >
                  清除所有数据
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNotification } from '@/composables/useNotification'
import type { UserSession } from '@/types/api'

const authStore = useAuthStore()
const { showSuccess, showError } = useNotification()

// 表单状态
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const isChangingPassword = ref(false)
const isRevokingSession = ref(false)

// 会话列表
const sessions = ref<UserSession[]>([])

// 应用设置
const theme = ref('system')
const language = ref('zh-CN')
const notifications = ref(true)

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 修改密码
const changePassword = async () => {
  if (isChangingPassword.value) return
  
  if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
    showError('请填写所有密码字段')
    return
  }
  
  if (newPassword.value !== confirmPassword.value) {
    showError('新密码与确认密码不一致')
    return
  }
  
  if (newPassword.value.length < 6) {
    showError('新密码长度至少6位')
    return
  }
  
  try {
    isChangingPassword.value = true
    
    await authStore.changePassword({
      current_password: currentPassword.value,
      new_password: newPassword.value
    })
    
    // 清空表单
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    
    showSuccess('密码修改成功')
  } catch (error: any) {
    showError(error.message || '密码修改失败')
  } finally {
    isChangingPassword.value = false
  }
}

// 获取用户会话
const loadUserSessions = async () => {
  try {
    const response = await authStore.getUserSessions()
    sessions.value = response.sessions
  } catch (error) {
    console.error('加载用户会话失败:', error)
  }
}

// 撤销会话
const revokeSession = async (sessionId: string) => {
  if (isRevokingSession.value) return
  
  try {
    isRevokingSession.value = true
    await authStore.revokeSession(sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    showSuccess('会话已撤销')
  } catch (error: any) {
    showError(error.message || '撤销会话失败')
  } finally {
    isRevokingSession.value = false
  }
}

// 清除本地缓存
const clearLocalData = () => {
  if (confirm('确定要清除本地缓存吗？这将清除应用的临时数据。')) {
    localStorage.clear()
    sessionStorage.clear()
    showSuccess('本地缓存已清除')
  }
}

// 清除所有数据
const clearAllData = () => {
  if (confirm('确定要清除所有数据吗？这将注销您的账户并清除所有本地数据。')) {
    authStore.logout()
    localStorage.clear()
    sessionStorage.clear()
    showSuccess('所有数据已清除，即将跳转到登录页面')
  }
}

onMounted(() => {
  loadUserSessions()
})
</script>

<style scoped>
.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: hsl(var(--primary));
}

input:checked + .slider:before {
  transform: translateX(26px);
}
</style>