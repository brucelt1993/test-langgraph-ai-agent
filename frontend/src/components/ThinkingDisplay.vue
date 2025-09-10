<template>
  <div class="thinking-display" :class="displayClass">
    <!-- 头部控制栏 -->
    <div class="thinking-header">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="thinking-icon">
            <Brain class="w-5 h-5" />
          </div>
          <div>
            <h3 class="text-base font-semibold">AI思考过程</h3>
            <p class="text-sm text-muted-foreground">
              {{ getThinkingSummary() }}
            </p>
          </div>
        </div>
        
        <div class="flex items-center space-x-2">
          <!-- 过滤器 -->
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                class="btn btn-ghost btn-sm"
                title="筛选步骤"
              >
                <Filter class="w-4 h-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>步骤类型</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                v-for="type in availableTypes"
                :key="type.value"
                @click="toggleFilter(type.value)"
              >
                <input
                  type="checkbox"
                  :checked="activeFilters.includes(type.value)"
                  class="w-4 h-4 mr-2"
                />
                <component :is="type.icon" class="w-4 h-4 mr-2" />
                {{ type.label }}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="clearFilters">
                <RotateCcw class="w-4 h-4 mr-2" />
                清除筛选
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          
          <!-- 视图模式 -->
          <div class="btn-group">
            <button
              class="btn btn-ghost btn-sm"
              :class="{ 'btn-active': viewMode === 'timeline' }"
              @click="setViewMode('timeline')"
              title="时间线视图"
            >
              <Clock class="w-4 h-4" />
            </button>
            <button
              class="btn btn-ghost btn-sm"
              :class="{ 'btn-active': viewMode === 'tree' }"
              @click="setViewMode('tree')"
              title="树形视图"
            >
              <GitBranch class="w-4 h-4" />
            </button>
            <button
              class="btn btn-ghost btn-sm"
              :class="{ 'btn-active': viewMode === 'compact' }"
              @click="setViewMode('compact')"
              title="紧凑视图"
            >
              <List class="w-4 h-4" />
            </button>
          </div>
          
          <!-- 操作按钮 -->
          <button
            v-if="canExpandAll"
            class="btn btn-ghost btn-sm"
            @click="expandAll"
            title="展开所有"
          >
            <ChevronDown class="w-4 h-4" />
          </button>
          
          <button
            v-if="canCollapseAll"
            class="btn btn-ghost btn-sm"
            @click="collapseAll"
            title="折叠所有"
          >
            <ChevronUp class="w-4 h-4" />
          </button>
          
          <button
            class="btn btn-ghost btn-sm"
            @click="toggleVisible"
            :title="isVisible ? '隐藏思考过程' : '显示思考过程'"
          >
            <component :is="isVisible ? EyeOff : Eye" class="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <!-- 进度条 -->
      <div 
        v-if="showProgress && thinkingProgress"
        class="thinking-progress mt-3"
      >
        <div class="progress-bar">
          <div 
            class="progress-fill"
            :style="{ width: `${thinkingProgress.percentage}%` }"
          ></div>
        </div>
        <div class="flex justify-between text-xs text-muted-foreground mt-1">
          <span>{{ thinkingProgress.currentStep }} / {{ thinkingProgress.totalSteps }}</span>
          <span v-if="thinkingProgress.estimatedTime">
            预计剩余: {{ formatDuration(thinkingProgress.estimatedTime) }}
          </span>
        </div>
      </div>
    </div>

    <!-- 思考步骤内容 -->
    <div 
      v-show="isVisible"
      class="thinking-content"
      :class="{ 'compact-mode': viewMode === 'compact' }"
    >
      <!-- 空状态 -->
      <div 
        v-if="!filteredSteps.length"
        class="empty-state"
      >
        <div class="empty-icon">
          <Brain class="w-12 h-12 text-muted-foreground/50" />
        </div>
        <h4 class="empty-title">
          {{ activeFilters.length > 0 ? '没有匹配的思考步骤' : '暂无思考过程' }}
        </h4>
        <p class="empty-description">
          {{ activeFilters.length > 0 ? '尝试调整筛选条件' : 'AI正在处理您的请求...' }}
        </p>
      </div>

      <!-- 步骤列表 -->
      <div v-else class="steps-container" :class="containerClass">
        <!-- 时间线视图 -->
        <div v-if="viewMode === 'timeline'" class="timeline-view">
          <div 
            v-for="(step, index) in filteredSteps"
            :key="index"
            class="timeline-item"
          >
            <div class="timeline-marker">
              <div class="timeline-dot" :class="getTimelineDotClass(step, index)"></div>
              <div 
                v-if="index < filteredSteps.length - 1"
                class="timeline-line"
              ></div>
            </div>
            <div class="timeline-content">
              <ThinkingStep
                :step="step"
                :step-number="index + 1"
                :level="0"
                :show-animations="showAnimations"
                :compact-mode="viewMode === 'compact'"
                :default-expanded="defaultExpanded"
                @expand-change="handleStepExpandChange"
                @step-click="handleStepClick"
              />
            </div>
          </div>
        </div>

        <!-- 树形视图 -->
        <div v-else-if="viewMode === 'tree'" class="tree-view space-y-3">
          <ThinkingStep
            v-for="(step, index) in filteredSteps"
            :key="index"
            :step="step"
            :step-number="index + 1"
            :level="0"
            :show-animations="showAnimations"
            :compact-mode="false"
            :default-expanded="defaultExpanded"
            @expand-change="handleStepExpandChange"
            @step-click="handleStepClick"
          />
        </div>

        <!-- 紧凑视图 -->
        <div v-else class="compact-view space-y-2">
          <ThinkingStep
            v-for="(step, index) in filteredSteps"
            :key="index"
            :step="step"
            :step-number="index + 1"
            :level="0"
            :show-animations="showAnimations"
            :compact-mode="true"
            :default-expanded="false"
            @expand-change="handleStepExpandChange"
            @step-click="handleStepClick"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { 
  Brain,
  Filter,
  Clock,
  GitBranch,
  List,
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  Search,
  Lightbulb,
  Target,
  CheckCircle,
  RotateCcw
} from 'lucide-vue-next'
import ThinkingStep, { type ThinkingStepData } from './ThinkingStep.vue'

// UI组件占位符
const DropdownMenu = { name: 'DropdownMenu' }
const DropdownMenuTrigger = { name: 'DropdownMenuTrigger' }
const DropdownMenuContent = { name: 'DropdownMenuContent' }
const DropdownMenuItem = { name: 'DropdownMenuItem' }
const DropdownMenuLabel = { name: 'DropdownMenuLabel' }
const DropdownMenuSeparator = { name: 'DropdownMenuSeparator' }

export interface ThinkingProgress {
  currentStep: number
  totalSteps: number
  percentage: number
  estimatedTime?: number
}

export interface ThinkingDisplayProps {
  steps: ThinkingStepData[]
  progress?: ThinkingProgress
  showProgress?: boolean
  showAnimations?: boolean
  defaultExpanded?: boolean
  allowFiltering?: boolean
  allowViewModes?: boolean
  initialViewMode?: 'timeline' | 'tree' | 'compact'
  compactHeader?: boolean
}

const props = withDefaults(defineProps<ThinkingDisplayProps>(), {
  steps: () => [],
  showProgress: true,
  showAnimations: true,
  defaultExpanded: false,
  allowFiltering: true,
  allowViewModes: true,
  initialViewMode: 'timeline',
  compactHeader: false
})

const emit = defineEmits<{
  'step-expand': [stepIndex: number, expanded: boolean]
  'step-click': [step: ThinkingStepData, stepIndex: number]
  'filter-change': [filters: string[]]
  'view-mode-change': [mode: string]
  'visibility-change': [visible: boolean]
}>()

// 响应式状态
const isVisible = ref(true)
const viewMode = ref(props.initialViewMode)
const activeFilters = ref<string[]>([])
const expandedSteps = ref(new Set<number>())

// 步骤类型配置
const availableTypes = [
  { value: 'analysis', label: '分析', icon: Brain },
  { value: 'search', label: '搜索', icon: Search },
  { value: 'reasoning', label: '推理', icon: Lightbulb },
  { value: 'decision', label: '决策', icon: Target },
  { value: 'validation', label: '验证', icon: CheckCircle },
  { value: 'action', label: '执行', icon: CheckCircle }
]

// 计算属性
const displayClass = computed(() => [
  'thinking-display-container',
  {
    'compact-header': props.compactHeader,
    'hidden-content': !isVisible.value,
    [`view-${viewMode.value}`]: true
  }
])

const containerClass = computed(() => [
  'steps-list',
  {
    'with-animations': props.showAnimations
  }
])

const filteredSteps = computed(() => {
  if (activeFilters.value.length === 0) {
    return props.steps
  }
  
  return props.steps.filter(step => 
    activeFilters.value.includes(step.type || 'reasoning')
  )
})

const thinkingProgress = computed(() => props.progress)

const canExpandAll = computed(() => {
  return expandedSteps.value.size < filteredSteps.value.length
})

const canCollapseAll = computed(() => {
  return expandedSteps.value.size > 0
})

// 方法
const getThinkingSummary = () => {
  const total = props.steps.length
  const completed = props.steps.filter(step => !step.error).length
  const hasErrors = props.steps.some(step => step.error)
  
  if (total === 0) return '等待AI思考...'
  
  let summary = `${completed}/${total} 个步骤`
  if (hasErrors) summary += ' (存在错误)'
  
  return summary
}

const toggleFilter = (type: string) => {
  const index = activeFilters.value.indexOf(type)
  if (index > -1) {
    activeFilters.value.splice(index, 1)
  } else {
    activeFilters.value.push(type)
  }
  emit('filter-change', activeFilters.value)
}

const clearFilters = () => {
  activeFilters.value = []
  emit('filter-change', [])
}

const setViewMode = (mode: 'timeline' | 'tree' | 'compact') => {
  viewMode.value = mode
  emit('view-mode-change', mode)
}

const expandAll = () => {
  filteredSteps.value.forEach((_, index) => {
    expandedSteps.value.add(index)
  })
}

const collapseAll = () => {
  expandedSteps.value.clear()
}

const toggleVisible = () => {
  isVisible.value = !isVisible.value
  emit('visibility-change', isVisible.value)
}

const handleStepExpandChange = (expanded: boolean, stepNumber: number) => {
  const stepIndex = stepNumber - 1
  if (expanded) {
    expandedSteps.value.add(stepIndex)
  } else {
    expandedSteps.value.delete(stepIndex)
  }
  emit('step-expand', stepIndex, expanded)
}

const handleStepClick = (step: ThinkingStepData, stepNumber: number) => {
  emit('step-click', step, stepNumber - 1)
}

const getTimelineDotClass = (step: ThinkingStepData, index: number) => {
  if (step.error) return 'dot-error'
  
  const type = step.type || 'reasoning'
  return `dot-${type}`
}

const formatDuration = (duration: number): string => {
  if (duration < 1000) return `${duration}ms`
  if (duration < 60000) return `${Math.round(duration / 1000)}s`
  return `${Math.floor(duration / 60000)}m`
}

// 监听器
watch(() => props.steps, () => {
  // 当步骤更新时，清理无效的展开状态
  const validIndices = new Set(
    Array.from({ length: props.steps.length }, (_, i) => i)
  )
  
  expandedSteps.value.forEach(index => {
    if (!validIndices.has(index)) {
      expandedSteps.value.delete(index)
    }
  })
}, { deep: true })

// 暴露方法
defineExpose({
  expand: expandAll,
  collapse: collapseAll,
  toggleVisibility: toggleVisible,
  setFilters: (filters: string[]) => { activeFilters.value = filters },
  setViewMode,
  isVisible: computed(() => isVisible.value),
  viewMode: computed(() => viewMode.value),
  activeFilters: computed(() => activeFilters.value)
})
</script>

<style scoped>
.thinking-display-container {
  @apply bg-card border border-border rounded-lg overflow-hidden;
}

.thinking-header {
  @apply p-4 border-b border-border bg-muted/30;
}

.thinking-display-container.compact-header .thinking-header {
  @apply p-3;
}

.thinking-icon {
  @apply w-10 h-10 bg-primary/10 text-primary rounded-full flex items-center justify-center;
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

.progress-bar {
  @apply w-full bg-muted rounded-full h-2 overflow-hidden;
}

.progress-fill {
  @apply h-full bg-primary transition-all duration-300 ease-out;
}

.thinking-content {
  @apply max-h-96 overflow-y-auto;
}

.thinking-content.compact-mode {
  @apply max-h-80;
}

.empty-state {
  @apply flex flex-col items-center justify-center py-12 text-center;
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

/* 时间线视图样式 */
.timeline-view {
  @apply p-4 space-y-4;
}

.timeline-item {
  @apply flex;
}

.timeline-marker {
  @apply flex flex-col items-center mr-4;
}

.timeline-dot {
  @apply w-3 h-3 rounded-full flex-shrink-0;
}

.timeline-dot.dot-analysis {
  @apply bg-blue-500;
}

.timeline-dot.dot-search {
  @apply bg-green-500;
}

.timeline-dot.dot-reasoning {
  @apply bg-yellow-500;
}

.timeline-dot.dot-decision {
  @apply bg-purple-500;
}

.timeline-dot.dot-validation {
  @apply bg-emerald-500;
}

.timeline-dot.dot-action {
  @apply bg-orange-500;
}

.timeline-dot.dot-error {
  @apply bg-destructive;
}

.timeline-line {
  @apply w-0.5 bg-border flex-1 mt-2;
}

.timeline-content {
  @apply flex-1 min-w-0;
}

/* 树形视图样式 */
.tree-view {
  @apply p-4;
}

/* 紧凑视图样式 */
.compact-view {
  @apply p-3;
}

/* 滚动条样式 */
.thinking-content::-webkit-scrollbar {
  @apply w-2;
}

.thinking-content::-webkit-scrollbar-track {
  @apply bg-transparent;
}

.thinking-content::-webkit-scrollbar-thumb {
  @apply bg-border rounded-full;
}

.thinking-content::-webkit-scrollbar-thumb:hover {
  @apply bg-border/80;
}

/* 响应式调整 */
@media (max-width: 640px) {
  .thinking-header {
    @apply p-3;
  }
  
  .thinking-content {
    @apply max-h-72;
  }
  
  .timeline-view,
  .tree-view,
  .compact-view {
    @apply p-2;
  }
  
  .btn-group {
    @apply flex-col w-auto;
  }
  
  .btn-group .btn:not(:last-child) {
    @apply border-r-0 border-b border-border;
  }
}
</style>