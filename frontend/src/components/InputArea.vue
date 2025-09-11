<template>
  <div class="border-t border-border bg-background p-4">
    <!-- 输入区域主体 -->
    <div class="max-w-6xl mx-auto">  <!-- 增加消息框最大宽度 -->
      <!-- 快捷操作栏 -->
      <div 
        v-if="showQuickActions"
        class="flex flex-wrap gap-2 mb-3"
      >
        <button
          v-for="action in quickActions"
          :key="action.text"
          class="btn btn-outline btn-sm"
          @click="insertQuickAction(action)"
          :disabled="disabled"
        >
          <component :is="action.icon" class="w-4 h-4 mr-1" />
          {{ action.text }}
        </button>
      </div>

      <!-- 主输入区域 -->
      <div class="relative">
        <!-- 文件拖拽区域 -->
        <div
          v-if="isDragOver"
          class="absolute inset-0 bg-primary/10 border-2 border-dashed border-primary rounded-lg flex items-center justify-center z-10"
        >
          <div class="text-center">
            <svg class="w-12 h-12 text-primary mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="text-primary font-medium">拖拽文件到这里上传</p>
            <p class="text-sm text-muted-foreground">支持图片、文档等格式</p>
          </div>
        </div>

        <!-- 输入框容器 -->
        <div 
          class="relative flex items-end space-x-2"
          @dragover.prevent="handleDragOver"
          @dragleave.prevent="handleDragLeave"
          @drop.prevent="handleDrop"
        >
          <!-- 附件展示 -->
          <div 
            v-if="attachments.length > 0"
            class="absolute bottom-full left-0 right-12 mb-2"
          >
            <div class="flex flex-wrap gap-2 p-2 bg-muted rounded-lg">
              <div
                v-for="(attachment, index) in attachments"
                :key="index"
                class="flex items-center space-x-2 bg-background rounded px-2 py-1"
              >
                <component 
                  :is="getAttachmentIcon(attachment.type)" 
                  class="w-4 h-4 text-muted-foreground" 
                />
                <span class="text-sm truncate max-w-32">
                  {{ attachment.name }}
                </span>
                <button
                  class="text-muted-foreground hover:text-destructive"
                  @click="removeAttachment(index)"
                >
                  <X class="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>

          <!-- 文本输入区域 -->
          <div class="flex-1 relative">
            <textarea
              ref="textareaRef"
              v-model="inputText"
              :placeholder="placeholder"
              class="input min-h-[44px] max-h-32 resize-none pr-10"
              :disabled="disabled"
              @keydown="handleKeyDown"
              @paste="handlePaste"
              @input="handleInput"
              rows="1"
            />
            
            <!-- 字符计数 -->
            <div 
              v-if="showCharCount && maxLength"
              class="absolute bottom-2 right-2 text-xs"
              :class="inputText.length > maxLength ? 'text-destructive' : 'text-muted-foreground'"
            >
              {{ inputText.length }}/{{ maxLength }}
            </div>
          </div>

          <!-- 操作按钮组 -->
          <div class="flex items-center space-x-1">
            <!-- 附件上传按钮 -->
            <button
              v-if="allowAttachments"
              class="btn btn-ghost btn-sm w-10 h-10 rounded-full"
              @click="triggerFileUpload"
              :disabled="disabled"
              title="上传附件"
            >
              <Paperclip class="w-4 h-4" />
            </button>

            <!-- 语音输入按钮 -->
            <button
              v-if="allowVoiceInput"
              class="btn btn-ghost btn-sm w-10 h-10 rounded-full"
              :class="{ 'bg-destructive text-destructive-foreground': isRecording }"
              @click="toggleVoiceInput"
              :disabled="disabled"
              :title="isRecording ? '停止录音' : '语音输入'"
            >
              <component :is="isRecording ? MicOff : Mic" class="w-4 h-4" />
            </button>

            <!-- 表情按钮 -->
            <button
              v-if="allowEmoji"
              class="btn btn-ghost btn-sm w-10 h-10 rounded-full"
              @click="toggleEmojiPicker"
              :disabled="disabled"
              title="插入表情"
            >
              <Smile class="w-4 h-4" />
            </button>

            <!-- 发送按钮 -->
            <button
              class="btn btn-primary btn-sm w-10 h-10 rounded-full"
              :disabled="!canSend"
              @click="handleSend"
              title="发送消息 (Ctrl+Enter)"
            >
              <component 
                :is="isSending ? LoaderIcon : SendIcon" 
                class="w-4 h-4"
                :class="{ 'animate-spin': isSending }"
              />
            </button>
          </div>
        </div>

        <!-- 隐藏的文件输入 -->
        <input
          ref="fileInputRef"
          type="file"
          multiple
          class="hidden"
          :accept="acceptedFileTypes"
          @change="handleFileSelect"
        />

        <!-- 表情选择器 -->
        <div
          v-if="showEmojiPicker"
          class="absolute bottom-full right-0 mb-2 bg-background border rounded-lg shadow-lg p-3 z-20"
        >
          <div class="grid grid-cols-8 gap-2 max-w-xs">
            <button
              v-for="emoji in commonEmojis"
              :key="emoji"
              class="hover:bg-accent rounded p-1 text-lg"
              @click="insertEmoji(emoji)"
            >
              {{ emoji }}
            </button>
          </div>
        </div>
      </div>

      <!-- 快捷键提示 -->
      <div 
        v-if="showShortcuts"
        class="flex justify-between items-center text-xs text-muted-foreground mt-2"
      >
        <div class="flex space-x-4">
          <span>Ctrl+Enter 发送</span>
          <span>Shift+Enter 换行</span>
          <span v-if="allowAttachments">Ctrl+U 上传文件</span>
        </div>
        <div v-if="wordCount > 0">
          {{ wordCount }} 字符
        </div>
      </div>

      <!-- 建议问题 -->
      <div
        v-if="showSuggestions && suggestions.length > 0"
        class="mt-3"
      >
        <div class="text-sm text-muted-foreground mb-2">建议问题:</div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="suggestion in suggestions"
            :key="suggestion"
            class="btn btn-outline btn-sm"
            @click="selectSuggestion(suggestion)"
            :disabled="disabled"
          >
            {{ suggestion }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { 
  Paperclip, 
  Mic, 
  MicOff, 
  Smile, 
  Send as SendIcon, 
  Loader as LoaderIcon,
  X,
  FileText,
  Image,
  File
} from 'lucide-vue-next'

// Props
interface QuickAction {
  text: string
  content: string
  icon: any
}

interface Attachment {
  name: string
  type: string
  size: number
  file: File
}

interface Props {
  placeholder?: string
  disabled?: boolean
  isSending?: boolean
  maxLength?: number
  allowAttachments?: boolean
  allowVoiceInput?: boolean
  allowEmoji?: boolean
  showQuickActions?: boolean
  showShortcuts?: boolean
  showSuggestions?: boolean
  showCharCount?: boolean
  acceptedFileTypes?: string
  suggestions?: string[]
  quickActions?: QuickAction[]
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '输入您的问题...',
  disabled: false,
  isSending: false,
  maxLength: 2000,
  allowAttachments: true,
  allowVoiceInput: false,
  allowEmoji: true,
  showQuickActions: false,
  showShortcuts: true,
  showSuggestions: true,
  showCharCount: true,
  acceptedFileTypes: 'image/*,application/pdf,.doc,.docx,.txt',
  suggestions: () => [
    '你好，请介绍一下自己',
    '今天天气怎么样？',
    '帮我写一份工作总结',
    '解释一下人工智能的工作原理'
  ],
  quickActions: () => []
})

// Emits
const emit = defineEmits<{
  send: [{ text: string; attachments: Attachment[] }]
  input: [text: string]
  attachmentsChange: [attachments: Attachment[]]
}>()

// 响应式引用
const textareaRef = ref<HTMLTextAreaElement>()
const fileInputRef = ref<HTMLInputElement>()
const inputText = ref('')
const attachments = ref<Attachment[]>([])
const isDragOver = ref(false)
const isRecording = ref(false)
const showEmojiPicker = ref(false)

// 计算属性
const canSend = computed(() => {
  return !props.disabled && 
         !props.isSending && 
         (inputText.value.trim().length > 0 || attachments.value.length > 0) &&
         inputText.value.length <= props.maxLength
})

const wordCount = computed(() => inputText.value.length)

// 常用表情
const commonEmojis = [
  '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣',
  '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰',
  '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜',
  '🤪', '🤨', '🧐', '🤓', '😎', '🤩', '🥳', '😏',
  '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣',
  '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠',
  '👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘', '🤙',
  '💪', '👏', '🙌', '👐', '🤝', '🙏', '❤️', '💕'
]

// 自动调整文本框高度
const adjustTextareaHeight = () => {
  const textarea = textareaRef.value
  if (!textarea) return

  textarea.style.height = 'auto'
  const newHeight = Math.min(textarea.scrollHeight, 128) // 最大高度32*4
  textarea.style.height = `${newHeight}px`
}

// 处理输入
const handleInput = () => {
  adjustTextareaHeight()
  emit('input', inputText.value)
}

// 处理键盘事件
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    if (event.ctrlKey || event.metaKey) {
      // Ctrl+Enter 发送
      event.preventDefault()
      handleSend()
    } else if (!event.shiftKey) {
      // Enter 发送 (如果不是Shift+Enter换行)
      event.preventDefault()
      handleSend()
    }
  } else if (event.key === 'u' && (event.ctrlKey || event.metaKey)) {
    // Ctrl+U 上传文件
    event.preventDefault()
    triggerFileUpload()
  }
}

// 处理粘贴事件
const handlePaste = (event: ClipboardEvent) => {
  const items = event.clipboardData?.items
  if (!items || !props.allowAttachments) return

  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.kind === 'file') {
      const file = item.getAsFile()
      if (file) {
        addAttachment(file)
      }
    }
  }
}

// 处理发送
const handleSend = () => {
  if (!canSend.value) return

  const text = inputText.value.trim()
  if (!text && attachments.value.length === 0) return

  emit('send', {
    text,
    attachments: [...attachments.value]
  })

  // 清空输入
  inputText.value = ''
  attachments.value = []
  adjustTextareaHeight()
  
  // 关闭表情选择器
  showEmojiPicker.value = false
}

// 触发文件上传
const triggerFileUpload = () => {
  fileInputRef.value?.click()
}

// 处理文件选择
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files) return

  Array.from(files).forEach(file => {
    addAttachment(file)
  })

  // 重置input
  target.value = ''
}

// 添加附件
const addAttachment = (file: File) => {
  if (attachments.value.length >= 5) { // 最多5个附件
    alert('最多只能上传5个文件')
    return
  }

  if (file.size > 10 * 1024 * 1024) { // 10MB限制
    alert('文件大小不能超过10MB')
    return
  }

  const attachment: Attachment = {
    name: file.name,
    type: file.type,
    size: file.size,
    file
  }

  attachments.value.push(attachment)
  emit('attachmentsChange', attachments.value)
}

// 移除附件
const removeAttachment = (index: number) => {
  attachments.value.splice(index, 1)
  emit('attachmentsChange', attachments.value)
}

// 获取附件图标
const getAttachmentIcon = (type: string) => {
  if (type.startsWith('image/')) {
    return Image
  } else if (type.includes('text') || type.includes('document')) {
    return FileText
  } else {
    return File
  }
}

// 处理拖拽
const handleDragOver = (event: DragEvent) => {
  if (!props.allowAttachments) return
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (event: DragEvent) => {
  isDragOver.value = false
  if (!props.allowAttachments) return

  const files = event.dataTransfer?.files
  if (!files) return

  Array.from(files).forEach(file => {
    addAttachment(file)
  })
}

// 语音输入相关
const toggleVoiceInput = () => {
  if (!props.allowVoiceInput) return
  
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

const startRecording = () => {
  // TODO: 实现语音录制功能
  isRecording.value = true
  console.log('开始录音')
}

const stopRecording = () => {
  // TODO: 实现语音录制停止和转文字
  isRecording.value = false
  console.log('停止录音')
}

// 表情相关
const toggleEmojiPicker = () => {
  showEmojiPicker.value = !showEmojiPicker.value
}

const insertEmoji = (emoji: string) => {
  const textarea = textareaRef.value
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const text = inputText.value

  inputText.value = text.slice(0, start) + emoji + text.slice(end)
  
  nextTick(() => {
    textarea.setSelectionRange(start + emoji.length, start + emoji.length)
    textarea.focus()
    adjustTextareaHeight()
  })
}

// 快捷操作
const insertQuickAction = (action: QuickAction) => {
  inputText.value = action.content
  adjustTextareaHeight()
  textareaRef.value?.focus()
}

// 建议问题
const selectSuggestion = (suggestion: string) => {
  inputText.value = suggestion
  adjustTextareaHeight()
  textareaRef.value?.focus()
}

// 监听输入文本变化
watch(inputText, () => {
  nextTick(adjustTextareaHeight)
})

// 点击外部关闭表情选择器
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement
  if (!target.closest('.emoji-picker') && !target.closest('button[title="插入表情"]')) {
    showEmojiPicker.value = false
  }
}

// 组件挂载时添加事件监听
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

// 组件卸载时移除事件监听
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* 文本框样式 */
.input:focus {
  @apply ring-2 ring-primary ring-offset-2;
}

/* 拖拽区域样式 */
.drag-over {
  @apply bg-primary/5 border-primary/50;
}

/* 附件样式 */
.attachment-item {
  @apply flex items-center space-x-2 bg-muted rounded px-2 py-1;
}

/* 表情选择器样式 */
.emoji-picker {
  @apply absolute bottom-full right-0 mb-2 bg-background border rounded-lg shadow-lg p-3 z-20;
}

/* 动画效果 */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 按钮悬停效果 */
.btn:hover {
  @apply transition-colors duration-200;
}

/* 响应式调整 */
@media (max-width: 640px) {
  .space-x-1 > * + * {
    @apply ml-0.5;
  }
  
  .btn-sm {
    @apply w-8 h-8;
  }
}
</style>