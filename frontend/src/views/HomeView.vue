<template>
  <div class="min-h-screen bg-background">
    
    <!-- 头部导航 -->
    <header class="border-b border-border bg-card">
      <div class="container mx-auto px-4 py-4">
        <nav class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <h1 class="text-2xl font-bold text-primary">AI助手</h1>
          </div>
          
          <div class="flex items-center space-x-4">
            <template v-if="authStore.isAuthenticated">
              <RouterLink
                to="/chat"
                class="btn btn-primary btn-md"
              >
                开始聊天
              </RouterLink>
              <button
                class="btn btn-outline btn-md"
                @click="handleLogout"
              >
                退出登录
              </button>
            </template>
            <template v-else>
              <RouterLink
                to="/login"
                class="btn btn-outline btn-md"
              >
                登录
              </RouterLink>
              <RouterLink
                to="/register"
                class="btn btn-primary btn-md"
              >
                注册
              </RouterLink>
            </template>
          </div>
        </nav>
      </div>
    </header>

    <!-- 主要内容 -->
    <main class="container mx-auto px-4 py-8">
      <!-- 英雄区域 -->
      <section class="text-center py-16">
        <h1 class="text-4xl md:text-6xl font-bold mb-6">
          与AI助手开始
          <span class="text-primary">智能对话</span>
        </h1>
        <p class="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          体验先进的AI技术，获得个性化的智能回答和建议。支持多轮对话，记忆上下文，让交流更自然。
        </p>
        
        <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <RouterLink
            v-if="!authStore.isAuthenticated"
            to="/register"
            class="btn btn-primary btn-lg"
          >
            立即开始
          </RouterLink>
          <RouterLink
            v-else
            to="/chat"
            class="btn btn-primary btn-lg"
          >
            继续聊天
          </RouterLink>
          <button
            class="btn btn-outline btn-lg"
            @click="scrollToFeatures"
          >
            了解更多
          </button>
        </div>
      </section>

      <!-- 功能介绍 -->
      <section id="features" class="py-16">
        <h2 class="text-3xl font-bold text-center mb-12">核心功能</h2>
        
        <div class="grid md:grid-cols-3 gap-8">
          <div class="card">
            <div class="card-header">
              <div class="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 class="card-title text-xl">智能对话</h3>
            </div>
            <div class="card-content">
              <p class="text-muted-foreground">
                支持多轮对话，AI能够理解上下文，提供更准确和个性化的回答。
              </p>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <div class="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 class="card-title text-xl">实时响应</h3>
            </div>
            <div class="card-content">
              <p class="text-muted-foreground">
                采用流式传输技术，实时显示AI思考过程和回答内容，体验更流畅。
              </p>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <div class="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 class="card-title text-xl">安全可靠</h3>
            </div>
            <div class="card-content">
              <p class="text-muted-foreground">
                采用先进的安全措施保护用户隐私，对话记录安全存储，用户信息严格保密。
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 底部 -->
    <footer class="border-t border-border bg-card">
      <div class="container mx-auto px-4 py-8">
        <div class="text-center text-muted-foreground">
          <p>&copy; 2024 AI助手. All rights reserved.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 处理登出
const handleLogout = async () => {
  try {
    await authStore.logout()
    await router.push('/')
  } catch (error) {
    console.error('登出失败:', error)
  }
}

// 滚动到功能区域
const scrollToFeatures = () => {
  const element = document.getElementById('features')
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' })
  }
}

// 设置页面标题
document.title = 'AI助手 - 智能对话助手'
</script>