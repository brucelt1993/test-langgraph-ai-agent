<template>
  <AuthGuard>
    <div class="min-h-screen bg-background">
      <!-- 头部 -->
      <header class="border-b border-border bg-card">
        <div class="container mx-auto px-4 py-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold">聊天记录</h1>
              <p class="text-muted-foreground">管理您的AI对话会话</p>
            </div>
            
            <button
              class="btn btn-primary"
              @click="createNewChat"
            >
              <Plus class="w-4 h-4 mr-2" />
              新建对话
            </button>
          </div>
        </div>
      </header>

      <!-- 主要内容 -->
      <main class="container mx-auto px-4 py-6">
        <!-- 搜索和筛选 -->
        <div class="flex flex-col sm:flex-row gap-4 mb-6">
          <div class="flex-1">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索对话..."
              class="input w-full"
            />
          </div>
          <select v-model="filterStatus" class="input w-full sm:w-48">
            <option value="all">所有会话</option>
            <option value="active">活跃会话</option>
            <option value="archived">已归档</option>
          </select>
        </div>

        <!-- 会话列表 -->
        <div v-if="isLoading" class="text-center py-8">
          <div class="loading-spinner w-8 h-8 mx-auto border-primary"></div>
          <p class="text-muted-foreground mt-2">加载中...</p>
        </div>

        <div v-else-if="filteredSessions.length === 0" class="text-center py-12">
          <div class="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
            <MessageSquare class="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 class="text-lg font-medium mb-2">
            {{ searchQuery ? '没有找到匹配的对话' : '还没有对话记录' }}
          </h3>
          <p class="text-muted-foreground mb-4">
            {{ searchQuery ? '尝试调整搜索条件' : '开始您的第一次AI对话吧' }}
          </p>
          <button
            class="btn btn-primary"
            @click="createNewChat"
          >
            创建新对话
          </button>
        </div>

        <div v-else class="grid gap-4">
          <div
            v-for="session in filteredSessions"
            :key="session.id"
            class="card cursor-pointer hover:shadow-md transition-shadow"
            @click="openChat(session.id)"
          >
            <div class="card-content p-4">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <h3 class="font-medium truncate">{{ session.title }}</h3>
                  <p class="text-sm text-muted-foreground mt-1">
                    {{ formatRelativeTime(session.updated_at) }}
                  </p>
                  <p class="text-sm text-muted-foreground">
                    {{ session.message_count }} 条消息 • {{ session.agent_name }}
                  </p>
                </div>
                
                <div class="flex items-center space-x-2 ml-4">
                  <!-- 会话状态指示器 -->
                  <div
                    class="w-2 h-2 rounded-full"
                    :class="session.is_active ? 'bg-green-500' : 'bg-muted'"
                    :title="session.is_active ? '活跃' : '已归档'"
                  ></div>
                  
                  <!-- 操作按钮 -->
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
                      <DropdownMenuItem @click.stop="editSession(session)">
                        <Edit3 class="w-4 h-4 mr-2" />
                        编辑标题
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
                        @click.stop="confirmDeleteSession(session)"
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
          </div>

          <!-- 分页 -->
          <div 
            v-if="totalPages > 1"
            class="flex justify-center items-center space-x-2 mt-6"
          >
            <button
              class="btn btn-outline btn-sm"
              :disabled="currentPage <= 1"
              @click="changePage(currentPage - 1)"
            >
              上一页
            </button>
            
            <span class="text-sm text-muted-foreground">
              {{ currentPage }} / {{ totalPages }}
            </span>
            
            <button
              class="btn btn-outline btn-sm"
              :disabled="currentPage >= totalPages"
              @click="changePage(currentPage + 1)"
            >
              下一页
            </button>
          </div>
        </div>
      </main>

      <!-- 删除确认弹窗 -->
      <Dialog :open="showDeleteConfirm" @update:open="showDeleteConfirm = $event">
        <DialogContent>
          <DialogHeader>
            <DialogTitle>删除对话</DialogTitle>
            <DialogDescription>
              确定要删除对话 "{{ sessionToDelete?.title }}" 吗？此操作无法撤销。
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <button class="btn btn-outline" @click="showDeleteConfirm = false">
              取消
            </button>
            <button class="btn btn-destructive" @click="deleteSession">
              删除
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  </AuthGuard>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Plus, 
  MessageSquare, 
  MoreVertical, 
  Edit3, 
  Archive, 
  Download, 
  Trash2 
} from 'lucide-vue-next'

import AuthGuard from '@/components/AuthGuard.vue'
import { useChatStore } from '@/stores/chat'
import type { ChatSession } from '@/types/chat'

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
const DropdownMenuSeparator = { name: 'DropdownMenuSeparator' }

// 路由和状态
const router = useRouter()
const chatStore = useChatStore()

// 响应式状态
const isLoading = ref(false)
const searchQuery = ref('')
const filterStatus = ref('all')
const currentPage = ref(1)
const pageSize = ref(20)
const showDeleteConfirm = ref(false)
const sessionToDelete = ref<ChatSession | null>(null)

// 计算属性
const sessions = computed(() => chatStore.sessions)

const filteredSessions = computed(() => {
  let filtered = sessions.value

  // 根据状态筛选
  if (filterStatus.value === 'active') {
    filtered = filtered.filter(session => session.is_active)
  } else if (filterStatus.value === 'archived') {
    filtered = filtered.filter(session => !session.is_active)
  }

  // 根据搜索查询筛选
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(session =>
      session.title.toLowerCase().includes(query)
    )
  }

  return filtered
})

const totalPages = computed(() => 
  Math.ceil(filteredSessions.value.length / pageSize.value)
)

// 创建新对话
const createNewChat = async () => {
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

// 打开对话
const openChat = (sessionId: string) => {
  router.push(`/chat/${sessionId}`)
}

// 编辑会话
const editSession = (session: ChatSession) => {
  const newTitle = prompt('请输入新的会话标题:', session.title)
  if (newTitle && newTitle.trim()) {
    chatStore.updateSession(session.id, { title: newTitle.trim() })
  }
}

// 归档/取消归档会话
const archiveSession = (session: ChatSession) => {
  chatStore.updateSession(session.id, { is_active: !session.is_active })
}

// 导出会话
const exportSession = (session: ChatSession) => {
  // TODO: 实现导出功能
  console.log('导出会话:', session.id)
}

// 确认删除会话
const confirmDeleteSession = (session: ChatSession) => {
  sessionToDelete.value = session
  showDeleteConfirm.value = true
}

// 删除会话
const deleteSession = async () => {
  if (!sessionToDelete.value) return

  try {
    await chatStore.deleteSession(sessionToDelete.value.id)
    showDeleteConfirm.value = false
    sessionToDelete.value = null
  } catch (error) {
    console.error('删除会话失败:', error)
  }
}

// 分页
const changePage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

// 格式化相对时间
const formatRelativeTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  const week = 7 * day
  const month = 30 * day

  if (diff < minute) {
    return '刚刚'
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)} 分钟前`
  } else if (diff < day) {
    return `${Math.floor(diff / hour)} 小时前`
  } else if (diff < week) {
    return `${Math.floor(diff / day)} 天前`
  } else if (diff < month) {
    return `${Math.floor(diff / week)} 周前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 加载会话列表
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

// 监听页面变化
watch(currentPage, () => {
  loadSessions()
})

// 监听搜索查询变化，重置页面
watch(searchQuery, () => {
  currentPage.value = 1
})

// 监听筛选状态变化，重置页面
watch(filterStatus, () => {
  currentPage.value = 1
})

// 初始化
onMounted(() => {
  loadSessions()
  document.title = '聊天记录 - AI助手'
})
</script>

<style scoped>
/* 自定义样式 */
.loading-spinner {
  border-color: currentColor;
  border-right-color: transparent;
}

/* 卡片悬停效果 */
.card {
  @apply transition-all duration-200;
}

.card:hover {
  @apply transform translate-y-[-1px];
}

/* 按钮样式 */
.btn:hover {
  @apply transition-colors duration-200;
}

/* 响应式调整 */
@media (max-width: 640px) {
  .card-content {
    @apply p-3;
  }
  
  .container {
    @apply px-3;
  }
}
</style>