import './style.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// 初始化认证状态
const initApp = async () => {
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()
  
  // 如果有存储的token，尝试初始化用户信息
  if (authStore.token) {
    try {
      await authStore.initialize()
    } catch (error) {
      console.error('初始化认证状态失败:', error)
      // 清除无效的认证信息
      authStore.clearAuth()
    }
  }
}

// 初始化应用
initApp().then(() => {
  app.mount('#app')
}).catch((error) => {
  console.error('应用初始化失败:', error)
  app.mount('#app')
})