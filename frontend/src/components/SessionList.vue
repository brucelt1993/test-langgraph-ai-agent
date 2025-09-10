<template>
  <div class="session-list" :class="containerClass">
    <!-- 列表头部 -->
    <div v-if="showHeader" class="list-header">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <h3 class="text-lg font-semibold">{{ title }}</h3>
          <div 
            v-if="totalCount !== undefined"
            class="count-badge"
          >
            {{ totalCount }}
          </div>
        </div>
        
        <div class="flex items-center space-x-2">
          <!-- 视图切换 -->
          <div v-if="allowViewModes" class="btn-group">
            <button
              class="btn btn-ghost btn-sm"
              :class="{ 'btn-active': viewMode === 'list' }"
              @click="setViewMode('list')"
              title="列表视图"
            >
              <List class="w-4 h-4" />
            </button>
            <button
              class="btn btn-ghost btn-sm"
              :class="{ 'btn-active': viewMode === 'grid' }"
              @click="setViewMode('grid')"
              title="网格视图"
            >
              <Grid class="w-4 h-4" />
            </button>
            <button
              class="btn btn-ghost btn-sm"
              :class="{ 'btn-active': viewMode === 'compact' }"
              @click="setViewMode('compact')"
              title="紧凑视图"
            >
              <Menu class="w-4 h-4" />
            </button>
          </div>
          
          <!-- 排序 -->
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button class="btn btn-ghost btn-sm" title="排序">
                <ArrowUpDown class="w-4 h-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>排序方式</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                v-for="option in sortOptions"
                :key="option.value"
                @click="setSortBy(option.value)"
                :class="{ 'font-medium': sortBy === option.value }"
              >
                <component :is="option.icon" class="w-4 h-4 mr-2" />
                {{ option.label }}
                <Check 
                  v-if="sortBy === option.value" 
                  class="w-4 h-4 ml-auto"
                />
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="toggleSortOrder">
                <component 
                  :is="sortOrder === 'asc' ? ArrowUp : ArrowDown" 
                  class="w-4 h-4 mr-2"
                />
                {{ sortOrder === 'asc' ? '升序' : '降序' }}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          
          <!-- 批量操作 -->
          <DropdownMenu v-if="allowBatchActions && selectedSessions.length > 0">
            <DropdownMenuTrigger asChild>
              <button class="btn btn-outline btn-sm">
                <Check class="w-4 h-4 mr-2" />
                {{ selectedSessions.length }} 项
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>批量操作</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="batchArchive">
                <Archive class="w-4 h-4 mr-2" />
                归档选中项
              </DropdownMenuItem>
              <DropdownMenuItem @click="batchExport">
                <Download class="w-4 h-4 mr-2" />
                导出选中项
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="batchDelete" class="text-destructive">
                <Trash2 class="w-4 h-4 mr-2" />
                删除选中项
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading && !sessions.length" class="loading-state">
      <div class="loading-spinner w-8 h-8 mx-auto border-primary"></div>
      <p class="text-muted-foreground mt-4 text-center">加载会话历史...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!sessions.length && !isLoading" class="empty-state">
      <div class="empty-icon">
        <MessageSquare class="w-16 h-16 text-muted-foreground/50" />
      </div>
      <h4 class="empty-title">{{ emptyTitle }}</h4>
      <p class="empty-description">{{ emptyDescription }}</p>
      <button
        v-if="showCreateButton"
        class="btn btn-primary mt-4"
        @click="createNewSession"
      >
        开始新对话
      </button>
    </div>

    <!-- 会话列表 -->
    <div v-else class="sessions-container" :class="listClass">
      <!-- 全选控制 -->
      <div 
        v-if="allowBatchActions && sessions.length > 0"
        class="select-all-bar"
      >
        <label class="flex items-center space-x-2 text-sm">
          <input
            type="checkbox"
            :checked="isAllSelected"
            :indeterminate="isSomeSelected"
            @change="toggleSelectAll"
            class="w-4 h-4"
          />
          <span>
            {{ selectedSessions.length > 0 ? `已选择 ${selectedSessions.length} 项` : '全选' }}
          </span>
        </label>
        <button
          v-if="selectedSessions.length > 0"
          class="text-xs text-muted-foreground hover:text-foreground"
          @click="clearSelection"
        >
          清除选择
        </button>
      </div>

      <!-- 列表视图 -->
      <div v-if="viewMode === 'list'" class="list-view space-y-2">
        <div
          v-for="session in paginatedSessions"
          :key="session.id"
          class="session-item list-item"
          :class="getSessionItemClass(session)"
          @click="handleSessionClick(session)"
        >
          <!-- 选择框 -->
          <div v-if="allowBatchActions" class="select-checkbox">
            <input
              type="checkbox"
              :checked="selectedSessions.includes(session.id)"
              @click.stop="toggleSessionSelection(session.id)"
              class="w-4 h-4"
            />
          </div>
          
          <!-- 会话信息 -->
          <div class="session-info flex-1">
            <div class="session-header">
              <h4 class="session-title">{{ session.title }}</h4>
              <div class="session-meta">
                <span class="session-date">
                  {{ formatDateTime(session.updated_at) }}
                </span>
                <span class="session-count">
                  {{ session.message_count }} 条消息
                </span>
                <span v-if="session.agent_name" class="session-agent">
                  {{ session.agent_name }}
                </span>
              </div>
            </div>
            
            <!-- 最后消息预览 -->
            <div 
              v-if="showPreview && session.last_message"
              class="session-preview"
            >
              <p class="preview-text">{{ session.last_message }}</p>
            </div>
            
            <!-- 标签 -->
            <div v-if="session.tags && session.tags.length > 0" class="session-tags">
              <span
                v-for="tag in session.tags.slice(0, 3)"
                :key="tag"
                class="tag"
              >
                {{ tag }}
              </span>
              <span v-if="session.tags.length > 3" class="tag-more">
                +{{ session.tags.length - 3 }}
              </span>
            </div>
          </div>
          
          <!-- 状态指示器 -->
          <div class="session-status">
            <div
              class="status-dot"
              :class="getStatusClass(session)"
              :title="getStatusTitle(session)"
            ></div>
          </div>
          
          <!-- 操作菜单 -->
          <div class="session-actions">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  class="btn btn-ghost btn-sm w-8 h-8"
                  @click.stop
                >
                  <MoreVertical class="w-4 h-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem @click.stop="viewSession(session)">
                  <Eye class="w-4 h-4 mr-2" />
                  查看详情
                </DropdownMenuItem>
                <DropdownMenuItem @click.stop="editSession(session)">
                  <Edit3 class="w-4 h-4 mr-2" />
                  编辑标题
                </DropdownMenuItem>
                <DropdownMenuItem @click.stop="duplicateSession(session)">
                  <Copy class="w-4 h-4 mr-2" />
                  复制会话
                </DropdownMenuItem>
                <DropdownMenuItem @click.stop="archiveSession(session)">
                  <Archive class="w-4 h-4 mr-2" />
                  {{ session.is_active ? '归档' : '取消归档' }}
                </DropdownMenuItem>
                <DropdownMenuItem @click.stop="exportSession(session)">
                  <Download class="w-4 h-4 mr-2" />
                  导出
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  @click.stop="deleteSession(session)"
                  class="text-destructive"
                >
                  <Trash2 class="w-4 h-4 mr-2" />
                  删除
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      <!-- 网格视图 -->
      <div v-else-if="viewMode === 'grid'" class="grid-view">
        <div
          v-for="session in paginatedSessions"
          :key="session.id"
          class="session-item grid-item"
          :class="getSessionItemClass(session)"
          @click="handleSessionClick(session)"
        >
          <!-- 选择框 -->
          <div v-if="allowBatchActions" class="select-checkbox absolute top-2 left-2">
            <input
              type="checkbox"
              :checked="selectedSessions.includes(session.id)"
              @click.stop="toggleSessionSelection(session.id)"
              class="w-4 h-4"
            />
          </div>
          
          <!-- 会话卡片内容 -->
          <div class="card-content">
            <div class="card-header">
              <h4 class="session-title">{{ session.title }}</h4>
              <button
                class="btn btn-ghost btn-sm w-6 h-6"
                @click.stop="openSessionMenu(session)"
              >
                <MoreVertical class="w-3 h-3" />
              </button>
            </div>
            
            <div v-if="showPreview && session.last_message" class="card-preview">
              <p class="preview-text">{{ session.last_message }}</p>
            </div>
            
            <div class="card-footer">
              <div class="session-meta">
                <span class="session-date">
                  {{ formatRelativeTime(session.updated_at) }}
                </span>
                <span class="session-count">
                  {{ session.message_count }}条
                </span>
              </div>
              <div
                class="status-dot"
                :class="getStatusClass(session)"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 紧凑视图 -->
      <div v-else class="compact-view space-y-1">
        <div
          v-for="session in paginatedSessions"
          :key="session.id"
          class="session-item compact-item"
          :class="getSessionItemClass(session)"
          @click="handleSessionClick(session)"
        >
          <div v-if="allowBatchActions" class="select-checkbox">
            <input
              type="checkbox"
              :checked="selectedSessions.includes(session.id)"
              @click.stop="toggleSessionSelection(session.id)"
              class="w-3 h-3"
            />
          </div>
          
          <div class="compact-info flex-1">
            <span class="session-title">{{ session.title }}</span>
            <span class="session-meta">
              {{ formatRelativeTime(session.updated_at) }} • {{ session.message_count }}条
            </span>
          </div>
          
          <div
            class="status-dot"
            :class="getStatusClass(session)"
          ></div>
        </div>
      </div>
    </div>

    <!-- 分页控制 -->
    <div 
      v-if="showPagination && totalPages > 1"
      class="pagination-controls"
    >
      <div class="flex items-center justify-between">
        <div class="pagination-info text-sm text-muted-foreground">
          显示 {{ (currentPage - 1) * pageSize + 1 }} - {{ Math.min(currentPage * pageSize, totalCount || 0) }} 
          / 共 {{ totalCount || 0 }} 条
        </div>
        
        <div class="pagination-buttons flex items-center space-x-2">
          <button
            class="btn btn-outline btn-sm"
            :disabled="currentPage <= 1"
            @click="goToPage(currentPage - 1)"
          >
            <ChevronLeft class="w-4 h-4" />
            上一页
          </button>
          
          <div class="page-numbers flex space-x-1">
            <button
              v-for="page in visiblePages"
              :key="page"
              class="btn btn-ghost btn-sm w-8 h-8"
              :class="{ 'btn-active': page === currentPage }"
              @click="goToPage(page)"
            >
              {{ page }}
            </button>
          </div>
          
          <button
            class="btn btn-outline btn-sm"
            :disabled="currentPage >= totalPages"
            @click="goToPage(currentPage + 1)"
          >
            下一页
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- 加载更多（无限滚动模式） -->
    <div 
      v-if="useInfiniteScroll && hasMore && !isLoading"
      ref="loadMoreTrigger"
      class="load-more-trigger"
    >
      <button
        class="btn btn-ghost btn-sm w-full"
        @click="loadMore"
        :disabled="isLoadingMore"
      >
        <span v-if="isLoadingMore">加载中...</span>
        <span v-else>加载更多</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { 
  List,
  Grid,
  Menu,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Check,
  Archive,
  Download,
  Trash2,
  MessageSquare,
  MoreVertical,
  Eye,
  Edit3,
  Copy,
  ChevronLeft,
  ChevronRight,
  Clock,
  Calendar,
  MessageCircle,
  User
} from 'lucide-vue-next'
import type { ChatSession } from '@/types/chat'

// UI组件占位符
const DropdownMenu = { name: 'DropdownMenu' }
const DropdownMenuTrigger = { name: 'DropdownMenuTrigger' }
const DropdownMenuContent = { name: 'DropdownMenuContent' }
const DropdownMenuItem = { name: 'DropdownMenuItem' }
const DropdownMenuLabel = { name: 'DropdownMenuLabel' }
const DropdownMenuSeparator = { name: 'DropdownMenuSeparator' }

export interface SessionListProps {
  sessions: ChatSession[]
  isLoading?: boolean
  isLoadingMore?: boolean
  totalCount?: number
  currentPage?: number
  pageSize?: number
  hasMore?: boolean
  showHeader?: boolean
  title?: string
  emptyTitle?: string
  emptyDescription?: string
  showCreateButton?: boolean
  showPreview?: boolean
  allowViewModes?: boolean
  allowBatchActions?: boolean
  showPagination?: boolean
  useInfiniteScroll?: boolean
  initialViewMode?: 'list' | 'grid' | 'compact'
  initialSortBy?: string
  initialSortOrder?: 'asc' | 'desc'
  containerClass?: string
}

const props = withDefaults(defineProps<SessionListProps>(), {
  sessions: () => [],
  isLoading: false,
  isLoadingMore: false,
  currentPage: 1,
  pageSize: 20,
  hasMore: false,
  showHeader: true,
  title: '会话历史',
  emptyTitle: '暂无会话历史',
  emptyDescription: '开始您的第一次AI对话吧',
  showCreateButton: true,
  showPreview: true,
  allowViewModes: true,
  allowBatchActions: true,
  showPagination: true,
  useInfiniteScroll: false,
  initialViewMode: 'list',
  initialSortBy: 'updated_at',
  initialSortOrder: 'desc'
})

const emit = defineEmits<{
  'session-click': [session: ChatSession]
  'session-view': [session: ChatSession]
  'session-edit': [session: ChatSession]
  'session-duplicate': [session: ChatSession]
  'session-archive': [session: ChatSession]
  'session-export': [session: ChatSession]
  'session-delete': [session: ChatSession]
  'batch-archive': [sessionIds: string[]]
  'batch-export': [sessionIds: string[]]
  'batch-delete': [sessionIds: string[]]
  'create-session': []
  'page-change': [page: number]
  'sort-change': [sortBy: string, sortOrder: 'asc' | 'desc']
  'view-mode-change': [mode: 'list' | 'grid' | 'compact']
  'load-more': []
}>()

// 响应式状态
const viewMode = ref(props.initialViewMode)
const sortBy = ref(props.initialSortBy)
const sortOrder = ref(props.initialSortOrder)
const selectedSessions = ref<string[]>([])
const loadMoreTrigger = ref<HTMLElement>()

// 排序选项
const sortOptions = [
  { value: 'updated_at', label: '最近更新', icon: Clock },
  { value: 'created_at', label: '创建时间', icon: Calendar },
  { value: 'message_count', label: '消息数量', icon: MessageCircle },
  { value: 'title', label: '标题', icon: User }
]

// 计算属性
const containerClass = computed(() => [
  'session-list-container',
  props.containerClass
])

const listClass = computed(() => [
  'sessions-list',
  `view-${viewMode.value}`
])

const paginatedSessions = computed(() => {
  // 如果使用无限滚动，返回所有会话
  if (props.useInfiniteScroll) {
    return props.sessions
  }
  
  // 否则进行分页
  const start = (props.currentPage - 1) * props.pageSize
  const end = start + props.pageSize
  return props.sessions.slice(start, end)
})

const totalPages = computed(() => 
  Math.ceil((props.totalCount || props.sessions.length) / props.pageSize)
)

const visiblePages = computed(() => {
  const current = props.currentPage
  const total = totalPages.value
  const pages: number[] = []
  
  if (total <= 7) {
    // 显示所有页码
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    // 智能显示页码
    pages.push(1)
    
    if (current > 3) {
      pages.push(-1) // 省略号标记
    }
    
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)
    
    for (let i = start; i <= end; i++) {
      if (!pages.includes(i)) {
        pages.push(i)
      }
    }
    
    if (current < total - 2) {
      pages.push(-2) // 省略号标记
    }
    
    if (total > 1) {
      pages.push(total)
    }
  }
  
  return pages
})

const isAllSelected = computed(() => 
  paginatedSessions.value.length > 0 && 
  selectedSessions.value.length === paginatedSessions.value.length
)

const isSomeSelected = computed(() => 
  selectedSessions.value.length > 0 && 
  selectedSessions.value.length < paginatedSessions.value.length
)

// 方法
const setViewMode = (mode: 'list' | 'grid' | 'compact') => {
  viewMode.value = mode
  emit('view-mode-change', mode)
}

const setSortBy = (value: string) => {
  if (sortBy.value === value) {
    toggleSortOrder()
  } else {
    sortBy.value = value
    emit('sort-change', sortBy.value, sortOrder.value)
  }
}

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  emit('sort-change', sortBy.value, sortOrder.value)
}

const getSessionItemClass = (session: ChatSession) => [
  {
    'selected': selectedSessions.value.includes(session.id),
    'archived': !session.is_active,
    'has-unread': false // TODO: 实现未读消息逻辑
  }
]

const getStatusClass = (session: ChatSession) => [
  'status-indicator',
  {
    'status-active': session.is_active,
    'status-archived': !session.is_active,
    'status-error': false // TODO: 实现错误状态逻辑
  }
]

const getStatusTitle = (session: ChatSession) => {
  if (!session.is_active) return '已归档'
  return '活跃'
}

const handleSessionClick = (session: ChatSession) => {
  emit('session-click', session)
}

const viewSession = (session: ChatSession) => {
  emit('session-view', session)
}

const editSession = (session: ChatSession) => {
  emit('session-edit', session)
}

const duplicateSession = (session: ChatSession) => {
  emit('session-duplicate', session)
}

const archiveSession = (session: ChatSession) => {
  emit('session-archive', session)
}

const exportSession = (session: ChatSession) => {
  emit('session-export', session)
}

const deleteSession = (session: ChatSession) => {
  emit('session-delete', session)
}

const toggleSessionSelection = (sessionId: string) => {
  const index = selectedSessions.value.indexOf(sessionId)
  if (index > -1) {
    selectedSessions.value.splice(index, 1)
  } else {
    selectedSessions.value.push(sessionId)
  }
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedSessions.value = []
  } else {
    selectedSessions.value = paginatedSessions.value.map(session => session.id)
  }
}

const clearSelection = () => {
  selectedSessions.value = []
}

const batchArchive = () => {
  emit('batch-archive', [...selectedSessions.value])
  clearSelection()
}

const batchExport = () => {
  emit('batch-export', [...selectedSessions.value])
  clearSelection()
}

const batchDelete = () => {
  emit('batch-delete', [...selectedSessions.value])
  clearSelection()
}

const createNewSession = () => {
  emit('create-session')
}

const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    emit('page-change', page)
  }
}

const loadMore = () => {
  emit('load-more')
}

const formatDateTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } else {
    return date.toLocaleDateString('zh-CN', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
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

// 无限滚动
const setupInfiniteScroll = () => {
  if (!props.useInfiniteScroll || !loadMoreTrigger.value) return

  const observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && props.hasMore && !props.isLoadingMore) {
        loadMore()
      }
    },
    { threshold: 0.1 }
  )

  observer.observe(loadMoreTrigger.value)
  
  return () => observer.disconnect()
}

// 监听器
watch(() => props.sessions, () => {
  // 清理无效的选中项
  selectedSessions.value = selectedSessions.value.filter(id =>
    props.sessions.some(session => session.id === id)
  )
})

// 生命周期
onMounted(() => {
  if (props.useInfiniteScroll) {
    nextTick(() => {
      setupInfiniteScroll()
    })
  }
})

// 暴露方法
defineExpose({
  clearSelection,
  selectAll: () => { selectedSessions.value = paginatedSessions.value.map(s => s.id) },
  getSelected: () => [...selectedSessions.value],
  setViewMode,
  setSortBy
})
</script>

<style scoped>
.session-list-container {
  @apply flex flex-col h-full bg-background;
}

.list-header {
  @apply p-4 border-b border-border bg-card;
}

.count-badge {
  @apply px-2 py-1 bg-muted text-muted-foreground rounded-full text-xs font-medium;
}

.btn-group {
  @apply flex border border-border rounded-md overflow-hidden;
}

.btn-group .btn {
  @apply border-0 rounded-none;
}

.btn-group .btn:not(:last-child) {
  @apply border-r border-border;
}

.btn-active {
  @apply bg-primary text-primary-foreground;
}

/* 加载和空状态 */
.loading-state,
.empty-state {
  @apply flex flex-col items-center justify-center py-16 text-center;
}

.empty-icon {
  @apply mb-4;
}

.empty-title {
  @apply text-lg font-medium mb-2;
}

.empty-description {
  @apply text-muted-foreground text-sm;
}

/* 会话列表容器 */
.sessions-container {
  @apply flex-1 overflow-y-auto;
}

.select-all-bar {
  @apply flex items-center justify-between p-3 border-b border-border bg-muted/30;
}

/* 列表视图 */
.list-view {
  @apply p-4;
}

.list-item {
  @apply flex items-center p-4 bg-card border border-border rounded-lg hover:shadow-sm transition-all duration-200 cursor-pointer;
}

.list-item:hover {
  @apply border-primary/20 shadow-md;
}

.list-item.selected {
  @apply border-primary bg-primary/5;
}

.list-item.archived {
  @apply opacity-60;
}

.select-checkbox {
  @apply mr-3 flex-shrink-0;
}

.session-info {
  @apply flex-1 min-w-0;
}

.session-header {
  @apply mb-2;
}

.session-title {
  @apply font-medium text-base line-clamp-1 mb-1;
}

.session-meta {
  @apply flex items-center space-x-2 text-sm text-muted-foreground;
}

.session-meta > span {
  @apply px-2 py-1 bg-muted/50 rounded text-xs;
}

.session-preview {
  @apply mb-2;
}

.preview-text {
  @apply text-sm text-muted-foreground line-clamp-2;
}

.session-tags {
  @apply flex items-center space-x-1 flex-wrap;
}

.tag {
  @apply px-2 py-1 bg-accent/20 text-accent-foreground text-xs rounded-full;
}

.tag-more {
  @apply px-2 py-1 bg-muted text-muted-foreground text-xs rounded-full;
}

.session-status {
  @apply mx-3 flex-shrink-0;
}

.status-indicator {
  @apply w-3 h-3 rounded-full;
}

.status-active {
  @apply bg-green-500;
}

.status-archived {
  @apply bg-gray-400;
}

.status-error {
  @apply bg-red-500;
}

.session-actions {
  @apply flex-shrink-0;
}

/* 网格视图 */
.grid-view {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4;
}

.grid-item {
  @apply relative bg-card border border-border rounded-lg p-4 hover:shadow-sm transition-all duration-200 cursor-pointer;
}

.grid-item:hover {
  @apply border-primary/20 shadow-md;
}

.grid-item.selected {
  @apply border-primary bg-primary/5;
}

.card-content {
  @apply space-y-3;
}

.card-header {
  @apply flex items-start justify-between;
}

.card-header .session-title {
  @apply font-medium text-sm line-clamp-2 flex-1 mr-2;
}

.card-preview {
  @apply min-h-[3rem];
}

.card-preview .preview-text {
  @apply text-xs text-muted-foreground line-clamp-3;
}

.card-footer {
  @apply flex items-center justify-between;
}

.card-footer .session-meta {
  @apply flex items-center space-x-2 text-xs text-muted-foreground;
}

.card-footer .session-meta > span {
  @apply px-1 py-0.5 bg-muted/50 rounded;
}

/* 紧凑视图 */
.compact-view {
  @apply p-2;
}

.compact-item {
  @apply flex items-center p-2 hover:bg-muted/50 rounded cursor-pointer transition-colors duration-150;
}

.compact-item.selected {
  @apply bg-primary/10 border-primary;
}

.compact-info {
  @apply flex flex-col min-w-0;
}

.compact-info .session-title {
  @apply font-medium text-sm line-clamp-1;
}

.compact-info .session-meta {
  @apply text-xs text-muted-foreground;
}

/* 分页控制 */
.pagination-controls {
  @apply p-4 border-t border-border bg-card;
}

.pagination-info {
  @apply text-sm text-muted-foreground;
}

.pagination-buttons {
  @apply flex items-center space-x-2;
}

.page-numbers {
  @apply flex space-x-1;
}

/* 加载更多 */
.load-more-trigger {
  @apply p-4 border-t border-border;
}

/* 工具类 */
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 滚动条样式 */
.sessions-container::-webkit-scrollbar {
  @apply w-2;
}

.sessions-container::-webkit-scrollbar-track {
  @apply bg-transparent;
}

.sessions-container::-webkit-scrollbar-thumb {
  @apply bg-border rounded-full;
}

.sessions-container::-webkit-scrollbar-thumb:hover {
  @apply bg-border/80;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .list-header {
    @apply p-3;
  }
  
  .list-view {
    @apply p-2;
  }
  
  .list-item {
    @apply p-3;
  }
  
  .grid-view {
    @apply grid-cols-1 gap-3 p-3;
  }
  
  .btn-group {
    @apply flex-col w-auto;
  }
  
  .btn-group .btn:not(:last-child) {
    @apply border-r-0 border-b border-border;
  }
  
  .pagination-controls {
    @apply p-3;
  }
  
  .pagination-buttons {
    @apply flex-wrap justify-center;
  }
}

/* 深色模式适配 */
@media (prefers-color-scheme: dark) {
  .status-active {
    @apply bg-green-400;
  }
  
  .status-archived {
    @apply bg-gray-500;
  }
  
  .status-error {
    @apply bg-red-400;
  }
}

/* 动画效果 */
.session-item {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { 
    opacity: 0; 
    transform: translateY(10px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

/* 选中动画 */
.session-item.selected {
  animation: selectPulse 0.3s ease-out;
}

@keyframes selectPulse {
  0% { 
    transform: scale(1); 
  }
  50% { 
    transform: scale(1.02); 
  }
  100% { 
    transform: scale(1); 
  }
}
</style>