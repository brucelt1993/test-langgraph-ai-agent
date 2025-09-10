<template>
  <span class="typewriter-text">
    <span v-html="displayText"></span>
    <span 
      v-if="showCursor && isCurrentlyTyping" 
      class="cursor"
      :class="cursorClass"
    >|</span>
  </span>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

export interface TypewriterTextProps {
  text: string
  speed?: number
  delay?: number
  showCursor?: boolean
  cursorClass?: string
  isStreaming?: boolean
  pauseOnComplete?: number
  enableMarkdown?: boolean
}

const props = withDefaults(defineProps<TypewriterTextProps>(), {
  speed: 50,
  delay: 0,
  showCursor: true,
  cursorClass: 'animate-pulse',
  isStreaming: false,
  pauseOnComplete: 500,
  enableMarkdown: true
})

const emit = defineEmits<{
  'typing-start': []
  'typing-complete': []
  'character-typed': [char: string, index: number]
}>()

// 响应式状态
const displayText = ref('')
const currentIndex = ref(0)
const isCurrentlyTyping = ref(false)
const typingTimer = ref<number | null>(null)
const completionTimer = ref<number | null>(null)

// 计算属性
const shouldType = computed(() => {
  return props.text.length > currentIndex.value
})

// 文本处理方法
const escapeHtml = (text: string): string => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

const processMarkdown = (text: string): string => {
  if (!props.enableMarkdown) {
    return escapeHtml(text)
  }

  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-sm font-mono">$1</code>')
    .replace(/\n/g, '<br>')
}

// 打字机动画方法
const typeCharacter = () => {
  if (currentIndex.value < props.text.length) {
    const char = props.text[currentIndex.value]
    displayText.value = processMarkdown(props.text.substring(0, currentIndex.value + 1))
    
    emit('character-typed', char, currentIndex.value)
    currentIndex.value++
    
    // 根据字符类型调整速度
    let delay = props.speed
    if (char === '.' || char === '!' || char === '?') {
      delay *= 3 // 句号等停顿更长
    } else if (char === ',' || char === ';') {
      delay *= 2 // 逗号等停顿较长
    } else if (char === ' ') {
      delay *= 0.5 // 空格快一些
    }
    
    typingTimer.value = window.setTimeout(typeCharacter, delay)
  } else {
    // 打字完成
    isCurrentlyTyping.value = false
    
    // 延迟一段时间后触发完成事件
    if (props.pauseOnComplete > 0) {
      completionTimer.value = window.setTimeout(() => {
        emit('typing-complete')
      }, props.pauseOnComplete)
    } else {
      emit('typing-complete')
    }
  }
}

const startTyping = () => {
  if (isCurrentlyTyping.value || props.text.length === 0) return
  
  stopTyping()
  isCurrentlyTyping.value = true
  emit('typing-start')
  
  if (props.delay > 0) {
    setTimeout(() => {
      typeCharacter()
    }, props.delay)
  } else {
    typeCharacter()
  }
}

const stopTyping = () => {
  if (typingTimer.value) {
    clearTimeout(typingTimer.value)
    typingTimer.value = null
  }
  
  if (completionTimer.value) {
    clearTimeout(completionTimer.value)
    completionTimer.value = null
  }
  
  isCurrentlyTyping.value = false
}

const resetTyping = () => {
  stopTyping()
  currentIndex.value = 0
  displayText.value = ''
}

const completeTyping = () => {
  stopTyping()
  currentIndex.value = props.text.length
  displayText.value = processMarkdown(props.text)
  isCurrentlyTyping.value = false
  emit('typing-complete')
}

// 监听文本变化
watch(() => props.text, (newText, oldText) => {
  if (newText !== oldText) {
    if (props.isStreaming) {
      // 流式模式：继续从当前位置打字
      if (newText.length > currentIndex.value) {
        if (!isCurrentlyTyping.value) {
          startTyping()
        }
      }
    } else {
      // 非流式模式：重新开始打字
      resetTyping()
      nextTick(() => {
        if (newText) {
          startTyping()
        }
      })
    }
  }
})

// 监听流式状态
watch(() => props.isStreaming, (isStreaming) => {
  if (!isStreaming && shouldType.value) {
    // 流式结束，继续完成剩余打字
    if (!isCurrentlyTyping.value) {
      startTyping()
    }
  }
})

// 生命周期
onMounted(() => {
  if (props.text) {
    startTyping()
  }
})

onUnmounted(() => {
  stopTyping()
})

// 暴露方法
defineExpose({
  start: startTyping,
  stop: stopTyping,
  reset: resetTyping,
  complete: completeTyping,
  isTyping: computed(() => isCurrentlyTyping.value)
})
</script>

<style scoped>
.typewriter-text {
  display: inline-block;
}

.cursor {
  color: currentColor;
  font-weight: bold;
}

.animate-pulse {
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 确保代码块样式正确 */
:deep(code) {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
}

/* 确保换行显示正确 */
:deep(br) {
  line-height: 1.5;
}

/* 强调文本样式 */
:deep(strong) {
  font-weight: 600;
}

:deep(em) {
  font-style: italic;
}
</style>