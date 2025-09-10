import type { StreamMessage } from '@/types/chat'
import { ConnectionStatus } from '@/types/api'

// 连接配置
interface StreamConnectionConfig {
  onMessage?: (message: StreamMessage) => void
  onError?: (error: Event | Error) => void
  onOpen?: () => void
  onClose?: () => void
  onStatusChange?: (status: ConnectionStatus) => void
  maxReconnectAttempts?: number
  reconnectInterval?: number
}

// 连接信息
interface ConnectionInfo {
  id: string
  url: string
  eventSource: EventSource | null
  status: ConnectionStatus
  config: StreamConnectionConfig
  reconnectAttempts: number
  reconnectTimer: number | null
}

class StreamService {
  private connections = new Map<string, ConnectionInfo>()
  private defaultConfig: Required<StreamConnectionConfig> = {
    onMessage: () => {},
    onError: () => {},
    onOpen: () => {},
    onClose: () => {},
    onStatusChange: () => {},
    maxReconnectAttempts: 5,
    reconnectInterval: 3000
  }

  // 连接到SSE流
  connect(connectionId: string, config: StreamConnectionConfig): void {
    if (this.connections.has(connectionId)) {
      console.warn(`连接 ${connectionId} 已存在`)
      return
    }

    const fullConfig = { ...this.defaultConfig, ...config }
    const url = `/api/stream/events/${connectionId}`

    const connectionInfo: ConnectionInfo = {
      id: connectionId,
      url,
      eventSource: null,
      status: ConnectionStatus.DISCONNECTED,
      config: fullConfig,
      reconnectAttempts: 0,
      reconnectTimer: null
    }

    this.connections.set(connectionId, connectionInfo)
    this.establishConnection(connectionInfo)
  }

  // 建立SSE连接
  private establishConnection(connectionInfo: ConnectionInfo): void {
    const { id, url, config } = connectionInfo

    this.updateConnectionStatus(connectionInfo, ConnectionStatus.CONNECTING)

    try {
      const eventSource = new EventSource(url)

      connectionInfo.eventSource = eventSource

      // 连接打开事件
      eventSource.onopen = () => {
        console.log(`SSE连接已建立: ${id}`)
        connectionInfo.reconnectAttempts = 0
        this.updateConnectionStatus(connectionInfo, ConnectionStatus.CONNECTED)
        config.onOpen?.()
      }

      // 接收消息事件
      eventSource.onmessage = (event) => {
        try {
          const message: StreamMessage = JSON.parse(event.data)
          config.onMessage?.(message)
        } catch (error) {
          console.error('解析SSE消息失败:', error)
        }
      }

      // 自定义事件监听器
      this.setupCustomEventListeners(eventSource, config)

      // 连接错误事件
      eventSource.onerror = (error) => {
        console.error(`SSE连接错误: ${id}`, error)
        this.updateConnectionStatus(connectionInfo, ConnectionStatus.ERROR)
        config.onError?.(error)

        // 自动重连
        this.attemptReconnect(connectionInfo)
      }

    } catch (error) {
      console.error(`建立SSE连接失败: ${id}`, error)
      this.updateConnectionStatus(connectionInfo, ConnectionStatus.ERROR)
      config.onError?.(error as Error)
    }
  }

  // 设置自定义事件监听器
  private setupCustomEventListeners(
    eventSource: EventSource, 
    config: StreamConnectionConfig
  ): void {
    const eventTypes = [
      'message',
      'thinking', 
      'tool_call',
      'tool_response',
      'error',
      'heartbeat',
      'connection_status',
      'stream_start',
      'stream_end',
      'chunk'
    ]

    eventTypes.forEach(eventType => {
      eventSource.addEventListener(eventType, (event) => {
        try {
          const customEvent = event as MessageEvent
          const message: StreamMessage = JSON.parse(customEvent.data)
          config.onMessage?.(message)
        } catch (error) {
          console.error(`解析${eventType}事件失败:`, error)
        }
      })
    })
  }

  // 尝试重连
  private attemptReconnect(connectionInfo: ConnectionInfo): void {
    const { config, reconnectAttempts } = connectionInfo

    if (reconnectAttempts >= config.maxReconnectAttempts!) {
      console.error(`连接 ${connectionInfo.id} 重连次数已达上限`)
      this.updateConnectionStatus(connectionInfo, ConnectionStatus.ERROR)
      return
    }

    connectionInfo.reconnectAttempts++
    this.updateConnectionStatus(connectionInfo, ConnectionStatus.RECONNECTING)

    // 清理现有连接
    if (connectionInfo.eventSource) {
      connectionInfo.eventSource.close()
    }

    // 延迟重连
    connectionInfo.reconnectTimer = window.setTimeout(() => {
      console.log(`尝试重连 ${connectionInfo.id} (第${connectionInfo.reconnectAttempts}次)`)
      this.establishConnection(connectionInfo)
    }, config.reconnectInterval!)
  }

  // 更新连接状态
  private updateConnectionStatus(
    connectionInfo: ConnectionInfo, 
    status: ConnectionStatus
  ): void {
    connectionInfo.status = status
    connectionInfo.config.onStatusChange?.(status)
  }

  // 断开连接
  disconnect(connectionId: string): void {
    const connectionInfo = this.connections.get(connectionId)
    if (!connectionInfo) {
      console.warn(`连接 ${connectionId} 不存在`)
      return
    }

    // 清理重连定时器
    if (connectionInfo.reconnectTimer) {
      clearTimeout(connectionInfo.reconnectTimer)
    }

    // 关闭EventSource连接
    if (connectionInfo.eventSource) {
      connectionInfo.eventSource.close()
    }

    // 更新状态并触发回调
    this.updateConnectionStatus(connectionInfo, ConnectionStatus.DISCONNECTED)
    connectionInfo.config.onClose?.()

    // 移除连接
    this.connections.delete(connectionId)

    console.log(`SSE连接已断开: ${connectionId}`)
  }

  // 获取连接状态
  getConnectionStatus(connectionId: string): ConnectionStatus | null {
    const connectionInfo = this.connections.get(connectionId)
    return connectionInfo?.status || null
  }

  // 获取所有连接
  getAllConnections(): string[] {
    return Array.from(this.connections.keys())
  }

  // 断开所有连接
  disconnectAll(): void {
    for (const connectionId of this.connections.keys()) {
      this.disconnect(connectionId)
    }
  }

  // 检查浏览器是否支持SSE
  static isSupported(): boolean {
    return typeof EventSource !== 'undefined'
  }
}

// 创建全局流式服务实例
export const streamService = new StreamService()

// 导出类型
export type { StreamConnectionConfig, ConnectionInfo }