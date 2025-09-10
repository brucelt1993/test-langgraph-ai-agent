// 聊天相关类型
export interface ChatSession {
  id: string
  user_id: string
  title: string
  agent_name: string
  is_active: boolean
  created_at: string
  updated_at: string
  last_message_at?: string
  message_count: number
  context: Record<string, any>
  metadata: Record<string, any>
  // 扩展属性
  tags?: string[]
  last_message?: Message
}

export interface Message {
  id: string
  session_id: string
  content: string
  message_type: 'user' | 'assistant' | 'system' | 'tool_call' | 'tool_response' | 'thinking'
  created_at: string
  updated_at: string
  metadata: Record<string, any>
  thinking_process?: Record<string, any>
  tool_calls?: Array<Record<string, any>>
  confidence_score?: number
  // 流式消息相关属性
  is_streaming?: boolean
  stream_connection_id?: string
}

export interface CreateSessionRequest {
  title?: string
  agent_name: string
  context?: Record<string, any>
}

export interface SendMessageRequest {
  content: string
  metadata?: Record<string, any>
}

export interface StreamMessage {
  type: 'message' | 'thinking' | 'tool_call' | 'tool_response' | 'error' | 'heartbeat' | 'connection_status' | 'stream_start' | 'stream_end' | 'chunk'
  content?: string
  data: Record<string, any>
  timestamp: string
  thinking_step?: Record<string, any>
  tool_call?: Record<string, any>
  is_partial?: boolean
  sequence_id?: number
}

export interface SessionListResponse {
  sessions: ChatSession[]
  total: number
  page: number
  size: number
  pages: number
}

export interface SessionStatsResponse {
  session_id: string
  message_count: number
  user_message_count: number
  assistant_message_count: number
  thinking_step_count: number
  tool_call_count: number
  average_response_time?: number
  total_conversation_time?: number
  first_message_at?: string
  last_message_at?: string
  context_rounds: number
}

// Agent相关类型
export interface AgentCapability {
  name: string
  description: string
  tools: string[]
}

export interface AgentInfo {
  name: string
  display_name: string
  description: string
  capabilities: AgentCapability[]
  is_available: boolean
  metadata: Record<string, any>
}