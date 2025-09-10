// ==================== 通用类型 ====================

// 分页响应类型
export interface PaginationResponse<T> {
  data: T[]
  total: number
  page: number
  size: number
  pages: number
}

// API响应包装器
export interface ApiResponse<T = any> {
  data?: T
  message?: string
  success?: boolean
}

// 通用错误响应
export interface ApiError {
  message: string
  detail?: string | string[]
  code?: string
}

// ==================== 认证相关类型 ====================

// 用户注册请求
export interface UserRegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

// 用户登录请求
export interface UserLoginRequest {
  username: string // 用户名或邮箱
  password: string
}

// Token响应
export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number // 秒
}

// 刷新Token请求
export interface RefreshTokenRequest {
  refresh_token: string
}

// 用户角色信息
export interface UserRole {
  id: string
  name: string
  display_name: string
  permissions: string | string[]
}

// 用户响应
export interface UserResponse {
  id: string
  username: string
  email: string
  full_name?: string
  is_active: boolean
  is_verified: boolean
  role: UserRole
  created_at: string
  last_login_at?: string
}

// 修改密码请求
export interface PasswordChangeRequest {
  current_password: string
  new_password: string
}

// 用户会话信息
export interface UserSession {
  id: string
  device_info: string
  ip_address: string
  created_at: string
  last_used_at: string
  expires_at: string
}

// 用户会话列表响应
export interface UserSessionsResponse {
  sessions: UserSession[]
}

// ==================== 聊天相关类型 ====================

// 消息类型枚举
export enum MessageType {
  USER = 'user',
  AI = 'ai',
  SYSTEM = 'system',
  TOOL = 'tool'
}

// 聊天会话创建请求
export interface ChatSessionCreate {
  title: string
  agent_name: string
  context?: Record<string, any>
}

// 聊天会话更新请求
export interface ChatSessionUpdate {
  title?: string
  context?: Record<string, any>
}

// 聊天会话响应
export interface ChatSessionResponse {
  id: string
  user_id: string
  title: string
  agent_name: string
  context: Record<string, any>
  is_active: boolean
  message_count: number
  last_message_at?: string
  created_at: string
  updated_at: string
}

// 聊天会话列表响应
export interface ChatSessionListResponse {
  sessions: ChatSessionResponse[]
  total: number
  page: number
  size: number
  pages: number
}

// 聊天会话统计信息
export interface ChatSessionStatsResponse {
  total_messages: number
  total_tokens?: number
  avg_response_time?: number
  first_message_at?: string
  last_message_at?: string
  user_message_count: number
  ai_message_count: number
  session_duration?: number // 分钟
}

// 消息创建请求
export interface MessageCreate {
  session_id: string
  type: MessageType
  content: string
  metadata?: Record<string, any>
  thinking_steps?: ThinkingStep[]
}

// 消息更新请求
export interface MessageUpdate {
  content?: string
  metadata?: Record<string, any>
}

// 思考步骤
export interface ThinkingStep {
  id: string
  title: string
  content: string
  type: 'reasoning' | 'planning' | 'analysis' | 'decision'
  confidence?: number
  timestamp: string
  error?: boolean
}

// 消息响应
export interface MessageResponse {
  id: string
  session_id: string
  type: MessageType
  content: string
  metadata: Record<string, any>
  thinking_steps: ThinkingStep[]
  created_at: string
  updated_at: string
}

// 发送消息请求
export interface SendMessageRequest {
  session_id: string
  content: string
  metadata?: Record<string, any>
}

// 流式响应消息
export interface StreamingMessage {
  type: 'content' | 'thinking' | 'tool_call' | 'error' | 'complete'
  data: any
  session_id?: string
  message_id?: string
  timestamp: string
}

// 工具调用信息
export interface ToolCall {
  name: string
  description: string
  parameters?: Record<string, any>
  result?: any
}

// ==================== SSE流式相关类型 ====================

// SSE连接状态
export enum ConnectionStatus {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

// SSE流消息
export interface StreamMessage {
  id?: string
  event?: string
  data: string
  retry?: number
}

// 流式连接配置
export interface StreamConfig {
  url: string
  headers?: Record<string, string>
  withCredentials?: boolean
  retryInterval?: number
  maxRetries?: number
}

// ==================== 天气Agent相关类型 ====================

// 天气查询请求
export interface WeatherQueryRequest {
  location: string
  language?: 'zh' | 'en'
  units?: 'metric' | 'imperial'
}

// 天气信息
export interface WeatherInfo {
  location: string
  temperature: number
  description: string
  humidity: number
  wind_speed: number
  pressure: number
  feels_like: number
  visibility?: number
  uv_index?: number
  timestamp: string
}

// 天气查询响应
export interface WeatherQueryResponse {
  weather: WeatherInfo
  forecast?: WeatherInfo[]
  query_time: string
  source: string
}

// ==================== 通知相关类型 ====================

// 通知类型
export enum NotificationType {
  SUCCESS = 'success',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

// 通知消息
export interface NotificationMessage {
  id: string
  type: NotificationType
  title: string
  message: string
  duration?: number
  timestamp: string
}

// ==================== 文件上传相关类型 ====================

// 文件上传配置
export interface FileUploadConfig {
  maxSize?: number // bytes
  allowedTypes?: string[]
  multiple?: boolean
}

// 文件上传进度
export interface FileUploadProgress {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

// 文件上传响应
export interface FileUploadResponse {
  file_id: string
  filename: string
  size: number
  mime_type: string
  url?: string
  created_at: string
}

// ==================== API端点类型映射 ====================

// Auth API 端点
export interface AuthApiEndpoints {
  // POST /api/auth/register
  register: {
    request: UserRegisterRequest
    response: ApiResponse<{
      message: string
      user_id: string
      username: string
      email: string
    }>
  }
  
  // POST /api/auth/login
  login: {
    request: UserLoginRequest
    response: TokenResponse
  }
  
  // POST /api/auth/refresh
  refresh: {
    request: RefreshTokenRequest
    response: TokenResponse
  }
  
  // POST /api/auth/logout
  logout: {
    request: void
    response: ApiResponse<{ message: string }>
  }
  
  // GET /api/auth/me
  getCurrentUser: {
    request: void
    response: UserResponse
  }
  
  // PUT /api/auth/me
  updateProfile: {
    request: { full_name?: string }
    response: UserResponse
  }
  
  // POST /api/auth/change-password
  changePassword: {
    request: PasswordChangeRequest
    response: ApiResponse<{ message: string }>
  }
  
  // GET /api/auth/sessions
  getUserSessions: {
    request: void
    response: UserSessionsResponse
  }
  
  // DELETE /api/auth/sessions/{session_id}
  revokeSession: {
    request: { session_id: string }
    response: ApiResponse<{ message: string }>
  }
}

// Chat API 端点
export interface ChatApiEndpoints {
  // POST /api/chat/sessions
  createSession: {
    request: ChatSessionCreate
    response: ChatSessionResponse
  }
  
  // GET /api/chat/sessions
  listSessions: {
    request: { page?: number; size?: number }
    response: ChatSessionListResponse
  }
  
  // GET /api/chat/sessions/{session_id}
  getSession: {
    request: { session_id: string }
    response: ChatSessionResponse
  }
  
  // PUT /api/chat/sessions/{session_id}
  updateSession: {
    request: { session_id: string } & ChatSessionUpdate
    response: ChatSessionResponse
  }
  
  // DELETE /api/chat/sessions/{session_id}
  deleteSession: {
    request: { session_id: string }
    response: ApiResponse<{ message: string }>
  }
  
  // GET /api/chat/sessions/{session_id}/messages
  getMessages: {
    request: { 
      session_id: string
      page?: number
      size?: number
    }
    response: PaginationResponse<MessageResponse>
  }
  
  // POST /api/chat/sessions/{session_id}/messages
  sendMessage: {
    request: { session_id: string } & SendMessageRequest
    response: MessageResponse
  }
  
  // GET /api/chat/sessions/{session_id}/stats
  getSessionStats: {
    request: { session_id: string }
    response: ChatSessionStatsResponse
  }
}

// Stream API 端点
export interface StreamApiEndpoints {
  // POST /api/stream/chat
  streamChat: {
    request: SendMessageRequest
    response: ReadableStream<StreamingMessage>
  }
}

// ==================== API客户端方法类型 ====================

// API客户端方法签名
export interface ApiClientMethods {
  // Auth methods
  register: (data: UserRegisterRequest) => Promise<AuthApiEndpoints['register']['response']>
  login: (data: UserLoginRequest) => Promise<TokenResponse>
  refreshToken: (data: RefreshTokenRequest) => Promise<TokenResponse>
  logout: () => Promise<ApiResponse<{ message: string }>>
  getCurrentUser: () => Promise<UserResponse>
  updateProfile: (data: { full_name?: string }) => Promise<UserResponse>
  changePassword: (data: PasswordChangeRequest) => Promise<ApiResponse<{ message: string }>>
  getUserSessions: () => Promise<UserSessionsResponse>
  revokeSession: (sessionId: string) => Promise<ApiResponse<{ message: string }>>
  
  // Chat methods
  createChatSession: (data: ChatSessionCreate) => Promise<ChatSessionResponse>
  getChatSessions: (params?: { page?: number; size?: number }) => Promise<ChatSessionListResponse>
  getChatSession: (sessionId: string) => Promise<ChatSessionResponse>
  updateChatSession: (sessionId: string, data: ChatSessionUpdate) => Promise<ChatSessionResponse>
  deleteChatSession: (sessionId: string) => Promise<ApiResponse<{ message: string }>>
  getChatMessages: (sessionId: string, params?: { page?: number; size?: number }) => Promise<PaginationResponse<MessageResponse>>
  sendChatMessage: (sessionId: string, data: Omit<SendMessageRequest, 'session_id'>) => Promise<MessageResponse>
  getChatSessionStats: (sessionId: string) => Promise<ChatSessionStatsResponse>
  
  // File upload methods
  uploadFile: (file: File, onProgress?: (progress: number) => void) => Promise<FileUploadResponse>
  downloadFile: (url: string, filename?: string) => Promise<void>
}

// ==================== Composable返回类型 ====================

// 认证状态
export interface AuthState {
  user: UserResponse | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

// 聊天状态
export interface ChatState {
  currentSession: ChatSessionResponse | null
  sessions: ChatSessionResponse[]
  messages: MessageResponse[]
  isLoading: boolean
  isStreaming: boolean
}

// SSE连接状态
export interface SSEState {
  connectionStatus: ConnectionStatus | null
  isConnected: boolean
  isConnecting: boolean
  lastMessage: StreamMessage | null
  error: string | null
}

export default {}