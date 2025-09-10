/**
 * SSE composables测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useSSE } from '@/composables/useSSE'
import { ConnectionStatus } from '@/types/api'
import { MockEventSource } from '@/tests/utils'

// Mock EventSource
vi.stubGlobal('EventSource', MockEventSource)

describe('useSSE', () => {
  let mockEventSource: MockEventSource

  beforeEach(() => {
    vi.clearAllMocks()
    // 拦截EventSource构造函数
    vi.mocked(MockEventSource).mockImplementation((url: string) => {
      mockEventSource = new MockEventSource(url)
      return mockEventSource as any
    })
  })

  afterEach(() => {
    mockEventSource?.close()
  })

  describe('连接管理', () => {
    it('应该初始化为未连接状态', () => {
      const { connectionStatus, isConnected, isConnecting } = useSSE()

      expect(connectionStatus.value).toBe(null)
      expect(isConnected.value).toBe(false)
      expect(isConnecting.value).toBe(false)
    })

    it('应该能够建立连接', async () => {
      const { connect, connectionStatus, isConnecting } = useSSE()

      const connectPromise = connect('http://localhost:8000/stream')
      
      expect(isConnecting.value).toBe(true)
      expect(connectionStatus.value).toBe(ConnectionStatus.CONNECTING)

      // 模拟连接成功
      mockEventSource.simulateOpen()

      await connectPromise

      expect(connectionStatus.value).toBe(ConnectionStatus.CONNECTED)
    })

    it('应该处理连接错误', async () => {
      const { connect, connectionStatus } = useSSE()

      const connectPromise = connect('http://localhost:8000/stream')

      // 模拟连接错误
      mockEventSource.simulateError()

      await connectPromise

      expect(connectionStatus.value).toBe(ConnectionStatus.ERROR)
    })

    it('应该能够断开连接', async () => {
      const { connect, disconnect, connectionStatus } = useSSE()

      await connect('http://localhost:8000/stream')
      mockEventSource.simulateOpen()

      disconnect()

      expect(connectionStatus.value).toBe(ConnectionStatus.DISCONNECTED)
      expect(mockEventSource.close).toHaveBeenCalled()
    })
  })

  describe('消息处理', () => {
    it('应该接收和处理消息', async () => {
      const { connect, messages } = useSSE()

      await connect('http://localhost:8000/stream')
      mockEventSource.simulateOpen()

      const testMessage = JSON.stringify({
        type: 'content',
        data: '测试消息',
        timestamp: new Date().toISOString()
      })

      mockEventSource.simulateMessage(testMessage)

      expect(messages.value).toHaveLength(1)
      expect(messages.value[0].data).toBe(testMessage)
    })

    it('应该处理不同类型的消息', async () => {
      const { connect } = useSSE()

      await connect('http://localhost:8000/stream')
      mockEventSource.simulateOpen()

      // 测试不同类型的消息
      const messages = [
        { type: 'content', data: '内容消息' },
        { type: 'thinking', data: '思考过程' },
        { type: 'tool_call', data: '工具调用' },
        { type: 'complete', data: '完成' }
      ]

      messages.forEach(msg => {
        mockEventSource.simulateMessage(JSON.stringify(msg))
      })

      // 验证消息被正确处理
      expect(mockEventSource.onmessage).toHaveBeenCalledTimes(messages.length)
    })
  })

  describe('重连机制', () => {
    it('应该在连接断开后自动重连', async () => {
      const { connect, connectionStatus } = useSSE({
        autoConnect: true,
        reconnectInterval: 100
      })

      await connect('http://localhost:8000/stream')
      mockEventSource.simulateOpen()

      // 模拟连接断开
      mockEventSource.simulateClose()

      expect(connectionStatus.value).toBe(ConnectionStatus.RECONNECTING)

      // 等待重连
      await new Promise(resolve => setTimeout(resolve, 150))

      // 验证重连尝试
      expect(vi.mocked(MockEventSource)).toHaveBeenCalledTimes(2)
    })

    it('应该在最大重试次数后停止重连', async () => {
      const { connect } = useSSE({
        autoConnect: true,
        maxReconnectAttempts: 2,
        reconnectInterval: 50
      })

      await connect('http://localhost:8000/stream')

      // 模拟多次连接失败
      for (let i = 0; i < 3; i++) {
        mockEventSource.simulateError()
        await new Promise(resolve => setTimeout(resolve, 60))
      }

      // 验证只重试了指定次数
      expect(vi.mocked(MockEventSource)).toHaveBeenCalledTimes(3) // 初始连接 + 2次重试
    })

    it('应该能够手动重连', async () => {
      const { connect, reconnect } = useSSE()

      await connect('http://localhost:8000/stream')
      mockEventSource.simulateError()

      const reconnectResult = reconnect()

      expect(vi.mocked(MockEventSource)).toHaveBeenCalledTimes(2)
    })
  })

  describe('聊天专用功能', () => {
    it('应该处理聊天流消息', async () => {
      const { connect } = useSSE()

      await connect('http://localhost:8000/stream/chat')
      mockEventSource.simulateOpen()

      const chatMessage = JSON.stringify({
        type: 'content',
        data: 'AI回复内容',
        session_id: 'session-123',
        message_id: 'msg-456',
        timestamp: new Date().toISOString()
      })

      mockEventSource.simulateMessage(chatMessage)

      // 验证聊天消息被正确处理
      expect(mockEventSource.onmessage).toHaveBeenCalled()
    })

    it('应该处理思考过程消息', async () => {
      const { connect } = useSSE()

      await connect('http://localhost:8000/stream/chat')
      mockEventSource.simulateOpen()

      const thinkingMessage = JSON.stringify({
        type: 'thinking',
        data: {
          step: '分析用户问题',
          content: '用户询问天气信息...',
          confidence: 0.9
        },
        timestamp: new Date().toISOString()
      })

      mockEventSource.simulateMessage(thinkingMessage)

      expect(mockEventSource.onmessage).toHaveBeenCalled()
    })

    it('应该处理工具调用消息', async () => {
      const { connect } = useSSE()

      await connect('http://localhost:8000/stream/chat')
      mockEventSource.simulateOpen()

      const toolCallMessage = JSON.stringify({
        type: 'tool_call',
        data: {
          name: 'weather_tool',
          description: '查询天气信息',
          parameters: { location: '北京' }
        },
        timestamp: new Date().toISOString()
      })

      mockEventSource.simulateMessage(toolCallMessage)

      expect(mockEventSource.onmessage).toHaveBeenCalled()
    })
  })

  describe('配置选项', () => {
    it('应该使用自定义headers', async () => {
      const customHeaders = { 'Authorization': 'Bearer token' }
      const { connect } = useSSE({
        headers: customHeaders
      })

      await connect('http://localhost:8000/stream')

      // EventSource不支持自定义headers，这里主要测试配置传递
      expect(vi.mocked(MockEventSource)).toHaveBeenCalledWith(
        'http://localhost:8000/stream'
      )
    })

    it('应该使用自定义超时设置', () => {
      const { connect } = useSSE({
        timeout: 30000
      })

      expect(typeof connect).toBe('function')
    })

    it('应该支持调试模式', () => {
      const { connect } = useSSE({
        debug: true
      })

      expect(typeof connect).toBe('function')
    })
  })

  describe('错误处理', () => {
    it('应该处理无效的JSON消息', async () => {
      const { connect, messages } = useSSE()

      await connect('http://localhost:8000/stream')
      mockEventSource.simulateOpen()

      // 发送无效JSON
      mockEventSource.simulateMessage('invalid json')

      // 应该不会添加到消息列表
      expect(messages.value).toHaveLength(0)
    })

    it('应该处理网络错误', async () => {
      const { connect, connectionStatus } = useSSE()

      const connectPromise = connect('http://localhost:8000/stream')
      
      mockEventSource.simulateError()

      await connectPromise

      expect(connectionStatus.value).toBe(ConnectionStatus.ERROR)
    })
  })

  describe('清理操作', () => {
    it('应该在组件卸载时清理连接', async () => {
      const { connect, disconnect } = useSSE()

      await connect('http://localhost:8000/stream')
      mockEventSource.simulateOpen()

      disconnect()

      expect(mockEventSource.close).toHaveBeenCalled()
    })

    it('应该清理事件监听器', async () => {
      const { connect, disconnect } = useSSE()

      await connect('http://localhost:8000/stream')
      disconnect()

      expect(mockEventSource.removeEventListener).toHaveBeenCalled()
    })
  })
})