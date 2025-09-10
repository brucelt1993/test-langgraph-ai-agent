import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/services/api'
import type { User, LoginRequest, RegisterRequest, LoginResponse } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isLoading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  // 初始化
  const initialize = async () => {
    if (token.value) {
      try {
        const userData = await apiClient.get('/auth/me')
        user.value = userData
      } catch (error) {
        console.error('初始化认证失败:', error)
        clearAuth()
      }
    }
  }

  // 登录
  const login = async (credentials: LoginRequest): Promise<void> => {
    isLoading.value = true
    try {
      const response: LoginResponse = await apiClient.post('/auth/login', credentials)
      
      // 保存认证信息
      token.value = response.access_token
      user.value = response.user
      
      // 持久化token
      localStorage.setItem('token', response.access_token)
      
      // 设置API客户端默认头部
      apiClient.setAuthToken(response.access_token)
      
    } catch (error) {
      clearAuth()
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // 注册
  const register = async (userData: RegisterRequest): Promise<void> => {
    isLoading.value = true
    try {
      const response: LoginResponse = await apiClient.post('/auth/register', userData)
      
      // 注册成功后自动登录
      token.value = response.access_token
      user.value = response.user
      
      localStorage.setItem('token', response.access_token)
      apiClient.setAuthToken(response.access_token)
      
    } catch (error) {
      clearAuth()
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // 登出
  const logout = async (): Promise<void> => {
    try {
      if (token.value) {
        await apiClient.post('/auth/logout')
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      clearAuth()
    }
  }

  // 刷新token
  const refreshToken = async (): Promise<boolean> => {
    try {
      const response: LoginResponse = await apiClient.post('/auth/refresh')
      
      token.value = response.access_token
      user.value = response.user
      
      localStorage.setItem('token', response.access_token)
      apiClient.setAuthToken(response.access_token)
      
      return true
    } catch (error) {
      console.error('刷新token失败:', error)
      clearAuth()
      return false
    }
  }

  // 更新用户信息
  const updateProfile = async (profileData: Partial<User>): Promise<void> => {
    try {
      const updatedUser = await apiClient.put('/auth/profile', profileData)
      user.value = { ...user.value!, ...updatedUser }
    } catch (error) {
      throw error
    }
  }

  // 修改密码
  const changePassword = async (oldPassword: string, newPassword: string): Promise<void> => {
    try {
      await apiClient.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword
      })
    } catch (error) {
      throw error
    }
  }

  // 清除认证信息
  const clearAuth = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    apiClient.clearAuthToken()
  }

  return {
    // 状态
    user,
    token,
    isLoading,
    
    // 计算属性
    isAuthenticated,
    
    // 方法
    initialize,
    login,
    register,
    logout,
    refreshToken,
    updateProfile,
    changePassword,
    clearAuth
  }
})