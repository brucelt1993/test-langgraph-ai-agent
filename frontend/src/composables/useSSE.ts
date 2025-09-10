/**
 * SSE (Server-Sent Events) 客户端Composable
 * 
 * 提供完整的SSE连接管理、自动重连、错误处理等功能
 */

import { ref, onUnmounted, computed, readonly, type Ref } from 'vue'
import { streamService } from '@/services/stream'
import { ConnectionStatus } from '@/types/api'
import type { StreamMessage } from '@/types/chat'

export interface UseSSEOptions {
  onMessage?: (message: StreamMessage) => void
  onError?: (error: Event | Error) => void
  onOpen?: () => void
  onClose?: () => void
  maxReconnectAttempts?: number
  reconnectInterval?: number
  autoConnect?: boolean
  headers?: Record<string, string>
  timeout?: number
  debug?: boolean
}

export interface UseSSEReturn {
  // 状态
  connectionStatus: Readonly<Ref<ConnectionStatus | null>>
  isConnected: Readonly<Ref<boolean>>
  isConnecting: Readonly<Ref<boolean>>
  isReconnecting: Readonly<Ref<boolean>>
  hasError: Readonly<Ref<boolean>>
  connectionId: Readonly<Ref<string | null>>
  
  // 方法
  connect: (connectionId: string) => Promise<void>
  disconnect: () => void
  reconnect: () => void
  
  // 消息收发
  messages: Readonly<Ref<StreamMessage[]>>
  lastMessage: Readonly<Ref<StreamMessage | null>>
  clearMessages: () => void
  
  // 连接信息
  connectionInfo: Readonly<Ref<{
    connected: boolean
    connectionTime?: Date
    lastMessageTime?: Date
    reconnectAttempts: number
    totalMessages: number
  }>>
}

/**
 * SSE客户端Composable
 */
export function useSSE(options: UseSSEOptions = {}): UseSSEReturn {
  // 响应式状态
  const connectionStatus = ref<ConnectionStatus | null>(null)
  const connectionId = ref<string | null>(null)
  const messages = ref<StreamMessage[]>([])
  const lastMessage = ref<StreamMessage | null>(null)
  const connectionTime = ref<Date | null>(null)
  const lastMessageTime = ref<Date | null>(null)
  const reconnectAttempts = ref(0)
  
  // 计算属性
  const isConnected = computed(() => 
    connectionStatus.value === ConnectionStatus.CONNECTED
  )
  
  const isConnecting = computed(() => 
    connectionStatus.value === ConnectionStatus.CONNECTING
  )
  
  const isReconnecting = computed(() => 
    connectionStatus.value === ConnectionStatus.RECONNECTING
  )
  
  const hasError = computed(() => 
    connectionStatus.value === ConnectionStatus.ERROR
  )
  
  const connectionInfo = computed(() => ({
    connected: isConnected.value,
    connectionTime: connectionTime.value || undefined,
    lastMessageTime: lastMessageTime.value || undefined,
    reconnectAttempts: reconnectAttempts.value,
    totalMessages: messages.value.length
  }))

  // 消息处理
  const handleMessage = (message: StreamMessage) => {
    messages.value.push(message)
    lastMessage.value = message
    lastMessageTime.value = new Date()
    
    // 调用外部回调
    options.onMessage?.(message)
  }

  // 错误处理
  const handleError = (error: Event | Error) => {
    console.error('SSE连接错误:', error)
    options.onError?.(error)
  }

  // 连接打开处理
  const handleOpen = () => {
    connectionTime.value = new Date()
    reconnectAttempts.value = 0
    options.onOpen?.()
  }

  // 连接关闭处理
  const handleClose = () => {
    connectionTime.value = null
    options.onClose?.()
  }

  // 状态变化处理
  const handleStatusChange = (status: ConnectionStatus) => {
    connectionStatus.value = status
    
    if (status === ConnectionStatus.RECONNECTING) {
      reconnectAttempts.value++
    }
  }

  // 连接到SSE流
  const connect = async (connId: string) => {
    if (connectionId.value) {
      disconnect()
    }

    connectionId.value = connId
    
    try {
      streamService.connect(connId, {
        onMessage: handleMessage,
        onError: handleError,
        onOpen: handleOpen,
        onClose: handleClose,
        onStatusChange: handleStatusChange,
        maxReconnectAttempts: options.maxReconnectAttempts || 5,
        reconnectInterval: options.reconnectInterval || 3000
      })
    } catch (error) {
      console.error('连接SSE失败:', error)
      handleError(error as Error)
    }
  }

  // 断开连接
  const disconnect = () => {
    if (connectionId.value) {
      streamService.disconnect(connectionId.value)
      connectionId.value = null
      connectionStatus.value = ConnectionStatus.DISCONNECTED
      connectionTime.value = null
    }
  }

  // 重新连接
  const reconnect = () => {
    if (connectionId.value) {
      const connId = connectionId.value
      disconnect()
      setTimeout(() => {
        connect(connId)
      }, 1000)
    }
  }

  // 清空消息
  const clearMessages = () => {
    messages.value = []
    lastMessage.value = null
    lastMessageTime.value = null
  }

  // 组件卸载时清理
  onUnmounted(() => {
    disconnect()
  })

  return {
    // 状态
    connectionStatus: readonly(connectionStatus),
    isConnected: readonly(isConnected),
    isConnecting: readonly(isConnecting),
    isReconnecting: readonly(isReconnecting),
    hasError: readonly(hasError),
    connectionId: readonly(connectionId),
    
    // 方法
    connect,
    disconnect,
    reconnect,
    
    // 消息
    messages: messages as Readonly<Ref<StreamMessage[]>>,
    lastMessage: readonly(lastMessage),
    clearMessages,
    
    // 连接信息
    connectionInfo: readonly(connectionInfo)
  }
}

/**
 * 用于单次SSE连接的简化版本
 */
export function useSimpleSSE(
  connectionId: string, 
  onMessage: (message: StreamMessage) => void
) {
  const sse = useSSE({
    onMessage,
    autoConnect: true
  })

  // 自动连接
  if (connectionId) {
    sse.connect(connectionId)
  }

  return {
    isConnected: sse.isConnected,
    isConnecting: sse.isConnecting,
    connectionStatus: sse.connectionStatus,
    disconnect: sse.disconnect,
    reconnect: sse.reconnect
  }
}

/**
 * 用于监听特定事件类型的SSE Hook
 */
export function useSSEEventListener(
  connectionId: string,
  eventTypes: string[],
  handler: (eventType: string, data: any) => void
) {
  return useSSE({
    onMessage: (message) => {
      if (eventTypes.includes(message.type)) {
        handler(message.type, message.data)
      }
    }
  })
}

/**
 * 用于聊天流式响应的专用Hook
 */
export function useChatSSE() {
  const streamingContent = ref('')
  const isStreaming = ref(false)
  const currentThinking = ref<string>('')
  const toolCalls = ref<Array<{ name: string, description: string }>>([])

  const sse = useSSE({
    onMessage: (message) => {
      switch (message.type) {
        case 'message':
          if (message.is_partial) {
            streamingContent.value += message.content || ''
          } else {
            streamingContent.value = message.content || ''
          }
          isStreaming.value = true
          break

        case 'thinking':
          currentThinking.value = message.content || ''
          break

        case 'tool_call':
          if (message.tool_call) {
            toolCalls.value.push({
              name: message.tool_call.name,
              description: message.tool_call.description || ''
            })
          }
          break

        case 'stream_end':
          isStreaming.value = false
          break

        case 'error':
          console.error('聊天流错误:', message.data)
          isStreaming.value = false
          break
      }
    }
  })

  const startChat = async (connectionId: string) => {
    streamingContent.value = ''
    isStreaming.value = false
    currentThinking.value = ''
    toolCalls.value = []
    
    await sse.connect(connectionId)
  }

  const stopChat = () => {
    sse.disconnect()
    isStreaming.value = false
  }

  return {
    // 聊天特定状态
    streamingContent: readonly(streamingContent),
    isStreaming: readonly(isStreaming),
    currentThinking: readonly(currentThinking),
    toolCalls: readonly(toolCalls),
    
    // 连接状态
    isConnected: sse.isConnected,
    isConnecting: sse.isConnecting,
    connectionStatus: sse.connectionStatus,
    
    // 方法
    startChat,
    stopChat,
    reconnect: sse.reconnect
  }
}