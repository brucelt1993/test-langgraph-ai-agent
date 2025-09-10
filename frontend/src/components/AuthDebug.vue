<template>
  <div class="fixed bottom-4 right-4 bg-gray-800 text-white p-4 rounded-lg shadow-lg max-w-sm" v-if="showDebug">
    <div class="flex justify-between items-center mb-2">
      <h3 class="font-bold text-sm">认证调试信息</h3>
      <button @click="showDebug = false" class="text-gray-400 hover:text-white">×</button>
    </div>
    <div class="space-y-1 text-xs">
      <div>🔑 Token: {{ authStore.token ? '✓' : '✗' }}</div>
      <div>👤 User: {{ authStore.user?.username || '未获取' }}</div>
      <div>✅ 认证状态: {{ authStore.isAuthenticated ? '已认证' : '未认证' }}</div>
      <div>⏳ 加载中: {{ authStore.isLoading ? '是' : '否' }}</div>
      <div>📍 当前路由: {{ currentRoute }}</div>
      <div>🔄 更新时间: {{ lastUpdate }}</div>
    </div>
    <div class="mt-2 pt-2 border-t border-gray-600">
      <button @click="refreshAuth" class="text-blue-400 hover:text-blue-300 text-xs">
        刷新认证状态
      </button>
    </div>
  </div>
  <button 
    v-else
    @click="showDebug = true" 
    class="fixed bottom-4 right-4 bg-blue-600 text-white p-2 rounded-full shadow-lg hover:bg-blue-700"
    title="显示调试信息"
  >
    🔍
  </button>
</template>

<script setup lang="ts">
import { ref, computed, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const showDebug = ref(true)
const lastUpdate = ref(new Date().toLocaleTimeString())

const currentRoute = computed(() => route.path)

// 监听认证状态变化
watchEffect(() => {
  // 每次认证状态变化都更新时间
  authStore.isAuthenticated
  authStore.token
  authStore.user
  lastUpdate.value = new Date().toLocaleTimeString()
})

const refreshAuth = async () => {
  try {
    await authStore.initialize()
    lastUpdate.value = new Date().toLocaleTimeString()
  } catch (error) {
    console.error('刷新认证状态失败:', error)
  }
}
</script>