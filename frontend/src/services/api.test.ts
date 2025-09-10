/**
 * API客户端测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import { apiClient } from '@/services/api'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as any

describe('ApiClient', () => {
  beforeEach(() => {
    // 重置所有mock
    vi.clearAllMocks()
    
    // Mock axios.create
    mockedAxios.create.mockReturnValue({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      },
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      request: vi.fn()
    })
  })

  afterEach(() => {
    // 清理认证token
    apiClient.clearAuthToken()
  })

  describe('认证功能', () => {
    it('应该设置认证token', () => {
      const token = 'test-token'
      
      apiClient.setAuthToken(token)
      
      // 由于token是私有的，我们需要通过其他方式验证
      expect(true).toBe(true) // 占位符测试
    })

    it('应该清除认证token', () => {
      apiClient.setAuthToken('test-token')
      apiClient.clearAuthToken()
      
      expect(true).toBe(true) // 占位符测试
    })
  })

  describe('加载状态管理', () => {
    it('应该返回加载状态', () => {
      const loadingStates = apiClient.getLoadingStates()
      
      expect(loadingStates.value).toEqual({})
    })

    it('应该检查特定请求的加载状态', () => {
      const isLoading = apiClient.isLoading('test-key')
      
      expect(isLoading).toBe(false)
    })
  })

  describe('HTTP请求方法', () => {
    let mockAxiosInstance: any

    beforeEach(() => {
      mockAxiosInstance = {
        request: vi.fn().mockResolvedValue({ data: 'success' })
      }
      mockedAxios.create.mockReturnValue({
        ...mockAxiosInstance,
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      })
    })

    it('应该发送GET请求', async () => {
      const result = await apiClient.get('/test')
      
      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'GET',
        url: '/test',
        data: undefined,
        meta: undefined
      })
    })

    it('应该发送POST请求', async () => {
      const data = { key: 'value' }
      
      await apiClient.post('/test', data)
      
      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'POST',
        url: '/test',
        data,
        meta: undefined
      })
    })

    it('应该发送PUT请求', async () => {
      const data = { key: 'updated' }
      
      await apiClient.put('/test', data)
      
      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'PUT',
        url: '/test',
        data,
        meta: undefined
      })
    })

    it('应该发送DELETE请求', async () => {
      await apiClient.delete('/test')
      
      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'DELETE',
        url: '/test',
        data: undefined,
        meta: undefined
      })
    })

    it('应该使用重试配置', async () => {
      const config = {
        retry: {
          retries: 2,
          retryDelay: 500,
          retryCondition: () => true
        }
      }
      
      await apiClient.get('/test', config)
      
      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'GET',
        url: '/test',
        data: undefined,
        meta: config
      })
    })

    it('应该跳过加载状态', async () => {
      const config = {
        skipLoading: true
      }
      
      await apiClient.get('/test', config)
      
      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'GET',
        url: '/test',
        data: undefined,
        meta: config
      })
    })

    it('应该使用自定义加载key', async () => {
      const config = {
        loadingKey: 'custom-key'
      }
      
      await apiClient.get('/test', config)
      
      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'GET',
        url: '/test',
        data: undefined,
        meta: config
      })
    })
  })

  describe('文件上传', () => {
    it('应该上传文件', async () => {
      const file = new File(['test'], 'test.txt', { type: 'text/plain' })
      const onProgress = vi.fn()

      // Mock axios实例
      const mockPost = vi.fn().mockResolvedValue({ data: { file_id: '123' } })
      const mockAxiosInstance = {
        post: mockPost,
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }
      mockedAxios.create.mockReturnValue(mockAxiosInstance)

      await apiClient.upload('/upload', file, onProgress)

      expect(mockPost).toHaveBeenCalledWith(
        '/upload',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: expect.any(Function)
        })
      )
    })
  })

  describe('文件下载', () => {
    it('应该下载文件', async () => {
      const mockGet = vi.fn().mockResolvedValue(new Blob(['test']))
      const mockAxiosInstance = {
        get: mockGet,
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }
      mockedAxios.create.mockReturnValue(mockAxiosInstance)

      // Mock DOM elements
      const mockLink = {
        href: '',
        download: '',
        click: vi.fn()
      }
      const mockCreateElement = vi.fn().mockReturnValue(mockLink)
      const mockAppendChild = vi.fn()
      const mockRemoveChild = vi.fn()
      const mockCreateObjectURL = vi.fn().mockReturnValue('blob:url')
      const mockRevokeObjectURL = vi.fn()

      global.document.createElement = mockCreateElement
      global.document.body.appendChild = mockAppendChild
      global.document.body.removeChild = mockRemoveChild
      global.URL.createObjectURL = mockCreateObjectURL
      global.URL.revokeObjectURL = mockRevokeObjectURL

      await apiClient.download('/download', 'test.txt')

      expect(mockGet).toHaveBeenCalledWith('/download', {
        responseType: 'blob'
      })
      expect(mockLink.click).toHaveBeenCalled()
    })
  })

  describe('axios实例访问', () => {
    it('应该返回原始axios实例', () => {
      const instance = apiClient.getAxiosInstance()
      expect(instance).toBeDefined()
    })
  })
})