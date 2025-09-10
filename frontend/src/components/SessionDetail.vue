<template>
  <div class="session-detail" :class="containerClass">
    <!-- 头部信息 -->
    <div class="detail-header">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <button
            v-if="showBackButton"
            class="btn btn-ghost btn-sm"
            @click="goBack"
            title="返回"
          >
            <ArrowLeft class="w-4 h-4" />
          </button>
          
          <div class="session-info">
            <div class="flex items-center space-x-3">
              <div class="session-avatar">
                <Bot class="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2 class="session-title">{{ session?.title || '会话详情' }}</h2>
                <p class="session-subtitle">
                  {{ getSessionSubtitle() }}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="flex items-center space-x-2">
          <!-- 会话控制 -->
          <button
            v-if="session && canResume"
            class="btn btn-primary btn-sm"
            @click="resumeSession"
            title="继续对话"
          >
            <Play class="w-4 h-4 mr-2" />
            继续对话
          </button>
          
          <!-- 操作菜单 -->
          <DropdownMenu v-if="session">
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
              <DropdownMenuItem @click="duplicateSession">
                <Copy class="w-4 h-4 mr-2" />
                复制会话
              </DropdownMenuItem>
              <DropdownMenuItem @click="exportSession">
                <Download class="w-4 h-4 mr-2" />
                导出会话
              </DropdownMenuItem>
              <DropdownMenuItem @click="shareSession">
                <Share2 class="w-4 h-4 mr-2" />
                分享会话
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="archiveSession">
                <Archive class="w-4 h-4 mr-2" />
                {{ session.is_active ? '归档会话' : '取消归档' }}
              </DropdownMenuItem>
              <DropdownMenuItem 
                @click="deleteSession" 
                class="text-destructive"
              >
                <Trash2 class="w-4 h-4 mr-2" />
                删除会话
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>

    <!-- 会话统计 -->
    <div v-if="showStats && sessionStats" class="session-stats">
      <div class="stats-grid">
        <div class="stat-item">
          <MessageCircle class="w-5 h-5 text-primary" />
          <div class="stat-content">
            <div class="stat-value">{{ sessionStats.message_count }}</div>
            <div class="stat-label">消息总数</div>
          </div>
        </div>
        
        <div class="stat-item">
          <Clock class="w-5 h-5 text-green-600" />
          <div class="stat-content">
            <div class="stat-value">
              {{ sessionStats.average_response_time ? Math.round(sessionStats.average_response_time) + 's' : '-' }}
            </div>
            <div class="stat-label">平均响应</div>
          </div>
        </div>
        
        <div class="stat-item">
          <Wrench class="w-5 h-5 text-orange-600" />
          <div class="stat-content">
            <div class="stat-value">{{ sessionStats.tool_call_count || 0 }}</div>
            <div class="stat-label">工具调用</div>
          </div>
        </div>
        
        <div class="stat-item">
          <BarChart3 class="w-5 h-5 text-purple-600" />
          <div class="stat-content">
            <div class="stat-value">{{ sessionStats.context_rounds || 0 }}</div>
            <div class="stat-label">上下文轮数</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="detail-content">
      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner w-8 h-8 mx-auto border-primary"></div>
        <p class="text-muted-foreground mt-4 text-center">加载会话详情...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="error-state">
        <div class="error-icon">
          <AlertCircle class="w-16 h-16 text-destructive" />
        </div>
        <h3 class="error-title">加载失败</h3>
        <p class="error-description">{{ error }}</p>
        <button class="btn btn-outline mt-4" @click="retry">
          <RefreshCw class="w-4 h-4 mr-2" />
          重试
        </button>
      </div>

      <!-- 会话内容 -->
      <div v-else-if="session" class="session-content">
        <!-- 消息列表 -->
        <div class="messages-section">
          <div class="section-header">
            <h3 class="section-title">对话历史</h3>
            <div class="section-controls">
              <!-- 消息筛选 -->
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button class="btn btn-ghost btn-sm" title="筛选消息">
                    <Filter class="w-4 h-4" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>消息类型</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    v-for="type in messageTypes"
                    :key="type.value"
                    @click="toggleMessageFilter(type.value)"
                  >
                    <input
                      type="checkbox"
                      :checked="messageFilters.includes(type.value)"
                      class="w-4 h-4 mr-2"
                    />
                    <component :is="type.icon" class="w-4 h-4 mr-2" />
                    {{ type.label }}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem @click="clearMessageFilters">
                    <RotateCcw class="w-4 h-4 mr-2" />
                    清除筛选
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              
              <!-- 搜索消息 -->
              <div class="relative">
                <input
                  v-model="messageSearchQuery"
                  type="text"
                  placeholder="搜索消息..."
                  class="input input-sm pl-8 w-64"
                />
                <Search class="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              </div>
            </div>
          </div>

          <!-- 消息列表组件 -->
          <MessageList
            :messages="filteredMessages"
            :is-loading="isLoadingMessages"
            :can-load-more="canLoadMoreMessages"
            :show-thinking-process="true"
            @load-more="loadMoreMessages"
            @message-click="handleMessageClick"
            class="messages-container"
          />
        </div>

        <!-- 侧边栏信息 -->
        <div v-if="showSidebar" class="session-sidebar">
          <!-- 会话元信息 -->
          <div class="sidebar-section">
            <h4 class="sidebar-title">会话信息</h4>
            <div class="metadata-list">
              <div class="metadata-item">
                <span class="metadata-label">创建时间</span>
                <span class="metadata-value">
                  {{ formatDateTime(session.created_at) }}
                </span>
              </div>
              <div class="metadata-item">
                <span class="metadata-label">最后更新</span>
                <span class="metadata-value">
                  {{ formatDateTime(session.updated_at) }}
                </span>
              </div>
              <div class="metadata-item">
                <span class="metadata-label">消息数量</span>
                <span class="metadata-value">{{ session.message_count }}</span>
              </div>
              <div class="metadata-item">
                <span class="metadata-label">AI助手</span>
                <span class="metadata-value">{{ session.agent_name || 'Default' }}</span>
              </div>
              <div class="metadata-item">
                <span class="metadata-label">状态</span>
                <span class="metadata-value">
                  <span 
                    class="status-badge" 
                    :class="session.is_active ? 'status-active' : 'status-archived'"
                  >
                    {{ session.is_active ? '活跃' : '已归档' }}
                  </span>
                </span>
              </div>
            </div>
          </div>

          <!-- 标签管理 -->
          <div v-if="session.tags || allowTagEdit" class="sidebar-section">
            <h4 class="sidebar-title">标签</h4>
            <div class="tags-container">
              <div v-if="session.tags && session.tags.length > 0" class="current-tags">
                <span
                  v-for="tag in session.tags"
                  :key="tag"
                  class="tag-chip"
                >
                  {{ tag }}
                  <button
                    v-if="allowTagEdit"
                    class="tag-remove"
                    @click="removeTag(tag)"
                  >
                    <X class="w-3 h-3" />
                  </button>
                </span>
              </div>
              <div v-if="allowTagEdit" class="tag-input">
                <input
                  v-model="newTag"
                  type="text"
                  placeholder="添加标签..."
                  class="input input-sm"
                  @keydown.enter="addTag"
                />
                <button
                  class="btn btn-ghost btn-sm"
                  @click="addTag"
                  :disabled="!newTag.trim()"
                >
                  <Plus class="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>

          <!-- 相关会话 -->
          <div v-if="relatedSessions.length > 0" class="sidebar-section">
            <h4 class="sidebar-title">相关会话</h4>
            <div class="related-sessions">
              <div
                v-for="relatedSession in relatedSessions"
                :key="relatedSession.id"
                class="related-item"
                @click="viewRelatedSession(relatedSession)"
              >
                <div class="related-info">
                  <h5 class="related-title">{{ relatedSession.title }}</h5>
                  <p class="related-meta">
                    {{ formatRelativeTime(relatedSession.updated_at) }}
                  </p>
                </div>
                <ChevronRight class="w-4 h-4 text-muted-foreground" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { 
  ArrowLeft,
  Bot,
  Play,
  MoreVertical,
  Edit3,
  Copy,
  Download,
  Share2,
  Archive,
  Trash2,
  MessageCircle,
  Clock,
  Wrench,
  BarChart3,
  AlertCircle,
  RefreshCw,
  Filter,
  Search,
  RotateCcw,
  User,
  Brain,
  Settings,
  X,
  Plus,
  ChevronRight
} from 'lucide-vue-next'
import MessageList from './MessageList.vue'
import type { ChatSession, Message, SessionStatsResponse } from '@/types/chat'

// UI组件占位符
const DropdownMenu = { name: 'DropdownMenu' }
const DropdownMenuTrigger = { name: 'DropdownMenuTrigger' }
const DropdownMenuContent = { name: 'DropdownMenuContent' }
const DropdownMenuItem = { name: 'DropdownMenuItem' }
const DropdownMenuLabel = { name: 'DropdownMenuLabel' }
const DropdownMenuSeparator = { name: 'DropdownMenuSeparator' }

export interface SessionDetailProps {
  session?: ChatSession
  messages?: Message[]
  sessionStats?: SessionStatsResponse
  relatedSessions?: ChatSession[]
  isLoading?: boolean
  isLoadingMessages?: boolean
  canLoadMoreMessages?: boolean
  error?: string
  showBackButton?: boolean
  showStats?: boolean
  showSidebar?: boolean
  canResume?: boolean
  allowTagEdit?: boolean
  containerClass?: string
}

const props = withDefaults(defineProps<SessionDetailProps>(), {
  messages: () => [],
  relatedSessions: () => [],
  isLoading: false,
  isLoadingMessages: false,
  canLoadMoreMessages: false,
  showBackButton: true,
  showStats: true,
  showSidebar: true,
  canResume: true,
  allowTagEdit: true
})

const emit = defineEmits<{
  'back': []
  'resume-session': [session: ChatSession]
  'edit-title': [session: ChatSession]
  'duplicate': [session: ChatSession]
  'export': [session: ChatSession]
  'share': [session: ChatSession]
  'archive': [session: ChatSession]
  'delete': [session: ChatSession]
  'load-more-messages': []
  'message-click': [message: Message]
  'view-related': [session: ChatSession]
  'add-tag': [sessionId: string, tag: string]
  'remove-tag': [sessionId: string, tag: string]
  'retry': []
}>()

// 响应式状态
const messageSearchQuery = ref('')
const messageFilters = ref<string[]>(['user', 'assistant'])
const newTag = ref('')

// 消息类型配置
const messageTypes = [
  { value: 'user', label: '用户消息', icon: User },
  { value: 'assistant', label: 'AI回复', icon: Bot },
  { value: 'thinking', label: '思考过程', icon: Brain },
  { value: 'system', label: '系统消息', icon: Settings }
]

// 计算属性
const containerClass = computed(() => [
  'session-detail-container',
  props.containerClass,
  {
    'with-sidebar': props.showSidebar,
    'loading': props.isLoading
  }
])

const filteredMessages = computed(() => {
  let filtered = props.messages || []

  // 按类型筛选
  if (messageFilters.value.length > 0) {
    filtered = filtered.filter(message => 
      messageFilters.value.includes(message.message_type)
    )
  }

  // 按搜索查询筛选
  if (messageSearchQuery.value.trim()) {
    const query = messageSearchQuery.value.toLowerCase()
    filtered = filtered.filter(message =>
      message.content.toLowerCase().includes(query)
    )
  }

  return filtered
})

// 方法
const getSessionSubtitle = () => {
  if (!props.session) return ''
  
  const messageCount = props.session.message_count
  const updateTime = formatRelativeTime(props.session.updated_at)
  
  return `${messageCount} 条消息 • ${updateTime}`
}

const goBack = () => {
  emit('back')
}

const resumeSession = () => {
  if (props.session) {
    emit('resume-session', props.session)
  }
}

const editSessionTitle = () => {
  if (props.session) {
    emit('edit-title', props.session)
  }
}

const duplicateSession = () => {
  if (props.session) {
    emit('duplicate', props.session)
  }
}

const exportSession = () => {
  if (props.session) {
    emit('export', props.session)
  }
}

const shareSession = () => {
  if (props.session) {
    emit('share', props.session)
  }
}

const archiveSession = () => {
  if (props.session) {
    emit('archive', props.session)
  }
}

const deleteSession = () => {
  if (props.session) {
    emit('delete', props.session)
  }
}

const loadMoreMessages = () => {
  emit('load-more-messages')
}

const handleMessageClick = (message: Message) => {
  emit('message-click', message)
}

const viewRelatedSession = (session: ChatSession) => {
  emit('view-related', session)
}

const toggleMessageFilter = (type: string) => {
  const index = messageFilters.value.indexOf(type)
  if (index > -1) {
    messageFilters.value.splice(index, 1)
  } else {
    messageFilters.value.push(type)
  }
}

const clearMessageFilters = () => {
  messageFilters.value = ['user', 'assistant']
}

const addTag = () => {
  if (!newTag.value.trim() || !props.session) return
  
  emit('add-tag', props.session.id, newTag.value.trim())
  newTag.value = ''
}

const removeTag = (tag: string) => {
  if (props.session) {
    emit('remove-tag', props.session.id, tag)
  }
}

const retry = () => {
  emit('retry')
}

const formatDateTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

const formatRelativeTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour

  if (diff < minute) return '刚刚'
  if (diff < hour) return `${Math.floor(diff / minute)}分钟前`
  if (diff < day) return `${Math.floor(diff / hour)}小时前`
  return `${Math.floor(diff / day)}天前`
}

// 暴露方法
defineExpose({
  clearSearch: () => { messageSearchQuery.value = '' },
  resetFilters: clearMessageFilters,
  focusSearch: () => {
    // TODO: 实现搜索框聚焦
  }
})
</script>

<style scoped>
.session-detail-container {
  @apply flex flex-col h-full bg-background;
}

.session-detail-container.with-sidebar .detail-content {
  @apply flex;
}

.session-detail-container.loading {
  @apply pointer-events-none;
}

/* 头部信息 */
.detail-header {
  @apply p-4 border-b border-border bg-card;
}

.session-info .session-title {
  @apply text-xl font-semibold;
}

.session-info .session-subtitle {
  @apply text-sm text-muted-foreground;
}

.session-avatar {
  @apply w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center;
}

/* 会话统计 */
.session-stats {
  @apply p-4 bg-muted/30 border-b border-border;
}

.stats-grid {
  @apply grid grid-cols-2 md:grid-cols-4 gap-4;
}

.stat-item {
  @apply flex items-center space-x-3 p-3 bg-card rounded-lg border border-border;
}

.stat-content {
  @apply flex flex-col;
}

.stat-value {
  @apply text-lg font-semibold;
}

.stat-label {
  @apply text-xs text-muted-foreground;
}

/* 主要内容 */
.detail-content {
  @apply flex-1 overflow-hidden;
}

/* 加载和错误状态 */
.loading-state,
.error-state {
  @apply flex flex-col items-center justify-center h-full text-center;
}

.error-icon {
  @apply mb-4;
}

.error-title {
  @apply text-lg font-medium mb-2;
}

.error-description {
  @apply text-muted-foreground text-sm;
}

/* 会话内容 */
.session-content {
  @apply flex h-full;
}

.messages-section {
  @apply flex-1 flex flex-col overflow-hidden;
}

.section-header {
  @apply flex items-center justify-between p-4 border-b border-border bg-card;
}

.section-title {
  @apply text-base font-medium;
}

.section-controls {
  @apply flex items-center space-x-3;
}

.messages-container {
  @apply flex-1 overflow-hidden;
}

/* 侧边栏 */
.session-sidebar {
  @apply w-80 bg-card border-l border-border overflow-y-auto;
}

.sidebar-section {
  @apply p-4 border-b border-border;
}

.sidebar-title {
  @apply text-sm font-medium mb-3 text-foreground;
}

/* 元数据列表 */
.metadata-list {
  @apply space-y-3;
}

.metadata-item {
  @apply flex justify-between items-start;
}

.metadata-label {
  @apply text-xs text-muted-foreground font-medium;
}

.metadata-value {
  @apply text-xs text-foreground text-right;
}

.status-badge {
  @apply px-2 py-1 rounded-full text-xs font-medium;
}

.status-active {
  @apply bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400;
}

.status-archived {
  @apply bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400;
}

/* 标签管理 */
.tags-container {
  @apply space-y-3;
}

.current-tags {
  @apply flex flex-wrap gap-2;
}

.tag-chip {
  @apply flex items-center space-x-1 px-2 py-1 bg-accent/20 text-accent-foreground text-xs rounded-full;
}

.tag-remove {
  @apply hover:text-destructive transition-colors duration-150;
}

.tag-input {
  @apply flex space-x-2;
}

/* 相关会话 */
.related-sessions {
  @apply space-y-2;
}

.related-item {
  @apply flex items-center justify-between p-2 hover:bg-muted/50 rounded cursor-pointer transition-colors duration-150;
}

.related-info {
  @apply flex-1 min-w-0;
}

.related-title {
  @apply text-sm font-medium line-clamp-1;
}

.related-meta {
  @apply text-xs text-muted-foreground;
}

/* 工具类 */
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 滚动条样式 */
.session-sidebar::-webkit-scrollbar {
  @apply w-2;
}

.session-sidebar::-webkit-scrollbar-track {
  @apply bg-transparent;
}

.session-sidebar::-webkit-scrollbar-thumb {
  @apply bg-border rounded-full;
}

.session-sidebar::-webkit-scrollbar-thumb:hover {
  @apply bg-border/80;
}

/* 响应式调整 */
@media (max-width: 1024px) {
  .session-detail-container.with-sidebar .detail-content {
    @apply flex-col;
  }
  
  .session-sidebar {
    @apply w-full h-auto max-h-64 border-l-0 border-t;
  }
  
  .stats-grid {
    @apply grid-cols-2;
  }
}

@media (max-width: 768px) {
  .detail-header {
    @apply p-3;
  }
  
  .session-stats {
    @apply p-3;
  }
  
  .stats-grid {
    @apply grid-cols-1 gap-3;
  }
  
  .stat-item {
    @apply p-2;
  }
  
  .section-header {
    @apply p-3;
  }
  
  .section-controls {
    @apply flex-col space-x-0 space-y-2 items-stretch;
  }
  
  .section-controls input {
    @apply w-full;
  }
  
  .sidebar-section {
    @apply p-3;
  }
}

@media (max-width: 640px) {
  .session-info .session-title {
    @apply text-lg;
  }
  
  .session-avatar {
    @apply w-10 h-10;
  }
  
  .metadata-item {
    @apply flex-col items-start space-y-1;
  }
  
  .metadata-value {
    @apply text-left;
  }
}

/* 动画效果 */
.session-detail-container {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.stat-item {
  animation: fadeInUp 0.3s ease-out;
}

.stat-item:nth-child(2) { animation-delay: 0.1s; }
.stat-item:nth-child(3) { animation-delay: 0.2s; }
.stat-item:nth-child(4) { animation-delay: 0.3s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 悬停效果 */
.stat-item:hover {
  @apply shadow-sm border-primary/20 transition-all duration-200;
}

.related-item:hover {
  @apply bg-muted/70;
}

.tag-chip:hover .tag-remove {
  @apply text-destructive;
}

/* 焦点状态 */
.tag-input input:focus {
  @apply ring-2 ring-primary ring-offset-2;
}

/* 深色模式适配 */
@media (prefers-color-scheme: dark) {
  .status-active {
    @apply bg-green-900/30 text-green-400;
  }
  
  .status-archived {
    @apply bg-gray-900/30 text-gray-400;
  }
}
</style>