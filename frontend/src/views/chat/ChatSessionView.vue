<template>
  <AuthGuard>
    <ChatView />
  </AuthGuard>
</template>

<script setup lang="ts">
import AuthGuard from '@/components/AuthGuard.vue'
import ChatView from './ChatView.vue'

// 这个组件主要是为了处理路由参数中的sessionId
// 实际的聊天逻辑在ChatView中处理
</script>