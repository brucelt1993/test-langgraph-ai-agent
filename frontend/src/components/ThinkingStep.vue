<template>
  <div 
    class="thinking-step"
    :class="stepClass"
  >
    <!-- 步骤头部 -->
    <div 
      class="step-header cursor-pointer"
      @click="toggleExpanded"
    >
      <div class="flex items-center space-x-3">
        <!-- 步骤图标 -->
        <div 
          class="step-icon"
          :class="iconClass"
        >
          <component 
            :is="stepIcon" 
            class="w-4 h-4"
          />
        </div>
        
        <!-- 步骤信息 -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between">
            <h4 class="step-title font-medium text-sm truncate">
              {{ step.title || `步骤 ${stepNumber}` }}
            </h4>
            <div class="flex items-center space-x-2">
              <!-- 置信度 -->
              <div 
                v-if="step.confidence"
                class="confidence-badge"
                :class="confidenceClass"
              >
                {{ Math.round(step.confidence * 100) }}%
              </div>
              
              <!-- 耗时 -->
              <div 
                v-if="step.duration"
                class="duration-badge text-xs text-muted-foreground"
              >
                {{ formatDuration(step.duration) }}
              </div>
              
              <!-- 展开/折叠图标 -->
              <component 
                :is="isExpanded ? ChevronDown : ChevronRight"
                class="w-4 h-4 text-muted-foreground transition-transform duration-200"
              />
            </div>
          </div>
          
          <!-- 步骤摘要 -->
          <p 
            v-if="step.summary"
            class="step-summary text-xs text-muted-foreground mt-1 line-clamp-2"
          >
            {{ step.summary }}
          </p>
        </div>
      </div>
    </div>

    <!-- 步骤详细内容 -->
    <div 
      v-show="isExpanded"
      class="step-content"
    >
      <!-- 步骤描述 -->
      <div 
        v-if="step.content"
        class="step-description mt-3 ml-8 p-3 bg-muted/30 rounded-lg"
      >
        <div 
          class="prose prose-sm max-w-none dark:prose-invert"
          v-html="formatContent(step.content)"
        ></div>
      </div>
      
      <!-- 输入数据 -->
      <div 
        v-if="step.inputs && Object.keys(step.inputs).length > 0"
        class="step-inputs mt-3 ml-8"
      >
        <h5 class="text-xs font-medium text-muted-foreground mb-2">输入数据</h5>
        <div class="bg-accent/20 rounded-lg p-3 space-y-2">
          <div 
            v-for="(value, key) in step.inputs" 
            :key="key"
            class="input-item"
          >
            <span class="text-xs font-mono text-accent-foreground">{{ key }}:</span>
            <span class="text-xs text-muted-foreground ml-2">{{ formatValue(value) }}</span>
          </div>
        </div>
      </div>
      
      <!-- 输出结果 -->
      <div 
        v-if="step.outputs && Object.keys(step.outputs).length > 0"
        class="step-outputs mt-3 ml-8"
      >
        <h5 class="text-xs font-medium text-muted-foreground mb-2">输出结果</h5>
        <div class="bg-secondary/20 rounded-lg p-3 space-y-2">
          <div 
            v-for="(value, key) in step.outputs" 
            :key="key"
            class="output-item"
          >
            <span class="text-xs font-mono text-secondary-foreground">{{ key }}:</span>
            <span class="text-xs text-muted-foreground ml-2">{{ formatValue(value) }}</span>
          </div>
        </div>
      </div>
      
      <!-- 子步骤 -->
      <div 
        v-if="step.substeps && step.substeps.length > 0"
        class="substeps mt-3 ml-8 space-y-2"
      >
        <h5 class="text-xs font-medium text-muted-foreground mb-2">子步骤</h5>
        <div class="substeps-container border-l-2 border-muted pl-4">
          <ThinkingStep
            v-for="(substep, index) in step.substeps"
            :key="index"
            :step="substep"
            :step-number="index + 1"
            :level="level + 1"
            :show-animations="showAnimations"
            :compact-mode="compactMode"
          />
        </div>
      </div>
      
      <!-- 错误信息 -->
      <div 
        v-if="step.error"
        class="step-error mt-3 ml-8 p-3 bg-destructive/10 border border-destructive/20 rounded-lg"
      >
        <div class="flex items-center space-x-2 text-destructive">
          <AlertCircle class="w-4 h-4" />
          <span class="text-sm font-medium">错误</span>
        </div>
        <p class="text-sm text-destructive/80 mt-1">
          {{ step.error }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  ChevronDown, 
  ChevronRight,
  Brain,
  Search,
  Lightbulb,
  Target,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-vue-next'

export interface ThinkingStepData {
  title?: string
  summary?: string
  content?: string
  type?: 'analysis' | 'search' | 'reasoning' | 'decision' | 'action' | 'validation'
  confidence?: number
  duration?: number
  inputs?: Record<string, any>
  outputs?: Record<string, any>
  substeps?: ThinkingStepData[]
  error?: string
  timestamp?: string
}

export interface ThinkingStepProps {
  step: ThinkingStepData
  stepNumber?: number
  level?: number
  showAnimations?: boolean
  compactMode?: boolean
  defaultExpanded?: boolean
}

const props = withDefaults(defineProps<ThinkingStepProps>(), {
  stepNumber: 1,
  level: 0,
  showAnimations: true,
  compactMode: false,
  defaultExpanded: false
})

const emit = defineEmits<{
  'expand-change': [expanded: boolean, stepNumber: number]
  'step-click': [step: ThinkingStepData, stepNumber: number]
}>()

// 响应式状态
const isExpanded = ref(props.defaultExpanded)

// 计算属性
const stepClass = computed(() => [
  'thinking-step-container',
  `level-${props.level}`,
  {
    'expanded': isExpanded.value,
    'compact': props.compactMode,
    'has-error': props.step.error,
    'animate': props.showAnimations
  }
])

const iconClass = computed(() => [
  'step-icon-container',
  `type-${props.step.type || 'reasoning'}`,
  {
    'has-error': props.step.error
  }
])

const confidenceClass = computed(() => {
  if (!props.step.confidence) return ''
  
  const confidence = props.step.confidence * 100
  if (confidence >= 80) return 'confidence-high'
  if (confidence >= 60) return 'confidence-medium' 
  return 'confidence-low'
})

const stepIcon = computed(() => {
  if (props.step.error) return AlertCircle
  
  switch (props.step.type) {
    case 'analysis': return Brain
    case 'search': return Search
    case 'reasoning': return Lightbulb
    case 'decision': return Target
    case 'validation': return CheckCircle
    case 'action': return CheckCircle
    default: return Brain
  }
})

// 方法
const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
  emit('expand-change', isExpanded.value, props.stepNumber)
  emit('step-click', props.step, props.stepNumber)
}

const formatContent = (content: string): string => {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-xs">$1</code>')
    .replace(/\n/g, '<br>')
}

const formatValue = (value: any): string => {
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2).slice(0, 100) + (JSON.stringify(value).length > 100 ? '...' : '')
  }
  return String(value).slice(0, 100) + (String(value).length > 100 ? '...' : '')
}

const formatDuration = (duration: number): string => {
  if (duration < 1000) {
    return `${Math.round(duration)}ms`
  } else if (duration < 60000) {
    return `${(duration / 1000).toFixed(1)}s`
  } else {
    return `${Math.floor(duration / 60000)}m ${Math.floor((duration % 60000) / 1000)}s`
  }
}

// 暴露方法
defineExpose({
  expand: () => { isExpanded.value = true },
  collapse: () => { isExpanded.value = false },
  toggle: toggleExpanded,
  isExpanded: computed(() => isExpanded.value)
})
</script>

<style scoped>
.thinking-step-container {
  @apply border rounded-lg transition-all duration-200;
  border-color: hsl(var(--border));
}

.thinking-step-container.expanded {
  @apply shadow-sm;
}

.thinking-step-container.has-error {
  @apply border-destructive/30 bg-destructive/5;
}

.thinking-step-container.compact .step-header {
  @apply py-2;
}

.step-header {
  @apply p-3 hover:bg-muted/50 transition-colors duration-200;
}

.step-icon-container {
  @apply w-8 h-8 rounded-full flex items-center justify-center;
}

.step-icon-container.type-analysis {
  @apply bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400;
}

.step-icon-container.type-search {
  @apply bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400;
}

.step-icon-container.type-reasoning {
  @apply bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400;
}

.step-icon-container.type-decision {
  @apply bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400;
}

.step-icon-container.type-validation {
  @apply bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400;
}

.step-icon-container.type-action {
  @apply bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400;
}

.step-icon-container.has-error {
  @apply bg-destructive/10 text-destructive;
}

.confidence-high {
  @apply bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400;
}

.confidence-medium {
  @apply bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400;
}

.confidence-low {
  @apply bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400;
}

.confidence-badge {
  @apply px-2 py-1 rounded-full text-xs font-medium;
}

.duration-badge {
  @apply px-2 py-1 bg-muted rounded-full;
}

.step-content {
  @apply border-t border-border;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 动画效果 */
.thinking-step-container.animate {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 层级缩进 */
.level-1 {
  @apply ml-4;
}

.level-2 {
  @apply ml-8;
}

.level-3 {
  @apply ml-12;
}

/* 响应式调整 */
@media (max-width: 640px) {
  .step-header {
    @apply p-2;
  }
  
  .step-content {
    @apply px-2;
  }
  
  .level-1, .level-2, .level-3 {
    @apply ml-2;
  }
}
</style>