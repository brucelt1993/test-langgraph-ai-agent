<template>
  <div class="min-h-screen bg-background">
    <!-- 头部导航 -->
    <header class="border-b border-border bg-card sticky top-0 z-40">
      <div class="flex items-center justify-between px-4 py-3">
        <!-- 左侧：返回和会话信息 -->
        <div class="flex items-center space-x-3">
          <button
            class="btn btn-ghost btn-sm"
            @click="goBack"
            title="返回"
          >
            <ArrowLeft class="w-4 h-4" />
          </button>
          
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
              <svg class="w-4 h-4 text-primary-foreground" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            
            <div>
              <h1 class="font-medium">
                {{ currentSession?.title || '新对话' }}
              </h1>
              <p class="text-sm text-muted-foreground">
                {{ getSessionStatus() }}
              </p>
            </div>
          </div>
        </div>

        <!-- 右侧：操作菜单 -->
        <div class="flex items-center space-x-2">
          <!-- 会话统计 -->
          <button
            v-if="currentSession"
            class="btn btn-ghost btn-sm"
            @click="showStats = true"
            title="会话统计"
          >
            <BarChart3 class="w-4 h-4" />
          </button>

          <!-- 清空对话 -->
          <button
            v-if="messages.length > 0"
            class="btn btn-ghost btn-sm"
            @click="confirmClearChat"
            title="清空对话"
          >
            <Trash2 class="w-4 h-4" />
          </button>

          <!-- 更多选项 -->
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button class="btn btn-ghost btn-sm">
                <MoreVertical class="w-4 h-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem @click="editSessionTitle">
                <Edit3 class="w-4 h-4 mr-2" />
                编辑标题
              </DropdownMenuItem>
              <DropdownMenuItem @click="exportChat">
                <Download class="w-4 h-4 mr-2" />
                导出对话
              </DropdownMenuItem>
              <DropdownMenuItem @click="shareChat">
                <Share2 class="w-4 h-4 mr-2" />
                分享对话
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="showSettings = true">
                <Settings class="w-4 h-4 mr-2" />
                设置
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>

    <!-- 聊天主体 -->
    <main class="flex flex-col" :style="{ height: 'calc(100vh - 61px)' }">
      <!-- 消息列表 -->
      <MessageList
        :messages="messages"
        :is-loading="isLoadingMessages"
        :is-typing="isSending"
        :can-load-more="canLoadMoreMessages"
        :show-thinking-process="showThinkingProcess"
        @load-more="loadMoreMessages"
        @message-click="handleMessageClick"
        @stream-complete="handleStreamComplete"
        @thinking-change="handleThinkingChange"
        @tool-call="handleToolCall"
        class="flex-1"
      />

      <!-- 输入区域 -->
      <InputArea
        :disabled="!currentSession || isSending"
        :is-sending="isSending"
        :suggestions="suggestions"
        :show-suggestions="!messages.length"
        @send="handleSendMessage"
        @input="handleInputChange"
        @attachments-change="handleAttachmentsChange"
      />
    </main>

    <!-- 会话统计弹窗 -->
    <Dialog :open="showStats" @update:open="showStats = $event">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>会话统计</DialogTitle>
          <DialogDescription>
            查看当前会话的详细统计信息
          </DialogDescription>
        </DialogHeader>
        
        <div v-if="sessionStats" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="text-center p-3 bg-muted rounded-lg">
              <div class="text-2xl font-bold">{{ sessionStats.message_count }}</div>
              <div class="text-sm text-muted-foreground">总消息数</div>
            </div>
            <div class="text-center p-3 bg-muted rounded-lg">
              <div class="text-2xl font-bold">{{ sessionStats.context_rounds }}</div>
              <div class="text-sm text-muted-foreground">上下文轮数</div>
            </div>
            <div class="text-center p-3 bg-muted rounded-lg">
              <div class="text-2xl font-bold">{{ sessionStats.tool_call_count }}</div>
              <div class="text-sm text-muted-foreground">工具调用</div>
            </div>
            <div class="text-center p-3 bg-muted rounded-lg">
              <div class="text-2xl font-bold">
                {{ sessionStats.average_response_time ? Math.round(sessionStats.average_response_time) + 's' : '-' }}
              </div>
              <div class="text-sm text-muted-foreground">平均响应</div>
            </div>
          </div>
          
          <div v-if="sessionStats.first_message_at" class="text-sm text-muted-foreground">
            <p>开始时间: {{ formatDateTime(sessionStats.first_message_at) }}</p>
            <p>最后活动: {{ formatDateTime(sessionStats.last_message_at) }}</p>
          </div>
        </div>

        <DialogFooter>
          <button class="btn btn-outline" @click="showStats = false">
            关闭
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 设置弹窗 -->
    <Dialog :open="showSettings" @update:open="showSettings = $event">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>聊天设置</DialogTitle>
          <DialogDescription>
            自定义您的聊天体验
          </DialogDescription>
        </DialogHeader>
        
        <div class="space-y-4">
          <!-- 显示AI思考过程 -->
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium">显示AI思考过程</label>
            <input
              v-model="showThinkingProcess"
              type="checkbox"
              class="h-4 w-4"
            />
          </div>
          
          <!-- 自动滚动 -->
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium">自动滚动到新消息</label>
            <input
              v-model="autoScroll"
              type="checkbox"
              class="h-4 w-4"
            />
          </div>
          
          <!-- 消息时间显示 -->
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium">显示消息时间</label>
            <input
              v-model="showMessageTime"
              type="checkbox"
              class="h-4 w-4"
            />
          </div>
        </div>

        <DialogFooter>
          <button class="btn btn-outline" @click="showSettings = false">
            关闭
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 清空对话确认弹窗 -->
    <Dialog :open="showClearConfirm" @update:open="showClearConfirm = $event">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>清空对话</DialogTitle>
          <DialogDescription>
            此操作将删除当前会话中的所有消息，且无法恢复。确定要继续吗？
          </DialogDescription>
        </DialogHeader>

        <DialogFooter>
          <button class="btn btn-outline" @click="showClearConfirm = false">
            取消
          </button>
          <button class="btn btn-destructive" @click="clearChat">
            确定清空
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  ArrowLeft, 
  MoreVertical, 
  Edit3, 
  Download, 
  Share2, 
  Settings, 
  Trash2,
  BarChart3
} from 'lucide-vue-next'

import MessageList from '@/components/MessageList.vue'
import InputArea from '@/components/InputArea.vue'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import type { Message, SessionStatsResponse } from '@/types/chat'

// 组件引用 (这些需要实际的UI库组件，这里用占位符)
const Dialog = { name: 'Dialog' }
const DialogContent = { name: 'DialogContent' }
const DialogHeader = { name: 'DialogHeader' }
const DialogTitle = { name: 'DialogTitle' }
const DialogDescription = { name: 'DialogDescription' }
const DialogFooter = { name: 'DialogFooter' }
const DropdownMenu = { name: 'DropdownMenu' }
const DropdownMenuTrigger = { name: 'DropdownMenuTrigger' }
const DropdownMenuContent = { name: 'DropdownMenuContent' }
const DropdownMenuItem = { name: 'DropdownMenuItem' }
const DropdownMenuSeparator = { name: 'DropdownMenuSeparator' }

// 路由和状态
const router = useRouter()
const route = useRoute()
const chatStore = useChatStore()
const authStore = useAuthStore()

// 响应式状态
const showStats = ref(false)
const showSettings = ref(false)
const showClearConfirm = ref(false)
const showThinkingProcess = ref(true)
const autoScroll = ref(true)
const showMessageTime = ref(true)
const sessionStats = ref<SessionStatsResponse | null>(null)

// 计算属性
const currentSession = computed(() => chatStore.currentSession)
const messages = computed(() => chatStore.currentMessages)
const isLoadingMessages = computed(() => chatStore.isLoading)
const isSending = computed(() => chatStore.isSending)
const canLoadMoreMessages = computed(() => {
  // 这里可以根据实际情况判断是否还有更多消息
  return messages.value.length >= 50
})

// 建议问题
const suggestions = ref([
  '你好，请介绍一下自己',
  '今天天气怎么样？',
  '帮我写一份工作总结',
  '解释一下人工智能的工作原理'
])

// 获取会话状态文本
const getSessionStatus = () => {
  if (!currentSession.value) return '新会话'
  
  const messageCount = messages.value.length
  if (messageCount === 0) return '等待开始对话'
  if (isSending.value) return 'AI正在思考...'
  
  return `${messageCount} 条消息`
}

// 返回上一页
const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/chat')
  }
}

// 处理发送消息
const handleSendMessage = async ({ text, attachments }: { text: string; attachments: any[] }) => {
  if (!currentSession.value || !text.trim()) return

  try {
    await chatStore.sendMessage(currentSession.value.id, text)
  } catch (error) {
    console.error('发送消息失败:', error)
    // TODO: 显示错误提示
  }
}

// 处理输入变化
const handleInputChange = (text: string) => {
  // 可以在这里处理输入变化，比如显示正在输入状态
  console.log('用户正在输入:', text)
}

// 处理附件变化
const handleAttachmentsChange = (attachments: any[]) => {
  console.log('附件变化:', attachments)
}

// 处理消息点击
const handleMessageClick = (message: Message) => {
  console.log('消息被点击:', message)
}

// 处理流式消息完成
const handleStreamComplete = (message: Message, content: string) => {
  console.log('流式消息完成:', message.id, content)
  // TODO: 更新消息内容到store
  chatStore.updateMessageContent(message.id, content)
}

// 处理思考过程变化
const handleThinkingChange = (message: Message, thinking: string) => {
  console.log('思考过程更新:', message.id, thinking)
  // TODO: 可以实时显示AI的思考过程
}

// 处理工具调用
const handleToolCall = (message: Message, tool: { name: string; description: string }) => {
  console.log('工具调用:', message.id, tool)
  // TODO: 显示工具调用的状态和结果
}

// 加载更多消息
const loadMoreMessages = async () => {
  if (!currentSession.value) return
  
  try {
    // TODO: 实现加载历史消息
    console.log('加载更多消息')
  } catch (error) {
    console.error('加载消息失败:', error)
  }
}

// 编辑会话标题
const editSessionTitle = () => {
  if (!currentSession.value) return
  
  const newTitle = prompt('请输入新的会话标题:', currentSession.value.title)
  if (newTitle && newTitle.trim()) {
    chatStore.updateSession(currentSession.value.id, { title: newTitle.trim() })
  }
}

// 确认清空对话
const confirmClearChat = () => {
  showClearConfirm.value = true
}

// 清空对话
const clearChat = () => {
  // TODO: 实现清空对话功能
  showClearConfirm.value = false
  console.log('清空对话')
}

// 导出对话
const exportChat = () => {
  if (!currentSession.value || !messages.value.length) return
  
  const chatData = {
    title: currentSession.value.title,
    messages: messages.value.map(msg => ({
      type: msg.message_type,
      content: msg.content,
      timestamp: msg.created_at
    })),
    exported_at: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(chatData, null, 2)], {
    type: 'application/json'
  })
  
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chat-${currentSession.value.id}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// 分享对话
const shareChat = () => {
  // TODO: 实现分享对话功能
  console.log('分享对话')
}

// 格式化日期时间
const formatDateTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 获取会话统计
const loadSessionStats = async () => {
  if (!currentSession.value) return
  
  try {
    const stats = await chatStore.getSessionStats(currentSession.value.id)
    sessionStats.value = stats
  } catch (error) {
    console.error('获取会话统计失败:', error)
  }
}

// 监听会话统计弹窗显示
watch(() => showStats.value, (show) => {
  if (show) {
    loadSessionStats()
  }
})

// 初始化
onMounted(async () => {
  const sessionId = route.params.sessionId as string | undefined
  
  if (sessionId && typeof sessionId === 'string') {
    // 加载指定会话
    try {
      await chatStore.getSession(sessionId)
    } catch (error) {
      console.error('加载会话失败:', error)
      router.push('/chat')
    }
  } else {
    // 创建新会话
    try {
      const newSession = await chatStore.createSession({
        title: '新对话',
        agent_name: 'default'
      })
      router.replace(`/chat/${newSession.id}`)
    } catch (error) {
      console.error('创建会话失败:', error)
    }
  }
  
  // 设置页面标题
  document.title = `聊天 - ${currentSession.value?.title || '新对话'} - AI助手`
})

// 清理
onUnmounted(() => {
  chatStore.disconnectStream()
})
</script>

<style scoped>
/* 自定义样式 */
.chat-header {
  backdrop-filter: blur(8px);
  background-color: rgba(255, 255, 255, 0.8);
}

.dark .chat-header {
  background-color: rgba(0, 0, 0, 0.8);
}

/* 按钮样式 */
.btn:hover {
  @apply transition-colors duration-200;
}

/* 响应式调整 */
@media (max-width: 640px) {
  .space-x-3 > * + * {
    @apply ml-2;
  }
  
  .px-4 {
    @apply px-3;
  }
}
</style>