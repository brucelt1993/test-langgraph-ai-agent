/**
 * 通知系统 Composable
 * 提供统一的消息通知功能
 */

import { ref } from 'vue'

export interface NotificationOptions {
  duration?: number
  closable?: boolean
  type?: 'success' | 'error' | 'warning' | 'info'
}

export interface Notification {
  id: string
  title?: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration: number
  closable: boolean
  createdAt: Date
}

const notifications = ref<Notification[]>([])
const notificationId = ref(0)

export function useNotification() {
  // 显示通知
  const showNotification = (
    message: string,
    type: 'success' | 'error' | 'warning' | 'info' = 'info',
    title?: string,
    options: NotificationOptions = {}
  ) => {
    const notification: Notification = {
      id: `notification-${++notificationId.value}`,
      title,
      message,
      type,
      duration: options.duration ?? (type === 'error' ? 8000 : 4000),
      closable: options.closable ?? true,
      createdAt: new Date()
    }

    notifications.value.push(notification)

    // 自动关闭
    if (notification.duration > 0) {
      setTimeout(() => {
        removeNotification(notification.id)
      }, notification.duration)
    }

    return notification.id
  }

  // 移除通知
  const removeNotification = (id: string) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  // 清除所有通知
  const clearNotifications = () => {
    notifications.value = []
  }

  // 便捷方法
  const showSuccess = (message: string, title?: string, options?: NotificationOptions) => {
    return showNotification(message, 'success', title, options)
  }

  const showError = (message: string, title?: string, options?: NotificationOptions) => {
    return showNotification(message, 'error', title, options)
  }

  const showWarning = (message: string, title?: string, options?: NotificationOptions) => {
    return showNotification(message, 'warning', title, options)
  }

  const showInfo = (message: string, title?: string, options?: NotificationOptions) => {
    return showNotification(message, 'info', title, options)
  }

  return {
    notifications,
    showNotification,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    removeNotification,
    clearNotifications
  }
}