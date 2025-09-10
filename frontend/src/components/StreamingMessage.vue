<template>
  <div class="streaming-message">
    <!-- 连接状态指示器 -->
    <div 
      v-if="showConnectionStatus" 
      class="connection-status mb-2 flex items-center space-x-2 text-sm"
    >
      <div 
        class="status-dot w-2 h-2 rounded-full"
        :class="connectionStatusClass"
      ></div>
      <span :class="connectionStatusTextClass">
        {{ connectionStatusText }}
      </span>
    </div>

    <!-- 流式内容 -->
    <div class="streaming-content">
      <!-- 思考过程 -->
      <ThinkingDisplay
        v-if="thinkingSteps.length > 0 && showThinkingProcess"
        :steps="thinkingSteps"
        :progress="thinkingProgress"
        :show-progress="isStreaming"
        :show-animations="true"
        :default-expanded="false"
        class="mb-4"
        @step-click="handleThinkingStepClick"
        @visibility-change="handleThinkingVisibilityChange"
      />

      <!-- 工具调用 -->
      <div v-if="toolCalls.length > 0" class="tool-calls mb-4 space-y-2">
        <div 
          v-for="(tool, index) in toolCalls" 
          :key="index"
          class="tool-call p-2 bg-amber-50 dark:bg-amber-950/30 rounded border-l-4 border-amber-400"
        >
          <div class="flex items-center space-x-2">
            <Wrench class="w-4 h-4 text-amber-600" />
            <span class="text-sm font-medium text-amber-700 dark:text-amber-300">
              调用工具: {{ tool.name }}
            </span>
          </div>
          <div v-if="tool.description" class="text-xs text-amber-600 dark:text-amber-400 mt-1">
            {{ tool.description }}
          </div>
        </div>
      </div>

      <!-- 主要消息内容 -->
      <div class="message-content">
        <TypewriterText 
          :text="streamingContent" 
          :speed="typewriterSpeed"
          :is-streaming="isStreaming"
          class="prose prose-sm max-w-none dark:prose-invert"
          @typing-complete="handleTypingComplete"
        />
        
        <!-- 流式指示器 -->
        <div 
          v-if="isStreaming && streamingContent" 
          class="streaming-cursor inline-block w-2 h-4 bg-primary ml-1 animate-pulse"
        ></div>
      </div>

      <!-- 流式状态指示器 -->
      <div 
        v-if="isStreaming && !streamingContent"
        class="streaming-indicator flex items-center space-x-2 text-muted-foreground"
      >
        <div class="flex space-x-1">
          <div class="w-2 h-2 bg-current rounded-full animate-bounce" style="animation-delay: 0ms"></div>
          <div class="w-2 h-2 bg-current rounded-full animate-bounce" style="animation-delay: 150ms"></div>
          <div class="w-2 h-2 bg-current rounded-full animate-bounce" style="animation-delay: 300ms"></div>
        </div>
        <span class="text-sm">AI正在回复...</span>
      </div>
    </div>

    <!-- 错误状态 -->
    <div 
      v-if="hasError && errorMessage"
      class="error-section mt-2 p-3 bg-red-50 dark:bg-red-950/30 rounded-lg border-l-4 border-red-400"
    >
      <div class="flex items-center space-x-2">
        <AlertCircle class="w-4 h-4 text-red-500" />
        <span class="text-sm font-medium text-red-700 dark:text-red-300">
          连接错误
        </span>
      </div>
      <div class="text-sm text-red-600 dark:text-red-400 mt-1">
        {{ errorMessage }}
      </div>
      <button 
        v-if="canRetry"
        @click="handleRetry"
        class="mt-2 text-xs text-red-600 dark:text-red-400 underline hover:no-underline"
      >
        重新连接
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Brain, Wrench, AlertCircle } from 'lucide-vue-next'
import { useChatSSE } from '@/composables/useSSE'
import { ConnectionStatus } from '@/types/api'
import TypewriterText from './TypewriterText.vue'
import ThinkingDisplay, { type ThinkingStepData, type ThinkingProgress } from './ThinkingDisplay.vue'

export interface StreamingMessageProps {
  connectionId?: string
  showConnectionStatus?: boolean
  showThinkingProcess?: boolean
  typewriterSpeed?: number
  autoConnect?: boolean
  maxRetries?: number
  retryInterval?: number
}

const props = withDefaults(defineProps<StreamingMessageProps>(), {
  showConnectionStatus: true,
  showThinkingProcess: true,
  typewriterSpeed: 50,
  autoConnect: false,
  maxRetries: 3,
  retryInterval: 3000
})

const emit = defineEmits<{
  'connection-change': [status: ConnectionStatus | null]
  'message-complete': [content: string]
  'thinking-change': [thinking: string]
  'thinking-step-added': [step: ThinkingStepData]
  'thinking-step-click': [step: ThinkingStepData, stepIndex: number]
  'thinking-visibility-change': [visible: boolean]
  'tool-call': [toolCall: { name: string; description: string }]
  'error': [error: string]
}>()

// 使用聊天SSE Composable
const {
  streamingContent,
  isStreaming,
  currentThinking,
  toolCalls,
  isConnected,
  isConnecting,
  connectionStatus,
  startChat,
  stopChat,
  reconnect
} = useChatSSE()

// 内部状态
const errorMessage = ref('')
const retryCount = ref(0)
const showRetryButton = ref(false)
const thinkingSteps = ref<ThinkingStepData[]>([])
const thinkingProgress = ref<ThinkingProgress | null>(null)

// 计算属性
const hasError = computed(() => 
  connectionStatus.value === ConnectionStatus.ERROR || !!errorMessage.value
)

const canRetry = computed(() => 
  hasError.value && retryCount.value < props.maxRetries
)

const connectionStatusClass = computed(() => ({
  'bg-green-500': isConnected.value,
  'bg-yellow-500': isConnecting.value,
  'bg-red-500': hasError.value,
  'bg-gray-400': !connectionStatus.value
}))

const connectionStatusTextClass = computed(() => ({
  'text-green-600 dark:text-green-400': isConnected.value,
  'text-yellow-600 dark:text-yellow-400': isConnecting.value,
  'text-red-600 dark:text-red-400': hasError.value,
  'text-gray-500': !connectionStatus.value
}))

const connectionStatusText = computed(() => {
  if (isConnected.value) return '已连接'
  if (isConnecting.value) return '连接中...'
  if (hasError.value) return '连接失败'
  return '未连接'
})

// 方法
const handleTypingComplete = () => {
  if (streamingContent.value) {
    emit('message-complete', streamingContent.value)
  }
}

const handleRetry = async () => {
  if (!canRetry.value) return
  
  retryCount.value++
  errorMessage.value = ''
  
  try {
    if (props.connectionId) {
      await startChat(props.connectionId)
    } else {
      reconnect()
    }
  } catch (error) {
    console.error('重连失败:', error)
    errorMessage.value = error instanceof Error ? error.message : '重连失败'
  }
}

const connectToStream = async (connectionId: string) => {
  try {
    errorMessage.value = ''
    await startChat(connectionId)
    retryCount.value = 0
  } catch (error) {
    console.error('连接流失败:', error)
    errorMessage.value = error instanceof Error ? error.message : '连接失败'
    emit('error', errorMessage.value)
  }
}

// 思考过程处理
const parseThinkingContent = (thinkingText: string): ThinkingStepData[] => {
  // 简单的思考过程解析逻辑
  // 实际项目中可能需要更复杂的解析
  const lines = thinkingText.split('\n').filter(line => line.trim())
  const steps: ThinkingStepData[] = []
  
  lines.forEach((line, index) => {
    const step: ThinkingStepData = {
      title: `思考步骤 ${index + 1}`,
      content: line,
      type: 'reasoning',
      confidence: Math.random() * 0.4 + 0.6, // 模拟置信度
      timestamp: new Date().toISOString()
    }
    steps.push(step)
  })
  
  return steps
}

const updateThinkingProgress = () => {
  if (thinkingSteps.value.length === 0) {
    thinkingProgress.value = null
    return
  }
  
  const completedSteps = thinkingSteps.value.filter(step => !step.error).length
  thinkingProgress.value = {
    currentStep: completedSteps,
    totalSteps: thinkingSteps.value.length,
    percentage: (completedSteps / thinkingSteps.value.length) * 100
  }
}

const handleThinkingStepClick = (step: ThinkingStepData, stepIndex: number) => {
  emit('thinking-step-click', step, stepIndex)
}

const handleThinkingVisibilityChange = (visible: boolean) => {
  emit('thinking-visibility-change', visible)
}

// 监听器
watch(() => props.connectionId, (newId, oldId) => {
  if (newId !== oldId) {
    if (oldId) {
      stopChat()
    }
    if (newId) {
      connectToStream(newId)
    }
  }
})

watch(connectionStatus, (status) => {
  emit('connection-change', status)
  
  if (status === ConnectionStatus.ERROR && canRetry.value) {
    setTimeout(handleRetry, props.retryInterval)
  }
})

watch(currentThinking, (thinking) => {
  emit('thinking-change', thinking)
  
  // 解析思考内容为步骤
  if (thinking) {
    const steps = parseThinkingContent(thinking)
    thinkingSteps.value = steps
    updateThinkingProgress()
    
    // 发出新步骤事件
    steps.forEach((step, index) => {
      if (index >= thinkingSteps.value.length - steps.length) {
        emit('thinking-step-added', step)
      }
    })
  }
})

watch(toolCalls, (calls) => {
  const lastCall = calls[calls.length - 1]
  if (lastCall) {
    emit('tool-call', lastCall)
  }
}, { deep: true })

// 生命周期
onMounted(() => {
  if (props.autoConnect && props.connectionId) {
    connectToStream(props.connectionId)
  }
})

onUnmounted(() => {
  stopChat()
})

// 暴露方法给父组件
defineExpose({
  connect: connectToStream,
  disconnect: stopChat,
  reconnect: handleRetry,
  isConnected,
  isStreaming,
  hasError
})
</script>

<style scoped>
.streaming-cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.streaming-indicator .animate-bounce {
  animation-duration: 1s;
  animation-iteration-count: infinite;
}

.thinking-content {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
}

/* 响应式调整 */
@media (max-width: 640px) {
  .connection-status {
    @apply text-xs;
  }
  
  .thinking-section,
  .tool-call,
  .error-section {
    @apply p-2;
  }
}

/* 暗色模式适配 */
.dark .streaming-cursor {
  @apply bg-primary;
}

/* 打字机效果的平滑过渡 */
.prose {
  transition: all 0.2s ease-in-out;
}

/* 工具调用动画 */
.tool-call {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 思考过程动画 */
.thinking-section {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>