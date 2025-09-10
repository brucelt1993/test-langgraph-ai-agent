<template>
  <AuthGuard>
    <div class="history-view">
      <!-- 头部导航 -->
      <header class="history-header">
        <div class="container mx-auto px-4 py-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-4">
              <button
                class="btn btn-ghost btn-sm"
                @click="goBack"
                title="返回"
              >
                <ArrowLeft class="w-4 h-4" />
              </button>
              
              <div>
                <h1 class="text-2xl font-bold">会话历史</h1>
                <p class="text-muted-foreground">
                  管理和浏览您的AI对话记录
                </p>
              </div>
            </div>
            
            <div class="flex items-center space-x-3">
              <!-- 全局搜索 -->
              <div class="relative">
                <input
                  v-model="globalSearchQuery"
                  type="text"
                  placeholder="搜索会话或消息..."
                  class="input w-64 pl-10"
                  @keydown.enter="performGlobalSearch"
                />
                <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <button
                  v-if="globalSearchQuery"
                  class="absolute right-2 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  @click="clearGlobalSearch"
                >
                  <X class="w-4 h-4" />
                </button>
              </div>
              
              <!-- 高级筛选 -->
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button class="btn btn-outline btn-sm">
                    <Filter class="w-4 h-4 mr-2" />
                    筛选
                    <span 
                      v-if="activeFiltersCount > 0"
                      class="ml-2 px-1.5 py-0.5 bg-primary text-primary-foreground text-xs rounded-full"
                    >
                      {{ activeFiltersCount }}
                    </span>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" class="w-64">
                  <DropdownMenuLabel>高级筛选</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  
                  <!-- 时间范围 -->
                  <div class="p-3 space-y-3">
                    <div>
                      <label class="text-sm font-medium mb-2 block">时间范围</label>
                      <select v-model="filters.dateRange" class="input input-sm w-full">
                        <option value="">所有时间</option>
                        <option value="today">今天</option>
                        <option value="week">本周</option>
                        <option value="month">本月</option>
                        <option value="year">今年</option>
                      </select>
                    </div>
                    
                    <!-- 状态筛选 -->
                    <div>
                      <label class="text-sm font-medium mb-2 block">状态</label>
                      <div class="space-y-2">
                        <label class="flex items-center space-x-2">
                          <input
                            v-model="filters.status"
                            type="radio"
                            value=""
                            class="w-3 h-3"
                          />
                          <span class="text-sm">全部</span>
                        </label>
                        <label class="flex items-center space-x-2">
                          <input
                            v-model="filters.status"
                            type="radio"
                            value="active"
                            class="w-3 h-3"
                          />
                          <span class="text-sm">活跃</span>
                        </label>
                        <label class="flex items-center space-x-2">
                          <input
                            v-model="filters.status"
                            type="radio"
                            value="archived"
                            class="w-3 h-3"
                          />
                          <span class="text-sm">已归档</span>
                        </label>
                      </div>
                    </div>
                    
                    <!-- AI助手 -->
                    <div>
                      <label class="text-sm font-medium mb-2 block">AI助手</label>
                      <select v-model="filters.agentName" class="input input-sm w-full">
                        <option value="">所有助手</option>
                        <option 
                          v-for="agent in availableAgents" 
                          :key="agent"
                          :value="agent"
                        >
                          {{ agent }}
                        </option>
                      </select>
                    </div>
                    
                    <!-- 消息数量范围 -->
                    <div>
                      <label class="text-sm font-medium mb-2 block">消息数量</label>
                      <div class="flex space-x-2">
                        <input
                          v-model.number="filters.minMessages"
                          type="number"
                          placeholder="最小"
                          class="input input-sm flex-1"
                          min="0"
                        />
                        <input
                          v-model.number="filters.maxMessages"
                          type="number"
                          placeholder="最大"
                          class="input input-sm flex-1"
                          min="0"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <DropdownMenuSeparator />
                  <div class="p-3 flex space-x-2">
                    <button 
                      class="btn btn-outline btn-sm flex-1"
                      @click="resetFilters"
                    >
                      重置
                    </button>
                    <button 
                      class="btn btn-primary btn-sm flex-1"
                      @click="applyFilters"
                    >
                      应用
                    </button>
                  </div>
                </DropdownMenuContent>
              </DropdownMenu>
              
              <!-- 新建对话 -->
              <button
                class="btn btn-primary"
                @click="createNewSession"
              >
                <Plus class="w-4 h-4 mr-2" />
                新建对话
              </button>
            </div>
          </div>
        </div>
      </header>

      <!-- 主要内容 -->
      <main class="history-main">
        <div class="container mx-auto px-4 h-full">
          <div class="history-content" :class="{ 'show-detail': selectedSession }">
            <!-- 会话列表 -->
            <div class="sessions-panel">
              <SessionList
                :sessions="filteredSessions"
                :is-loading="isLoading"
                :is-loading-more="isLoadingMore"
                :total-count="totalCount"
                :current-page="currentPage"
                :page-size="pageSize"
                :has-more="hasMore"
                :show-header="false"
                :show-create-button="false"
                :use-infinite-scroll="useInfiniteScroll"
                @session-click="selectSession"
                @session-view="selectSession"
                @session-edit="handleSessionEdit"
                @session-duplicate="handleSessionDuplicate"
                @session-archive="handleSessionArchive"
                @session-export="handleSessionExport"
                @session-delete="handleSessionDelete"
                @batch-archive="handleBatchArchive"
                @batch-export="handleBatchExport"
                @batch-delete="handleBatchDelete"
                @create-session="createNewSession"
                @page-change="handlePageChange"
                @sort-change="handleSortChange"
                @view-mode-change="handleViewModeChange"
                @load-more="loadMoreSessions"
                class="h-full"
              />
            </div>

            <!-- 会话详情 -->
            <div 
              v-if="selectedSession" 
              class="detail-panel"
            >
              <SessionDetail
                :session="selectedSession"
                :messages="selectedSessionMessages"
                :session-stats="selectedSessionStats"
                :related-sessions="relatedSessions"
                :is-loading="isLoadingDetail"
                :is-loading-messages="isLoadingMessages"
                :can-load-more-messages="canLoadMoreMessages"
                :error="detailError"
                :show-back-button="isMobile"
                :show-stats="true"
                :show-sidebar="!isMobile"
                :can-resume="true"
                :allow-tag-edit="true"
                @back="deselectSession"
                @resume-session="resumeSession"
                @edit-title="handleSessionEdit"
                @duplicate="handleSessionDuplicate"
                @export="handleSessionExport"
                @share="handleSessionShare"
                @archive="handleSessionArchive"
                @delete="handleSessionDelete"
                @load-more-messages="loadMoreMessages"
                @message-click="handleMessageClick"
                @view-related="selectSession"
                @add-tag="handleAddTag"
                @remove-tag="handleRemoveTag"
                @retry="retryLoadDetail"
                class="h-full"
              />
            </div>
          </div>
        </div>
      </main>

      <!-- 删除确认弹窗 -->
      <Dialog :open="showDeleteConfirm" @update:open="showDeleteConfirm = $event">
        <DialogContent>
          <DialogHeader>
            <DialogTitle>删除会话</DialogTitle>
            <DialogDescription>
              确定要删除会话 "{{ sessionToDelete?.title }}" 吗？此操作无法撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <button class="btn btn-outline" @click="showDeleteConfirm = false">
              取消
            </button>
            <button class="btn btn-destructive" @click="confirmDeleteSession">
              删除
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <!-- 批量删除确认弹窗 -->
      <Dialog :open="showBatchDeleteConfirm" @update:open="showBatchDeleteConfirm = $event">
        <DialogContent>
          <DialogHeader>
            <DialogTitle>批量删除会话</DialogTitle>
            <DialogDescription>
              确定要删除选中的 {{ sessionsToDelete.length }} 个会话吗？此操作无法撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <button class="btn btn-outline" @click="showBatchDeleteConfirm = false">
              取消
            </button>
            <button class="btn btn-destructive" @click="confirmBatchDelete">
              删除 {{ sessionsToDelete.length }} 个会话
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  </AuthGuard>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useBreakpoints } from '@vueuse/core'
import { 
  ArrowLeft,
  Search,
  X,
  Filter,
  Plus
} from 'lucide-vue-next'

import AuthGuard from '@/components/AuthGuard.vue'
import SessionList from '@/components/SessionList.vue'
import SessionDetail from '@/components/SessionDetail.vue'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import type { ChatSession, Message, SessionStatsResponse } from '@/types/chat'

// UI组件占位符
const Dialog = { name: 'Dialog' }
const DialogContent = { name: 'DialogContent' }
const DialogHeader = { name: 'DialogHeader' }
const DialogTitle = { name: 'DialogTitle' }
const DialogDescription = { name: 'DialogDescription' }
const DialogFooter = { name: 'DialogFooter' }
const DropdownMenu = { name: 'DropdownMenu' }
const DropdownMenuTrigger = { name: 'DropdownMenuTrigger' }
const DropdownMenuContent = { name: 'DropdownMenuContent' }
const DropdownMenuItem = { name: 'DropdownMenuItem' }
const DropdownMenuLabel = { name: 'DropdownMenuLabel' }
const DropdownMenuSeparator = { name: 'DropdownMenuSeparator' }

// 路由和store
const router = useRouter()
const chatStore = useChatStore()
const authStore = useAuthStore()

// 响应式断点检测
const breakpoints = useBreakpoints({
  mobile: 768,
  tablet: 1024
})
const isMobile = breakpoints.smaller('mobile')

// 响应式状态
const isLoading = ref(false)
const isLoadingMore = ref(false)
const isLoadingDetail = ref(false)
const isLoadingMessages = ref(false)
const detailError = ref('')

const selectedSession = ref<ChatSession | null>(null)
const selectedSessionMessages = ref<Message[]>([])
const selectedSessionStats = ref<SessionStatsResponse | null>(null)
const relatedSessions = ref<ChatSession[]>([])

const globalSearchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const useInfiniteScroll = ref(false)

// 筛选状态
const filters = ref({
  dateRange: '',
  status: '',
  agentName: '',
  minMessages: null as number | null,
  maxMessages: null as number | null
})

// 删除状态
const showDeleteConfirm = ref(false)
const showBatchDeleteConfirm = ref(false)
const sessionToDelete = ref<ChatSession | null>(null)
const sessionsToDelete = ref<string[]>([])

// 计算属性
const sessions = computed(() => chatStore.sessions)
const totalCount = computed(() => chatStore.totalSessionCount)
const hasMore = computed(() => sessions.value.length < totalCount.value)
const canLoadMoreMessages = computed(() => false) // TODO: 实现消息分页

const availableAgents = computed(() => {
  const agents = new Set(sessions.value.map(s => s.agent_name).filter(Boolean))
  return Array.from(agents)
})

const activeFiltersCount = computed(() => {
  let count = 0
  if (filters.value.dateRange) count++
  if (filters.value.status) count++
  if (filters.value.agentName) count++
  if (filters.value.minMessages !== null) count++
  if (filters.value.maxMessages !== null) count++
  return count
})

const filteredSessions = computed(() => {
  let filtered = [...sessions.value]
  
  // 全局搜索
  if (globalSearchQuery.value.trim()) {
    const query = globalSearchQuery.value.toLowerCase()
    filtered = filtered.filter(session =>
      session.title.toLowerCase().includes(query)
    )
  }
  
  // 应用筛选器
  if (filters.value.status) {
    filtered = filtered.filter(session =>
      filters.value.status === 'active' ? session.is_active : !session.is_active
    )
  }
  
  if (filters.value.agentName) {
    filtered = filtered.filter(session =>
      session.agent_name === filters.value.agentName
    )
  }
  
  if (filters.value.minMessages !== null) {
    filtered = filtered.filter(session =>
      session.message_count >= filters.value.minMessages!
    )
  }
  
  if (filters.value.maxMessages !== null) {
    filtered = filtered.filter(session =>
      session.message_count <= filters.value.maxMessages!
    )
  }
  
  // 时间范围筛选
  if (filters.value.dateRange) {
    const now = new Date()
    let startDate: Date
    
    switch (filters.value.dateRange) {
      case 'today':
        startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
        break
      case 'week':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        break
      case 'month':
        startDate = new Date(now.getFullYear(), now.getMonth(), 1)
        break
      case 'year':
        startDate = new Date(now.getFullYear(), 0, 1)
        break
      default:
        startDate = new Date(0)
    }
    
    filtered = filtered.filter(session =>
      new Date(session.updated_at) >= startDate
    )
  }
  
  return filtered
})

// 方法
const goBack = () => {
  if (selectedSession.value && isMobile.value) {
    deselectSession()
  } else {
    router.push('/chat')
  }
}

const createNewSession = async () => {
  try {
    const session = await chatStore.createSession({
      title: '新对话',
      agent_name: 'default'
    })
    router.push(`/chat/${session.id}`)
  } catch (error) {
    console.error('创建新对话失败:', error)
  }
}

const selectSession = async (session: ChatSession) => {
  if (selectedSession.value?.id === session.id) return
  
  selectedSession.value = session
  selectedSessionMessages.value = []
  selectedSessionStats.value = null
  relatedSessions.value = []
  detailError.value = ''
  
  await loadSessionDetail(session.id)
}

const deselectSession = () => {
  selectedSession.value = null
  selectedSessionMessages.value = []
  selectedSessionStats.value = null
  relatedSessions.value = []
}

const loadSessionDetail = async (sessionId: string) => {
  isLoadingDetail.value = true
  detailError.value = ''
  
  try {
    // 并行加载会话详情、消息和统计
    const [messages, stats] = await Promise.all([
      chatStore.getSessionMessages(sessionId),
      chatStore.getSessionStats(sessionId).catch(() => null)
    ])
    
    selectedSessionMessages.value = messages
    selectedSessionStats.value = stats
    
    // 加载相关会话
    await loadRelatedSessions(sessionId)
  } catch (error) {
    console.error('加载会话详情失败:', error)
    detailError.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    isLoadingDetail.value = false
  }
}

const loadRelatedSessions = async (sessionId: string) => {
  try {
    // TODO: 实现相关会话推荐逻辑
    // 暂时返回最近的几个会话作为相关会话
    relatedSessions.value = sessions.value
      .filter(s => s.id !== sessionId)
      .slice(0, 5)
  } catch (error) {
    console.error('加载相关会话失败:', error)
  }
}

const loadMoreMessages = async () => {
  // TODO: 实现消息分页加载
}

const retryLoadDetail = () => {
  if (selectedSession.value) {
    loadSessionDetail(selectedSession.value.id)
  }
}

// 搜索和筛选
const performGlobalSearch = () => {
  currentPage.value = 1
  // 搜索会自动通过computed属性触发
}

const clearGlobalSearch = () => {
  globalSearchQuery.value = ''
}

const resetFilters = () => {
  filters.value = {
    dateRange: '',
    status: '',
    agentName: '',
    minMessages: null,
    maxMessages: null
  }
}

const applyFilters = () => {
  currentPage.value = 1
  // 筛选会自动通过computed属性触发
}

// 会话操作处理
const handleSessionEdit = async (session: ChatSession) => {
  const newTitle = prompt('请输入新的会话标题:', session.title)
  if (newTitle && newTitle.trim()) {
    try {
      await chatStore.updateSession(session.id, { title: newTitle.trim() })
      if (selectedSession.value?.id === session.id) {
        selectedSession.value.title = newTitle.trim()
      }
    } catch (error) {
      console.error('更新会话标题失败:', error)
    }
  }
}

const handleSessionDuplicate = async (session: ChatSession) => {
  try {
    const newSession = await chatStore.duplicateSession(session.id)
    // 可以选择跳转到新会话或显示成功提示
    console.log('会话已复制:', newSession.id)
  } catch (error) {
    console.error('复制会话失败:', error)
  }
}

const handleSessionArchive = async (session: ChatSession) => {
  try {
    await chatStore.updateSession(session.id, { is_active: !session.is_active })
    if (selectedSession.value?.id === session.id) {
      selectedSession.value.is_active = !session.is_active
    }
  } catch (error) {
    console.error('归档会话失败:', error)
  }
}

const handleSessionExport = async (session: ChatSession) => {
  try {
    // TODO: 实现会话导出功能
    console.log('导出会话:', session.id)
  } catch (error) {
    console.error('导出会话失败:', error)
  }
}

const handleSessionShare = async (session: ChatSession) => {
  try {
    // TODO: 实现会话分享功能
    console.log('分享会话:', session.id)
  } catch (error) {
    console.error('分享会话失败:', error)
  }
}

const handleSessionDelete = (session: ChatSession) => {
  sessionToDelete.value = session
  showDeleteConfirm.value = true
}

const confirmDeleteSession = async () => {
  if (!sessionToDelete.value) return
  
  try {
    await chatStore.deleteSession(sessionToDelete.value.id)
    if (selectedSession.value?.id === sessionToDelete.value.id) {
      deselectSession()
    }
    showDeleteConfirm.value = false
    sessionToDelete.value = null
  } catch (error) {
    console.error('删除会话失败:', error)
  }
}

// 批量操作
const handleBatchArchive = async (sessionIds: string[]) => {
  try {
    await Promise.all(
      sessionIds.map(id => {
        const session = sessions.value.find(s => s.id === id)
        return session ? chatStore.updateSession(id, { is_active: !session.is_active }) : Promise.resolve()
      })
    )
  } catch (error) {
    console.error('批量归档失败:', error)
  }
}

const handleBatchExport = async (sessionIds: string[]) => {
  try {
    // TODO: 实现批量导出
    console.log('批量导出会话:', sessionIds)
  } catch (error) {
    console.error('批量导出失败:', error)
  }
}

const handleBatchDelete = (sessionIds: string[]) => {
  sessionsToDelete.value = sessionIds
  showBatchDeleteConfirm.value = true
}

const confirmBatchDelete = async () => {
  try {
    await Promise.all(
      sessionsToDelete.value.map(id => chatStore.deleteSession(id))
    )
    
    // 如果当前选中的会话被删除，取消选择
    if (selectedSession.value && sessionsToDelete.value.includes(selectedSession.value.id)) {
      deselectSession()
    }
    
    showBatchDeleteConfirm.value = false
    sessionsToDelete.value = []
  } catch (error) {
    console.error('批量删除失败:', error)
  }
}

// 其他处理
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadSessions()
}

const handleSortChange = (sortBy: string, sortOrder: 'asc' | 'desc') => {
  // TODO: 实现排序
  console.log('排序变更:', sortBy, sortOrder)
}

const handleViewModeChange = (mode: 'list' | 'grid' | 'compact') => {
  // TODO: 保存视图模式到本地存储
  console.log('视图模式变更:', mode)
}

const loadMoreSessions = () => {
  isLoadingMore.value = true
  // TODO: 实现无限滚动加载
  setTimeout(() => {
    isLoadingMore.value = false
  }, 1000)
}

const resumeSession = (session: ChatSession) => {
  router.push(`/chat/${session.id}`)
}

const handleMessageClick = (message: Message) => {
  console.log('消息点击:', message)
}

const handleAddTag = async (sessionId: string, tag: string) => {
  try {
    // TODO: 实现标签添加
    console.log('添加标签:', sessionId, tag)
  } catch (error) {
    console.error('添加标签失败:', error)
  }
}

const handleRemoveTag = async (sessionId: string, tag: string) => {
  try {
    // TODO: 实现标签移除
    console.log('移除标签:', sessionId, tag)
  } catch (error) {
    console.error('移除标签失败:', error)
  }
}

// 加载会话数据
const loadSessions = async () => {
  if (isLoading.value) return
  
  isLoading.value = true
  try {
    await chatStore.fetchSessions(currentPage.value, pageSize.value)
  } catch (error) {
    console.error('加载会话列表失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadSessions()
  document.title = '会话历史 - AI助手'
})

// 监听移动端状态变化
watch(isMobile, (mobile) => {
  if (!mobile && selectedSession.value) {
    // 从移动端切换到桌面端时，确保详情面板显示
    nextTick(() => {
      // 可以做一些布局调整
    })
  }
})
</script>

<style scoped>
.history-view {
  @apply flex flex-col h-screen bg-background;
}

/* 头部导航 */
.history-header {
  @apply border-b border-border bg-card sticky top-0 z-40;
}

.history-header .container {
  @apply max-w-none;
}

/* 主要内容 */
.history-main {
  @apply flex-1 overflow-hidden;
}

.history-content {
  @apply flex h-full;
}

.history-content.show-detail .sessions-panel {
  @apply border-r border-border;
}

/* 会话面板 */
.sessions-panel {
  @apply w-full transition-all duration-300;
}

.history-content.show-detail .sessions-panel {
  @apply w-96 flex-shrink-0;
}

/* 详情面板 */
.detail-panel {
  @apply flex-1 bg-card;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .history-content.show-detail .sessions-panel {
    @apply hidden;
  }
  
  .detail-panel {
    @apply w-full;
  }
  
  .history-header .container {
    @apply px-3;
  }
  
  .history-header .flex {
    @apply flex-col space-y-4 space-x-0;
  }
  
  .history-header .flex > div:first-child {
    @apply w-full;
  }
  
  .history-header .flex > div:last-child {
    @apply w-full justify-between;
  }
  
  .history-header .flex > div:last-child > div:first-child {
    @apply w-full max-w-none;
  }
  
  .history-header input {
    @apply w-full;
  }
}

@media (max-width: 640px) {
  .history-header {
    @apply py-3;
  }
  
  .history-header .flex > div:last-child {
    @apply flex-col space-x-0 space-y-3;
  }
  
  .history-header .flex > div:last-child > div {
    @apply w-full;
  }
}

/* 筛选面板样式 */
.filter-section {
  @apply space-y-4 p-4;
}

.filter-section label {
  @apply text-sm font-medium text-foreground;
}

.filter-section input,
.filter-section select {
  @apply mt-1;
}

/* 动画效果 */
.history-view {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.sessions-panel,
.detail-panel {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 过渡效果 */
.sessions-panel {
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.detail-panel {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 搜索框样式增强 */
.history-header input[type="text"] {
  @apply transition-all duration-200;
}

.history-header input[type="text"]:focus {
  @apply ring-2 ring-primary ring-offset-2 shadow-sm;
}

/* 筛选按钮激活状态 */
.btn:has(+ [data-active="true"]) {
  @apply bg-primary/10 text-primary border-primary/20;
}

/* 优化小屏幕下的筛选面板 */
@media (max-width: 768px) {
  .filter-dropdown {
    @apply w-screen max-w-sm;
  }
}

/* 加载状态 */
.loading-overlay {
  @apply absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50;
}

/* 空状态优化 */
.empty-state {
  @apply py-16 text-center;
}

.empty-state h3 {
  @apply text-xl font-medium mb-2;
}

.empty-state p {
  @apply text-muted-foreground mb-6;
}

/* 标签样式 */
.filter-badge {
  @apply inline-flex items-center px-2 py-1 bg-primary text-primary-foreground text-xs rounded-full font-medium;
}

/* 确保对话框在移动端的显示 */
@media (max-width: 640px) {
  .dialog-content {
    @apply max-w-[90vw] max-h-[90vh];
  }
}

/* 高对比度模式支持 */
@media (prefers-contrast: high) {
  .history-header {
    @apply border-b-2;
  }
  
  .sessions-panel {
    @apply border-r-2;
  }
  
  .btn {
    @apply border-2;
  }
}

/* 减少动画模式 */
@media (prefers-reduced-motion: reduce) {
  * {
    @apply transition-none;
  }
  
  .sessions-panel,
  .detail-panel,
  .history-view {
    animation: none;
  }
}

/* 打印样式 */
@media print {
  .history-header,
  .btn,
  .dropdown-menu {
    @apply hidden;
  }
  
  .history-content {
    @apply block;
  }
  
  .sessions-panel,
  .detail-panel {
    @apply w-full border-0;
  }
}
</style>