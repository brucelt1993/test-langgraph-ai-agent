<template>
  <div class="min-h-screen bg-background text-foreground p-8">
    <div class="container mx-auto max-w-4xl">
      <h1 class="text-4xl font-bold mb-8 text-primary">CSS 样式测试页面</h1>
      
      <!-- 基础样式测试 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div class="card p-6">
          <h2 class="text-2xl font-semibold mb-4 text-card-foreground">卡片组件测试</h2>
          <p class="text-muted-foreground mb-4">这是一个标准的卡片组件，用来测试基础样式。</p>
          <div class="flex space-x-4">
            <button class="btn btn-primary btn-md">主要按钮</button>
            <button class="btn btn-secondary btn-md">次要按钮</button>
            <button class="btn btn-outline btn-md">轮廓按钮</button>
          </div>
        </div>
        
        <div class="card p-6">
          <h2 class="text-2xl font-semibold mb-4">表单组件测试</h2>
          <div class="space-y-4">
            <input 
              type="text" 
              placeholder="输入框测试" 
              class="input w-full"
            />
            <input 
              type="email" 
              placeholder="邮箱输入框" 
              class="input w-full"
            />
            <button class="btn btn-destructive w-full">删除按钮</button>
          </div>
        </div>
      </div>
      
      <!-- 聊天样式测试 -->
      <div class="card p-6 mb-8">
        <h2 class="text-2xl font-semibold mb-4">聊天样式测试</h2>
        <div class="space-y-4">
          <div class="flex justify-end">
            <div class="message-bubble message-user">
              这是用户消息的样式测试。
            </div>
          </div>
          <div class="flex justify-start">
            <div class="message-bubble message-assistant">
              这是AI助手消息的样式测试，包含更长的内容来测试换行和样式效果。
            </div>
          </div>
          <div class="flex justify-center">
            <div class="message-bubble message-thinking">
              这是思考过程的样式测试。
            </div>
          </div>
        </div>
      </div>
      
      <!-- 颜色主题测试 -->
      <div class="card p-6 mb-8">
        <h2 class="text-2xl font-semibold mb-4">颜色主题测试</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="p-4 bg-primary text-primary-foreground rounded-lg text-center">
            主色调
          </div>
          <div class="p-4 bg-secondary text-secondary-foreground rounded-lg text-center">
            次要色
          </div>
          <div class="p-4 bg-muted text-muted-foreground rounded-lg text-center">
            静音色
          </div>
          <div class="p-4 bg-accent text-accent-foreground rounded-lg text-center">
            强调色
          </div>
        </div>
      </div>
      
      <!-- 暗色模式切换测试 -->
      <div class="card p-6">
        <h2 class="text-2xl font-semibold mb-4">主题切换测试</h2>
        <button 
          @click="toggleTheme" 
          class="btn btn-ghost btn-lg"
        >
          {{ isDark ? '🌞 切换到亮色模式' : '🌙 切换到暗色模式' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isDark = ref(false)

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

onMounted(() => {
  const theme = localStorage.getItem('theme') || 
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
  
  isDark.value = theme === 'dark'
  document.documentElement.classList.toggle('dark', isDark.value)
})
</script>