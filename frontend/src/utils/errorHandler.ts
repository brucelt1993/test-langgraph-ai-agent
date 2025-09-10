import { AxiosError } from 'axios'

// 错误类型枚举
export enum ErrorType {
  NETWORK = 'network',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  VALIDATION = 'validation',
  SERVER = 'server',
  TIMEOUT = 'timeout',
  RATE_LIMIT = 'rate_limit',
  NOT_FOUND = 'not_found',
  UNKNOWN = 'unknown'
}

// 错误严重级别
export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// 标准化错误接口
export interface StandardError {
  type: ErrorType
  severity: ErrorSeverity
  message: string
  originalError?: any
  details?: Record<string, any>
  timestamp: string
  canRetry: boolean
  userFriendlyMessage: string
}

// 错误处理选项
export interface ErrorHandlingOptions {
  showNotification?: boolean
  logError?: boolean
  reportError?: boolean
  fallbackMessage?: string
}

// 错误处理器类
export class ErrorHandler {
  private errorReportingService?: (error: StandardError) => Promise<void>
  private notificationService?: (message: string, type: 'error' | 'warning' | 'info') => void

  constructor(
    errorReportingService?: (error: StandardError) => Promise<void>,
    notificationService?: (message: string, type: 'error' | 'warning' | 'info') => void
  ) {
    this.errorReportingService = errorReportingService
    this.notificationService = notificationService
  }

  // 标准化错误
  public standardizeError(error: any): StandardError {
    const timestamp = new Date().toISOString()

    // 处理Axios错误
    if (error.isAxiosError) {
      return this.handleAxiosError(error as AxiosError, timestamp)
    }

    // 处理JavaScript原生错误
    if (error instanceof Error) {
      return this.handleNativeError(error, timestamp)
    }

    // 处理字符串错误
    if (typeof error === 'string') {
      return {
        type: ErrorType.UNKNOWN,
        severity: ErrorSeverity.MEDIUM,
        message: error,
        originalError: error,
        timestamp,
        canRetry: false,
        userFriendlyMessage: error
      }
    }

    // 处理未知错误
    return {
      type: ErrorType.UNKNOWN,
      severity: ErrorSeverity.MEDIUM,
      message: '发生了未知错误',
      originalError: error,
      timestamp,
      canRetry: false,
      userFriendlyMessage: '发生了未知错误，请稍后重试'
    }
  }

  // 处理Axios错误
  private handleAxiosError(error: AxiosError, timestamp: string): StandardError {
    const { response, code, message } = error

    // 网络错误
    if (!response) {
      if (code === 'ECONNABORTED') {
        return {
          type: ErrorType.TIMEOUT,
          severity: ErrorSeverity.MEDIUM,
          message: '请求超时',
          originalError: error,
          timestamp,
          canRetry: true,
          userFriendlyMessage: '请求超时，请重试'
        }
      }

      if (code === 'ERR_NETWORK') {
        return {
          type: ErrorType.NETWORK,
          severity: ErrorSeverity.HIGH,
          message: '网络连接失败',
          originalError: error,
          timestamp,
          canRetry: true,
          userFriendlyMessage: '网络连接失败，请检查网络设置后重试'
        }
      }

      return {
        type: ErrorType.NETWORK,
        severity: ErrorSeverity.HIGH,
        message: message || '网络请求失败',
        originalError: error,
        timestamp,
        canRetry: true,
        userFriendlyMessage: '网络连接异常，请稍后重试'
      }
    }

    const { status, data } = response

    // 根据HTTP状态码分类错误
    switch (status) {
      case 400:
        return {
          type: ErrorType.VALIDATION,
          severity: ErrorSeverity.LOW,
          message: (data as any)?.message || '请求参数错误',
          originalError: error,
          details: (data as any)?.details,
          timestamp,
          canRetry: false,
          userFriendlyMessage: '请求参数有误，请检查后重试'
        }

      case 401:
        return {
          type: ErrorType.AUTHENTICATION,
          severity: ErrorSeverity.HIGH,
          message: '未授权访问',
          originalError: error,
          timestamp,
          canRetry: false,
          userFriendlyMessage: '登录已过期，请重新登录'
        }

      case 403:
        return {
          type: ErrorType.AUTHORIZATION,
          severity: ErrorSeverity.MEDIUM,
          message: '权限不足',
          originalError: error,
          timestamp,
          canRetry: false,
          userFriendlyMessage: '没有权限访问此资源'
        }

      case 404:
        return {
          type: ErrorType.NOT_FOUND,
          severity: ErrorSeverity.LOW,
          message: '资源不存在',
          originalError: error,
          timestamp,
          canRetry: false,
          userFriendlyMessage: '请求的资源不存在'
        }

      case 422:
        return {
          type: ErrorType.VALIDATION,
          severity: ErrorSeverity.LOW,
          message: '数据验证失败',
          originalError: error,
          details: (data as any)?.detail,
          timestamp,
          canRetry: false,
          userFriendlyMessage: this.formatValidationErrors((data as any)?.detail) || '输入数据验证失败'
        }

      case 429:
        return {
          type: ErrorType.RATE_LIMIT,
          severity: ErrorSeverity.MEDIUM,
          message: '请求过于频繁',
          originalError: error,
          timestamp,
          canRetry: true,
          userFriendlyMessage: '请求过于频繁，请稍后重试'
        }

      case 500:
      case 502:
      case 503:
      case 504:
        return {
          type: ErrorType.SERVER,
          severity: ErrorSeverity.HIGH,
          message: '服务器错误',
          originalError: error,
          timestamp,
          canRetry: status !== 500, // 500错误通常不应该重试
          userFriendlyMessage: status === 500 ? '服务器内部错误' : '服务暂时不可用，请稍后重试'
        }

      default:
        return {
          type: ErrorType.UNKNOWN,
          severity: ErrorSeverity.MEDIUM,
          message: (data as any)?.message || `HTTP ${status} 错误`,
          originalError: error,
          timestamp,
          canRetry: false,
          userFriendlyMessage: (data as any)?.message || '请求失败，请稍后重试'
        }
    }
  }

  // 处理JavaScript原生错误
  private handleNativeError(error: Error, timestamp: string): StandardError {
    return {
      type: ErrorType.UNKNOWN,
      severity: ErrorSeverity.MEDIUM,
      message: error.message,
      originalError: error,
      details: {
        stack: error.stack,
        name: error.name
      },
      timestamp,
      canRetry: false,
      userFriendlyMessage: '应用程序发生错误，请刷新页面重试'
    }
  }

  // 格式化验证错误
  private formatValidationErrors(details: any): string | null {
    if (!details || !Array.isArray(details)) {
      return null
    }

    return details
      .map((error: any) => {
        if (typeof error === 'string') return error
        if (error.msg) return error.msg
        if (error.message) return error.message
        return '验证错误'
      })
      .join('，')
  }

  // 处理错误
  public async handleError(
    error: any,
    options: ErrorHandlingOptions = {}
  ): Promise<StandardError> {
    const standardError = this.standardizeError(error)

    // 记录错误
    if (options.logError !== false) {
      this.logError(standardError)
    }

    // 显示通知
    if (options.showNotification !== false && this.notificationService) {
      const message = options.fallbackMessage || standardError.userFriendlyMessage
      const notificationType = standardError.severity === ErrorSeverity.LOW ? 'warning' : 'error'
      this.notificationService(message, notificationType)
    }

    // 报告错误
    if (options.reportError && this.errorReportingService) {
      try {
        await this.errorReportingService(standardError)
      } catch (reportingError) {
        console.error('错误报告失败:', reportingError)
      }
    }

    return standardError
  }

  // 记录错误
  private logError(error: StandardError): void {
    const logLevel = this.getLogLevel(error.severity)
    const logData = {
      type: error.type,
      message: error.message,
      userFriendlyMessage: error.userFriendlyMessage,
      timestamp: error.timestamp,
      details: error.details,
      originalError: error.originalError
    }

    switch (logLevel) {
      case 'error':
        console.error('[ErrorHandler]', logData)
        break
      case 'warn':
        console.warn('[ErrorHandler]', logData)
        break
      case 'info':
        console.info('[ErrorHandler]', logData)
        break
      default:
        console.log('[ErrorHandler]', logData)
    }
  }

  // 获取日志级别
  private getLogLevel(severity: ErrorSeverity): string {
    switch (severity) {
      case ErrorSeverity.CRITICAL:
      case ErrorSeverity.HIGH:
        return 'error'
      case ErrorSeverity.MEDIUM:
        return 'warn'
      case ErrorSeverity.LOW:
        return 'info'
      default:
        return 'log'
    }
  }

  // 检查错误是否可以重试
  public canRetry(error: any): boolean {
    const standardError = this.standardizeError(error)
    return standardError.canRetry
  }

  // 获取用户友好的错误消息
  public getUserFriendlyMessage(error: any, fallback?: string): string {
    const standardError = this.standardizeError(error)
    return fallback || standardError.userFriendlyMessage
  }
}

// 创建全局错误处理器实例
export const errorHandler = new ErrorHandler()

// 便捷方法
export const handleError = (error: any, options?: ErrorHandlingOptions) => 
  errorHandler.handleError(error, options)

export const canRetryError = (error: any) => errorHandler.canRetry(error)

export const getErrorMessage = (error: any, fallback?: string) => 
  errorHandler.getUserFriendlyMessage(error, fallback)