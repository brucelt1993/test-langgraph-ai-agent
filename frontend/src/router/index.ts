import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: {
      title: 'AI助手',
      requiresAuth: false
    }
  },
  {
    path: '/test-css',
    name: 'test-css',
    component: () => import('@/views/TestCss.vue'),
    meta: {
      title: 'CSS样式测试',
      requiresAuth: false
    }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: {
      title: '登录',
      requiresAuth: false,
      hideForAuth: true // 已登录用户不显示
    }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: {
      title: '注册',
      requiresAuth: false,
      hideForAuth: true
    }
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('@/views/chat/ChatListView.vue'),
    meta: {
      title: '聊天',
      requiresAuth: true
    }
  },
  {
    path: '/chat/:sessionId',
    name: 'chatSession',
    component: () => import('@/views/chat/ChatSessionView.vue'),
    meta: {
      title: '聊天会话',
      requiresAuth: true
    }
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/user/ProfileView.vue'),
    meta: {
      title: '个人资料',
      requiresAuth: true
    }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/user/SettingsView.vue'),
    meta: {
      title: '设置',
      requiresAuth: true
    }
  },
  // 404页面
  {
    path: '/:pathMatch(.*)*',
    name: 'notFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: {
      title: '页面不存在'
    }
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 全局路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - AI助手`
  }

  // 检查认证状态
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()

  // 等待认证状态初始化完成（如果需要）
  if (authStore.token && !authStore.user) {
    try {
      await authStore.initialize()
    } catch (error) {
      console.error('路由守卫：认证状态初始化失败', error)
    }
  }

  // 需要认证的路由
  if (to.meta?.requiresAuth) {
    if (!authStore.isAuthenticated) {
      // 保存原始路由，登录后跳转回来
      next({ 
        name: 'login', 
        query: { redirect: to.fullPath }
      })
      return
    }
  }

  // 已登录用户访问登录/注册页面，重定向到首页
  if (to.meta?.hideForAuth && authStore.isAuthenticated) {
    next({ name: 'home' })
    return
  }

  next()
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
})

export default router