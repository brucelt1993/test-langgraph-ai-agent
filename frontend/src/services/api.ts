import axios, { 
  type AxiosInstance, 
  type AxiosResponse, 
  type AxiosError,
  type InternalAxiosRequestConfig 
} from 'axios'
import { ref, type Ref } from 'vue'
import { config } from '@/config/env'

// API响应类型
interface ApiResponse<T = any> {
  data: T
  message?: string
  success?: boolean
}

// API错误类型
interface ApiError {
  message: string
  detail?: string
  code?: string
}

// 重试配置接口
interface RetryConfig {
  retries: number
  retryDelay: number
  retryCondition?: (error: AxiosError) => boolean
}

// 加载状态管理
interface LoadingState {
  [key: string]: boolean
}

// 请求配置扩展
interface ApiRequestConfig {
  retry?: RetryConfig
  skipLoading?: boolean
  loadingKey?: string
  params?: Record<string, any>
}

class ApiClient {
  private client: AxiosInstance
  private authToken: string | null = null
  private loadingStates: Ref<LoadingState> = ref({})
  private defaultRetryConfig: RetryConfig = {
    retries: 3,
    retryDelay: 1000,
    retryCondition: (error: AxiosError) => {
      // 只对网络错误或5xx错误重试
      return !error.response || (error.response.status >= 500 && error.response.status < 600)
    }
  }

  constructor(baseURL: string = config.API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  // 获取加载状态
  getLoadingStates(): Ref<LoadingState> {
    return this.loadingStates
  }

  // 检查特定请求是否在加载中
  isLoading(key: string = 'default'): boolean {
    return this.loadingStates.value[key] || false
  }

  // 设置加载状态
  private setLoading(key: string, loading: boolean) {
    this.loadingStates.value[key] = loading
  }

  // 清除加载状态
  private clearLoading(key: string) {
    delete this.loadingStates.value[key]
  }

  // 延迟函数
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  // 重试请求
  private async retryRequest(
    requestFn: () => Promise<any>,
    config: RetryConfig,
    attempt: number = 0
  ): Promise<any> {
    try {
      return await requestFn()
    } catch (error) {
      if (
        attempt < config.retries &&
        config.retryCondition &&
        config.retryCondition(error as AxiosError)
      ) {
        await this.delay(config.retryDelay * Math.pow(2, attempt)) // 指数退避
        return this.retryRequest(requestFn, config, attempt + 1)
      }
      throw error
    }
  }

  private setupInterceptors() {
    // 请求拦截器
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig & { meta?: ApiRequestConfig }) => {
        // 添加认证token
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`
        }

        // 添加时间戳防止缓存
        if (config.method === 'get') {
          config.params = {
            ...config.params,
            _t: Date.now()
          }
        }

        // 处理加载状态
        const meta = config.meta
        if (meta && !meta.skipLoading) {
          const loadingKey = meta.loadingKey || `${config.method?.toUpperCase()}_${config.url}`
          this.setLoading(loadingKey, true)
          config.meta = { ...meta, loadingKey }
        }

        return config
      },
      (error) => {
        console.error('请求拦截器错误:', error)
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // 清除加载状态
        const config = response.config as InternalAxiosRequestConfig & { meta?: ApiRequestConfig }
        const meta = config.meta
        if (meta && meta.loadingKey) {
          this.clearLoading(meta.loadingKey)
        }

        return response.data
      },
      async (error: AxiosError) => {
        // 清除加载状态
        const config = error.config as InternalAxiosRequestConfig & { meta?: ApiRequestConfig }
        const meta = config?.meta
        if (meta && meta.loadingKey) {
          this.clearLoading(meta.loadingKey)
        }

        const { response, code } = error

        // 网络错误
        if (!response) {
          if (code === 'ECONNABORTED') {
            throw new Error('请求超时，请重试')
          }
          if (code === 'ERR_NETWORK') {
            throw new Error('网络连接失败，请检查网络设置')
          }
          throw new Error('网络连接失败')
        }

        const { status, data } = response

        // 处理不同的HTTP状态码
        switch (status) {
          case 401:
            // 未授权处理 - 区分登录失败和token过期
            const errorData = data as ApiError
            const errorMessage = errorData.message || errorData.detail || '认证失败'
            
            // 如果当前在登录页面，直接抛出错误消息，不跳转
            if (window.location.pathname === '/login' || window.location.pathname.includes('/auth/')) {
              throw new Error(errorMessage)
            }
            
            // 否则清除认证信息并跳转到登录页面
            this.clearAuthToken()
            window.location.href = '/login'
            throw new Error('登录已过期，请重新登录')

          case 403:
            throw new Error('没有权限访问此资源')

          case 404:
            throw new Error('请求的资源不存在')

          case 422:
            // 验证错误
            const validationError = data as any
            if (validationError.detail && Array.isArray(validationError.detail)) {
              const errors = validationError.detail.map((err: any) => err.msg).join(', ')
              throw new Error(`输入验证失败: ${errors}`)
            }
            throw new Error(validationError.message || '输入数据验证失败')

          case 429:
            throw new Error('请求过于频繁，请稍后重试')

          case 500:
            throw new Error('服务器内部错误')

          case 502:
          case 503:
          case 504:
            throw new Error('服务暂时不可用，请稍后重试')

          default:
            const defaultErrorData = data as ApiError
            throw new Error(defaultErrorData.message || `请求失败 (${status})`)
        }
      }
    )
  }

  // 设置认证token
  setAuthToken(token: string) {
    this.authToken = token
  }

  // 清除认证token
  clearAuthToken() {
    this.authToken = null
  }

  // 通用请求方法
  private async request<T = any>(
    method: string,
    url: string,
    data?: any,
    config?: ApiRequestConfig
  ): Promise<T> {
    const retryConfig = config?.retry || this.defaultRetryConfig
    const requestConfig: any = {
      method,
      url,
      data,
      meta: config
    }

    // 处理查询参数
    if (config?.params) {
      requestConfig.params = config.params
    }

    return this.retryRequest(async () => {
      return this.client.request(requestConfig)
    }, retryConfig)
  }

  // GET请求
  async get<T = any>(url: string, config?: ApiRequestConfig): Promise<T> {
    return this.request('GET', url, undefined, config)
  }

  // POST请求
  async post<T = any>(url: string, data?: any, config?: ApiRequestConfig): Promise<T> {
    return this.request('POST', url, data, config)
  }

  // PUT请求
  async put<T = any>(url: string, data?: any, config?: ApiRequestConfig): Promise<T> {
    return this.request('PUT', url, data, config)
  }

  // PATCH请求
  async patch<T = any>(url: string, data?: any, config?: ApiRequestConfig): Promise<T> {
    return this.request('PATCH', url, data, config)
  }

  // DELETE请求
  async delete<T = any>(url: string, config?: ApiRequestConfig): Promise<T> {
    return this.request('DELETE', url, undefined, config)
  }

  // 文件上传
  async upload<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)

    return this.client.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
  }

  // 下载文件
  async download(url: string, filename?: string): Promise<void> {
    const response = await this.client.get(url, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }

  // 获取原始axios实例
  getAxiosInstance(): AxiosInstance {
    return this.client
  }
}

// 创建全局API客户端实例
export const apiClient = new ApiClient()

// 导出类型
export type { 
  ApiResponse, 
  ApiError, 
  RetryConfig, 
  LoadingState, 
  ApiRequestConfig 
}