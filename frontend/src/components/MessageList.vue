<template>
  <div 
    ref="messagesContainer"
    class="flex-1 overflow-y-auto p-4"
    :class="containerClass"
  >
    <div class="max-w-6xl mx-auto space-y-4">  <!-- 增加消息列表最大宽度 -->
    <!-- 加载更多历史消息 -->
    <div 
      v-if="canLoadMore && !isLoadingMore"
      class="text-center"
    >
      <button
        class="btn btn-ghost btn-sm"
        @click="loadMoreMessages"
      >
        加载更多消息
      </button>
    </div>
    
    <!-- 加载历史消息状态 -->
    <div 
      v-if="isLoadingMore"
      class="text-center"
    >
      <div class="loading-spinner w-4 h-4 mx-auto border-muted-foreground"></div>
      <p class="text-sm text-muted-foreground mt-2">加载历史消息...</p>
    </div>

    <!-- 空状态 -->
    <div 
      v-if="!messages.length && !isLoading"
      class="flex flex-col items-center justify-center h-full min-h-[200px] text-center"
    >
      <div class="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
        <svg class="w-8 h-8 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </div>
      <h3 class="text-lg font-medium mb-2">开始对话</h3>
      <p class="text-muted-foreground">
        输入您的问题，AI助手将为您提供帮助
      </p>
    </div>

    <!-- 消息列表 -->
    <div 
      v-for="(message, index) in messages" 
      :key="message.id"
      class="message-container"
      :class="getMessageContainerClass(message)"
    >
      <!-- 消息时间分组 -->
      <div 
        v-if="shouldShowTimeGroup(index)"
        class="text-center my-4"
      >
        <span class="text-xs text-muted-foreground bg-background px-3 py-1 rounded-full border">
          {{ formatTimeGroup(message.created_at) }}
        </span>
      </div>

      <!-- 消息气泡 -->
      <div 
        class="message-bubble"
        :class="getMessageBubbleClass(message)"
      >
        <!-- 用户消息 -->
        <div v-if="message.message_type === 'user'" class="space-y-2">
          <div class="text-sm font-medium text-right">您</div>
          <div class="prose prose-sm dark:prose-invert">
            {{ message.content }}
          </div>
          <div class="text-xs opacity-70 text-right">
            {{ formatMessageTime(message.created_at) }}
          </div>
        </div>

        <!-- AI消息 -->
        <div v-else-if="message.message_type === 'assistant'" class="space-y-2">
          <div class="flex items-center space-x-2">
            <div class="w-6 h-6 bg-primary rounded-full flex items-center justify-center">
              <svg class="w-3 h-3 text-primary-foreground" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            <div class="text-sm font-medium">AI助手</div>
            <div 
              v-if="message.confidence_score"
              class="text-xs bg-accent px-2 py-1 rounded-full"
            >
              置信度: {{ Math.round(message.confidence_score * 100) }}%
            </div>
          </div>
          
          <!-- 流式消息处理 -->
          <StreamingMessage
            v-if="message.is_streaming"
            :connection-id="message.stream_connection_id"
            :show-connection-status="false"
            :show-thinking-process="showThinkingProcess"
            :typewriter-speed="50"
            @message-complete="(content: string) => handleStreamComplete(message, content)"
            @thinking-change="(thinking: any) => handleThinkingChange(message, thinking)"
            @tool-call="(tool: any) => handleToolCall(message, tool)"
          />
          <!-- 静态消息 -->
          <div v-else>
            <div 
              class="prose prose-sm dark:prose-invert max-w-none"
              v-html="formatMessageContent(message.content)"
            ></div>
            
            <!-- 思考过程展示 -->
            <div 
              v-if="message.thinking_process && showThinkingProcess"
              class="mt-3 p-3 bg-accent/30 rounded-lg border border-accent/50"
            >
              <button
                class="flex items-center space-x-2 text-sm font-medium text-accent-foreground mb-2"
                @click="toggleThinkingProcess(message.id)"
              >
                <component 
                  :is="expandedThinking.has(message.id) ? ChevronDownIcon : ChevronRightIcon"
                  class="w-4 h-4"
                />
                <span>思考过程</span>
              </button>
              
              <div 
                v-if="expandedThinking.has(message.id)"
                class="space-y-2 text-sm"
              >
                <div 
                  v-for="(step, stepIndex) in message.thinking_process.steps" 
                  :key="stepIndex"
                  class="border-l-2 border-accent pl-3"
                >
                  <div class="font-medium">{{ step.title }}</div>
                  <div class="text-muted-foreground">{{ step.content }}</div>
                  <div v-if="step.confidence" class="text-xs">
                    置信度: {{ Math.round(step.confidence * 100) }}%
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 工具调用展示 -->
            <div 
              v-if="message.tool_calls && message.tool_calls.length > 0"
              class="mt-3 space-y-2"
            >
              <div 
                v-for="(toolCall, toolIndex) in message.tool_calls"
                :key="toolIndex"
                class="p-3 bg-secondary/30 rounded-lg border border-secondary/50"
              >
                <div class="flex items-center space-x-2 mb-2">
                  <svg class="w-4 h-4 text-secondary-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span class="text-sm font-medium">{{ toolCall.tool_name }}</span>
                </div>
                <div class="text-sm text-muted-foreground">
                  {{ toolCall.description || '调用工具处理请求' }}
                </div>
              </div>
            </div>
          </div>

          <div class="text-xs opacity-70">
            {{ formatMessageTime(message.created_at) }}
          </div>
        </div>

        <!-- 系统消息 -->
        <div v-else-if="message.message_type === 'system'" class="text-center">
          <div class="inline-block px-3 py-1 bg-muted rounded-full text-sm text-muted-foreground">
            {{ message.content }}
          </div>
        </div>

        <!-- 思考过程消息 -->
        <div v-else-if="message.message_type === 'thinking'" class="message-thinking">
          <div class="flex items-center space-x-2 mb-2">
            <div class="loading-spinner w-4 h-4 border-accent"></div>
            <span class="text-sm font-medium text-accent-foreground">AI正在思考...</span>
          </div>
          <div class="text-sm text-accent-foreground/80">
            {{ message.content }}
          </div>
        </div>

        <!-- 工具调用消息 -->
        <div v-else-if="message.message_type === 'tool_call'" class="bg-secondary/20">
          <div class="flex items-center space-x-2 mb-2">
            <svg class="w-4 h-4 text-secondary-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            </svg>
            <span class="text-sm font-medium">工具调用</span>
          </div>
          <div class="text-sm">
            {{ message.content }}
          </div>
        </div>
      </div>
    </div>

    <!-- 打字指示器 -->
    <div 
      v-if="isTyping"
      class="message-container justify-start"
    >
      <div class="message-bubble message-assistant">
        <div class="flex items-center space-x-2">
          <div class="w-6 h-6 bg-primary rounded-full flex items-center justify-center">
            <svg class="w-3 h-3 text-primary-foreground" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <div class="flex space-x-1">
            <div class="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
            <div class="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style="animation-delay: 0.1s;"></div>
            <div class="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style="animation-delay: 0.2s;"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 滚动到底部按钮 -->
    <div 
      v-if="showScrollToBottom"
      class="fixed bottom-20 right-4 z-10"
    >
      <button
        class="btn btn-primary rounded-full w-12 h-12 shadow-lg"
        @click="() => scrollToBottom()"
        title="滚动到底部"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </button>
    </div>
    </div> <!-- 关闭max-w-6xl容器 -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ChevronDownIcon, ChevronRightIcon } from 'lucide-vue-next'
import StreamingMessage from './StreamingMessage.vue'
import type { Message } from '@/types/chat'

// Props
interface Props {
  messages: Message[]
  isLoading?: boolean
  isTyping?: boolean
  canLoadMore?: boolean
  showThinkingProcess?: boolean
  containerClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  messages: () => [],
  isLoading: false,
  isTyping: false,
  canLoadMore: false,
  showThinkingProcess: true,
  containerClass: ''
})

// Emits
const emit = defineEmits<{
  loadMore: []
  messageClick: [message: Message]
  streamComplete: [message: Message, content: string]
  thinkingChange: [message: Message, thinking: string]
  toolCall: [message: Message, tool: { name: string; description: string }]
}>()

// 响应式引用
const messagesContainer = ref<HTMLElement>()
const isLoadingMore = ref(false)
const showScrollToBottom = ref(false)
const expandedThinking = ref(new Set<string>())

// 自动滚动到底部
const scrollToBottom = (smooth = true) => {
  if (!messagesContainer.value) return
  
  messagesContainer.value.scrollTo({
    top: messagesContainer.value.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto'
  })
}

// 检查是否应该显示"滚动到底部"按钮
const checkScrollToBottom = () => {
  if (!messagesContainer.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  const isNearBottom = scrollHeight - scrollTop - clientHeight < 100
  
  showScrollToBottom.value = !isNearBottom && props.messages.length > 0
}

// 加载更多消息
const loadMoreMessages = async () => {
  if (isLoadingMore.value || !props.canLoadMore) return
  
  isLoadingMore.value = true
  
  try {
    emit('loadMore')
  } finally {
    setTimeout(() => {
      isLoadingMore.value = false
    }, 1000)
  }
}

// 获取消息容器样式类
const getMessageContainerClass = (message: Message) => {
  return [
    'flex',
    message.message_type === 'user' ? 'justify-end' : 'justify-start',
    'animate-slide-in'
  ]
}

// 获取消息气泡样式类
const getMessageBubbleClass = (message: Message) => {
  const baseClasses = ['message-bubble', 'max-w-[85%]']
  
  switch (message.message_type) {
    case 'user':
      baseClasses.push('message-user')
      break
    case 'assistant':
      baseClasses.push('message-assistant')
      break
    case 'thinking':
      baseClasses.push('message-thinking')
      break
    case 'system':
      baseClasses.push('bg-muted/50', 'text-muted-foreground')
      break
    default:
      baseClasses.push('bg-muted', 'text-muted-foreground')
  }
  
  return baseClasses
}

// 格式化消息内容 (支持Markdown)
const formatMessageContent = (content: string) => {
  // 简单的Markdown处理
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-sm">$1</code>')
    .replace(/\n/g, '<br>')
}

// 格式化消息时间
const formatMessageTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (date.toDateString() === now.toDateString()) { // 今天
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } else { // 其他日期
    return date.toLocaleDateString('zh-CN', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

// 是否应该显示时间分组
const shouldShowTimeGroup = (index: number) => {
  if (index === 0) return true
  
  const currentMessage = props.messages[index]
  const previousMessage = props.messages[index - 1]
  
  if (!currentMessage || !previousMessage) return false
  
  const currentTime = new Date(currentMessage.created_at)
  const previousTime = new Date(previousMessage.created_at)
  
  // 如果时间差超过1小时，显示时间分组
  return currentTime.getTime() - previousTime.getTime() > 3600000
}

// 格式化时间分组
const formatTimeGroup = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  
  if (date.toDateString() === now.toDateString()) {
    return '今天'
  } else {
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000)
    if (date.toDateString() === yesterday.toDateString()) {
      return '昨天'
    } else {
      return date.toLocaleDateString('zh-CN', { 
        year: 'numeric',
        month: 'long', 
        day: 'numeric' 
      })
    }
  }
}

// 切换思考过程展开状态
const toggleThinkingProcess = (messageId: string) => {
  if (expandedThinking.value.has(messageId)) {
    expandedThinking.value.delete(messageId)
  } else {
    expandedThinking.value.add(messageId)
  }
}

// 流式消息事件处理
const handleStreamComplete = (message: Message, content: string) => {
  emit('streamComplete', message, content)
}

const handleThinkingChange = (message: Message, thinking: string) => {
  emit('thinkingChange', message, thinking)
}

const handleToolCall = (message: Message, tool: { name: string; description: string }) => {
  emit('toolCall', message, tool)
}

// 监听消息变化，自动滚动到底部
watch(() => props.messages.length, async () => {
  await nextTick()
  
  // 如果用户在底部附近，自动滚动
  if (!showScrollToBottom.value) {
    scrollToBottom()
  }
})

// 监听打字状态，自动滚动到底部
watch(() => props.isTyping, async (isTyping) => {
  if (isTyping) {
    await nextTick()
    scrollToBottom()
  }
})

// 生命周期
onMounted(() => {
  const container = messagesContainer.value
  if (!container) return
  
  // 监听滚动事件
  container.addEventListener('scroll', checkScrollToBottom)
  
  // 初始滚动到底部
  nextTick(() => {
    scrollToBottom(false)
  })
})

onUnmounted(() => {
  const container = messagesContainer.value
  if (container) {
    container.removeEventListener('scroll', checkScrollToBottom)
  }
})
</script>

<style scoped>
/* 滚动条样式 */
.overflow-y-auto::-webkit-scrollbar {
  @apply w-2;
}

.overflow-y-auto::-webkit-scrollbar-track {
  @apply bg-transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  @apply bg-border rounded-full;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  @apply bg-border/80;
}

/* 动画 */
@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.animate-bounce {
  animation: bounce 1.4s infinite ease-in-out both;
}

/* 消息气泡样式 */
.message-bubble {
  @apply p-3 rounded-lg break-words;
}

.message-user {
  @apply bg-primary text-primary-foreground;
}

.message-assistant {
  @apply bg-muted text-foreground;
}

.message-thinking {
  @apply bg-accent/50 text-accent-foreground border border-accent/50;
}

/* 代码块样式 */
.prose code {
  @apply bg-muted px-1 py-0.5 rounded text-sm;
}

.prose pre {
  @apply bg-muted p-3 rounded-lg overflow-x-auto;
}

.prose pre code {
  @apply bg-transparent p-0;
}

/* 响应式调整 */
@media (max-width: 640px) {
  .message-bubble {
    @apply max-w-[90%];
  }
}
</style>