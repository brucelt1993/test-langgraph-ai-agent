/**
 * 测试工具函数
 */

import { describe, it, expect, vi } from 'vitest'
import { createApp } from 'vue'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import type { Component } from 'vue'

/**
 * 创建测试应用
 */
export function createTestApp() {
  const app = createApp({})
  const pinia = createPinia()
  app.use(pinia)
  return { app, pinia }
}

/**
 * 挂载组件用于测试
 */
export function mountComponent(component: Component, options?: any) {
  const { pinia } = createTestApp()
  
  return mount(component, {
    global: {
      plugins: [pinia],
      mocks: {
        $t: (key: string) => key,
        $router: {
          push: vi.fn(),
          replace: vi.fn(),
        },
        $route: {
          path: '/',
          params: {},
          query: {},
        },
      },
      stubs: {
        'router-link': true,
        'router-view': true,
      },
    },
    ...options,
  })
}

/**
 * 模拟API响应
 */
export function mockApiResponse<T>(data: T, delay = 0) {
  return new Promise<T>((resolve) => {
    setTimeout(() => resolve(data), delay)
  })
}

/**
 * 模拟API错误
 */
export function mockApiError(message: string, status = 400) {
  const error = new Error(message) as any
  error.response = {
    status,
    data: { message },
  }
  return Promise.reject(error)
}

/**
 * 等待DOM更新
 */
export async function nextTick() {
  await new Promise(resolve => setTimeout(resolve, 0))
}

/**
 * 创建模拟用户数据
 */
export function createMockUser(overrides = {}) {
  return {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    full_name: 'Test User',
    is_active: true,
    is_verified: true,
    role: {
      id: '1',
      name: 'user',
      display_name: '普通用户',
      permissions: ['chat:create', 'chat:read'],
    },
    created_at: '2024-01-01T00:00:00Z',
    last_login_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

/**
 * 创建模拟聊天会话数据
 */
export function createMockChatSession(overrides = {}) {
  return {
    id: '1',
    user_id: '1',
    title: '测试会话',
    agent_name: 'weather_agent',
    context: {},
    is_active: true,
    message_count: 0,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

/**
 * 创建模拟消息数据
 */
export function createMockMessage(overrides = {}) {
  return {
    id: '1',
    session_id: '1',
    type: 'user',
    content: '测试消息',
    metadata: {},
    thinking_steps: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

/**
 * 模拟EventSource
 */
export class MockEventSource {
  onopen = vi.fn()
  onmessage = vi.fn()
  onerror = vi.fn()
  onclose = vi.fn()
  
  readyState = 1
  url: string
  
  static readonly CONNECTING = 0
  static readonly OPEN = 1
  static readonly CLOSED = 2
  
  constructor(url: string) {
    this.url = url
  }
  
  addEventListener = vi.fn()
  removeEventListener = vi.fn()
  close = vi.fn()
  
  // 测试辅助方法
  simulateOpen() {
    this.readyState = MockEventSource.OPEN
    this.onopen?.({ type: 'open' } as Event)
  }
  
  simulateMessage(data: string) {
    this.onmessage?.({ 
      data, 
      type: 'message' 
    } as MessageEvent)
  }
  
  simulateError() {
    this.readyState = MockEventSource.CLOSED
    this.onerror?.({ type: 'error' } as Event)
  }
  
  simulateClose() {
    this.readyState = MockEventSource.CLOSED
    this.onclose?.({ type: 'close' } as Event)
  }
}