<template>
  <div class="fixed top-4 right-4 z-50 space-y-2">
    <TransitionGroup
      name="notification"
      tag="div"
      class="space-y-2"
    >
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="notification-item"
        :class="getNotificationClass(notification.type)"
        role="alert"
        aria-live="polite"
      >
        <div class="flex items-start">
          <!-- 图标 -->
          <div class="flex-shrink-0 mr-3">
            <component 
              :is="getIcon(notification.type)"
              :class="getIconClass(notification.type)"
              class="h-5 w-5" 
            />
          </div>

          <!-- 内容 -->
          <div class="flex-1 min-w-0">
            <h4 
              v-if="notification.title" 
              class="text-sm font-medium mb-1"
              :class="getTitleClass(notification.type)"
            >
              {{ notification.title }}
            </h4>
            <p 
              class="text-sm"
              :class="getMessageClass(notification.type)"
            >
              {{ notification.message }}
            </p>
          </div>

          <!-- 关闭按钮 -->
          <button
            v-if="notification.closable"
            @click="removeNotification(notification.id)"
            class="ml-2 flex-shrink-0 rounded-md text-sm font-medium hover:opacity-75 focus:outline-none focus:ring-2 focus:ring-offset-2"
            :class="getCloseButtonClass(notification.type)"
          >
            <span class="sr-only">关闭</span>
            <XMarkIcon class="h-4 w-4" />
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon, InformationCircleIcon, XMarkIcon } from 'lucide-vue-next'
import { useNotification } from '@/composables/useNotification'

const { notifications, removeNotification } = useNotification()

// 获取图标组件
const getIcon = (type: string) => {
  switch (type) {
    case 'success':
      return CheckCircleIcon
    case 'error':
      return XCircleIcon
    case 'warning':
      return ExclamationTriangleIcon
    case 'info':
    default:
      return InformationCircleIcon
  }
}

// 获取通知样式类
const getNotificationClass = (type: string) => {
  const baseClass = 'max-w-sm w-full bg-white border rounded-lg shadow-lg p-4'
  
  switch (type) {
    case 'success':
      return `${baseClass} border-green-200`
    case 'error':
      return `${baseClass} border-red-200`
    case 'warning':
      return `${baseClass} border-yellow-200`
    case 'info':
    default:
      return `${baseClass} border-blue-200`
  }
}

// 获取图标样式类
const getIconClass = (type: string) => {
  switch (type) {
    case 'success':
      return 'text-green-500'
    case 'error':
      return 'text-red-500'
    case 'warning':
      return 'text-yellow-500'
    case 'info':
    default:
      return 'text-blue-500'
  }
}

// 获取标题样式类
const getTitleClass = (type: string) => {
  switch (type) {
    case 'success':
      return 'text-green-900'
    case 'error':
      return 'text-red-900'
    case 'warning':
      return 'text-yellow-900'
    case 'info':
    default:
      return 'text-blue-900'
  }
}

// 获取消息样式类
const getMessageClass = (type: string) => {
  switch (type) {
    case 'success':
      return 'text-green-700'
    case 'error':
      return 'text-red-700'
    case 'warning':
      return 'text-yellow-700'
    case 'info':
    default:
      return 'text-blue-700'
  }
}

// 获取关闭按钮样式类
const getCloseButtonClass = (type: string) => {
  switch (type) {
    case 'success':
      return 'text-green-400 hover:text-green-600 focus:ring-green-500'
    case 'error':
      return 'text-red-400 hover:text-red-600 focus:ring-red-500'
    case 'warning':
      return 'text-yellow-400 hover:text-yellow-600 focus:ring-yellow-500'
    case 'info':
    default:
      return 'text-blue-400 hover:text-blue-600 focus:ring-blue-500'
  }
}
</script>

<style scoped>
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.notification-move {
  transition: transform 0.3s ease;
}

/* 确保通知项具有适当的定位 */
.notification-item {
  position: relative;
}
</style>