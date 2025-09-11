import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { apiClient } from '@/services/api'
import { streamService } from '@/services/stream'
import type { 
  ChatSession, 
  Message, 
  SendMessageRequest, 
  CreateSessionRequest,
  StreamMessage 
} from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const sessions = ref<ChatSession[]>([])
  const currentSession = ref<ChatSession | null>(null)
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const isSending = ref(false)
  const streamConnection = ref<string | null>(null)

  // 计算属性
  const activeSessions = computed(() => 
    sessions.value.filter(session => session.is_active)
  )
  
  const currentMessages = computed(() => 
    messages.value.filter(msg => msg.session_id === currentSession.value?.id)
  )

  // 获取会话列表
  const fetchSessions = async (page = 1, size = 20) => {
    isLoading.value = true
    try {
      const response = await apiClient.get('/chat/sessions', {
        params: { page, size }
      })
      sessions.value = response.sessions
    } catch (error) {
      console.error('获取会话列表失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // 创建新会话
  const createSession = async (data: CreateSessionRequest): Promise<ChatSession> => {
    try {
      const session = await apiClient.post('/chat/sessions', data)
      sessions.value.unshift(session)
      return session
    } catch (error) {
      console.error('创建会话失败:', error)
      throw error
    }
  }

  // 获取指定会话
  const getSession = async (sessionId: string): Promise<void> => {
    try {
      const session = await apiClient.get(`/chat/sessions/${sessionId}`)
      currentSession.value = session
      
      // 同时获取会话消息
      await fetchSessionMessages(sessionId)
    } catch (error) {
      console.error('获取会话失败:', error)
      throw error
    }
  }

  // 获取会话消息
  const fetchSessionMessages = async (sessionId: string, page = 1, size = 50) => {
    try {
      const sessionMessages = await apiClient.get(`/chat/sessions/${sessionId}/messages`, {
        params: { page, size }
      })
      
      // 更新消息列表
      const existingMessages = messages.value.filter(msg => msg.session_id !== sessionId)
      messages.value = [...existingMessages, ...sessionMessages]
    } catch (error) {
      console.error('获取会话消息失败:', error)
      throw error
    }
  }

  // 发送消息（使用SSE流式响应）
  const sendMessage = async (sessionId: string, content: string, metadata?: any): Promise<void> => {
    if (!currentSession.value || isSending.value) return

    isSending.value = true
    
    try {
      // 创建用户消息
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        session_id: sessionId,
        content,
        message_type: 'user',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: metadata || {}
      }
      
      // 立即添加用户消息到界面
      messages.value.push(userMessage)
      
      // 创建SSE连接并发送消息
      const response = await apiClient.post(`/stream/chat/${sessionId}/stream`, {
        content,
        metadata
      })
      
      streamConnection.value = response.connection_id
      
      // 监听流式响应
      streamService.connect(response.connection_id, {
        onMessage: (message: StreamMessage) => {
          handleStreamMessage(message)
        },
        onError: (error: any) => {
          console.error('流式响应错误:', error)
        },
        onClose: () => {
          streamConnection.value = null
          isSending.value = false
        }
      })
      
    } catch (error) {
      console.error('发送消息失败:', error)
      isSending.value = false
      throw error
    }
  }

  // 处理流式消息
  const handleStreamMessage = (streamMsg: StreamMessage) => {
    const { type, data } = streamMsg

    switch (type) {
      case 'thinking':
        // 处理AI思考过程
        updateThinkingProcess(data)
        break
        
      case 'tool_call':
        // 处理工具调用
        updateToolCall(data)
        break
        
      case 'message':
        // 处理AI响应消息
        if (data.message_type === 'assistant') {
          updateAssistantMessage(data)
        }
        break
        
      case 'stream_end':
        // 流结束，刷新消息列表
        if (currentSession.value) {
          fetchSessionMessages(currentSession.value.id)
        }
        isSending.value = false
        break
        
      case 'error':
        console.error('流式响应错误:', data)
        isSending.value = false
        break
    }
  }

  // 更新思考过程
  const updateThinkingProcess = (data: any) => {
    // 在界面中显示AI思考过程
    console.log('AI思考:', data)
  }

  // 更新工具调用
  const updateToolCall = (data: any) => {
    // 在界面中显示工具调用信息
    console.log('工具调用:', data)
  }

  // 更新AI消息
  const updateAssistantMessage = (data: any) => {
    const existingMessageIndex = messages.value.findIndex(
      msg => msg.id === data.id
    )
    
    if (existingMessageIndex >= 0) {
      // 更新现有消息
      messages.value[existingMessageIndex] = { ...messages.value[existingMessageIndex], ...data }
    } else {
      // 添加新消息
      messages.value.push(data)
    }
  }

  // 更新会话
  const updateSession = async (sessionId: string, data: Partial<ChatSession>): Promise<void> => {
    try {
      const updatedSession = await apiClient.put(`/chat/sessions/${sessionId}`, data)
      
      // 更新本地会话
      const sessionIndex = sessions.value.findIndex(s => s.id === sessionId)
      if (sessionIndex >= 0) {
        sessions.value[sessionIndex] = updatedSession
      }
      
      if (currentSession.value?.id === sessionId) {
        currentSession.value = updatedSession
      }
    } catch (error) {
      console.error('更新会话失败:', error)
      throw error
    }
  }

  // 删除会话
  const deleteSession = async (sessionId: string): Promise<void> => {
    try {
      await apiClient.delete(`/chat/sessions/${sessionId}`)
      
      // 从本地移除
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      messages.value = messages.value.filter(m => m.session_id !== sessionId)
      
      if (currentSession.value?.id === sessionId) {
        currentSession.value = null
      }
    } catch (error) {
      console.error('删除会话失败:', error)
      throw error
    }
  }

  // 获取会话统计
  const getSessionStats = async (sessionId: string) => {
    try {
      const stats = await apiClient.get(`/chat/sessions/${sessionId}/stats`)
      return stats
    } catch (error) {
      console.error('获取会话统计失败:', error)
      throw error
    }
  }

  // 更新消息内容
  const updateMessageContent = (messageId: string, content: string) => {
    const messageIndex = messages.value.findIndex(msg => msg.id === messageId)
    if (messageIndex >= 0) {
      messages.value[messageIndex].content = content
    }
  }

  // 断开流式连接
  const disconnectStream = () => {
    if (streamConnection.value) {
      streamService.disconnect(streamConnection.value)
      streamConnection.value = null
    }
    isSending.value = false
  }

  // 清理状态
  const clearState = () => {
    sessions.value = []
    currentSession.value = null
    messages.value = []
    disconnectStream()
  }

  return {
    // 状态
    sessions: readonly(sessions),
    currentSession: readonly(currentSession),
    messages: readonly(messages),
    isLoading: readonly(isLoading),
    isSending: readonly(isSending),
    
    // 计算属性
    activeSessions,
    currentMessages,
    
    // 方法
    fetchSessions,
    createSession,
    getSession,
    fetchSessionMessages,
    sendMessage,
    updateSession,
    deleteSession,
    getSessionStats,
    updateMessageContent,
    disconnectStream,
    clearState
  }
})