/**
 * ErrorHandler测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AxiosError } from 'axios'
import { 
  ErrorHandler, 
  ErrorType, 
  ErrorSeverity,
  errorHandler,
  handleError,
  canRetryError,
  getErrorMessage 
} from '@/utils/errorHandler'

describe('ErrorHandler', () => {
  let handler: ErrorHandler
  let mockErrorReporting: ReturnType<typeof vi.fn>
  let mockNotification: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockErrorReporting = vi.fn()
    mockNotification = vi.fn()
    handler = new ErrorHandler(mockErrorReporting, mockNotification)
  })

  describe('standardizeError', () => {
    it('应该处理Axios网络错误', () => {
      const axiosError = {
        isAxiosError: true,
        code: 'ERR_NETWORK',
        message: 'Network Error',
        response: undefined
      } as AxiosError

      const result = handler.standardizeError(axiosError)

      expect(result.type).toBe(ErrorType.NETWORK)
      expect(result.severity).toBe(ErrorSeverity.HIGH)
      expect(result.canRetry).toBe(true)
      expect(result.userFriendlyMessage).toContain('网络连接失败')
    })

    it('应该处理Axios超时错误', () => {
      const axiosError = {
        isAxiosError: true,
        code: 'ECONNABORTED',
        message: 'timeout of 30000ms exceeded',
        response: undefined
      } as AxiosError

      const result = handler.standardizeError(axiosError)

      expect(result.type).toBe(ErrorType.TIMEOUT)
      expect(result.severity).toBe(ErrorSeverity.MEDIUM)
      expect(result.canRetry).toBe(true)
    })

    it('应该处理401未授权错误', () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 401,
          data: { message: 'Unauthorized' }
        }
      } as AxiosError

      const result = handler.standardizeError(axiosError)

      expect(result.type).toBe(ErrorType.AUTHENTICATION)
      expect(result.severity).toBe(ErrorSeverity.HIGH)
      expect(result.canRetry).toBe(false)
      expect(result.userFriendlyMessage).toContain('登录已过期')
    })

    it('应该处理422验证错误', () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 422,
          data: {
            detail: [
              { msg: 'Field is required' },
              { msg: 'Invalid format' }
            ]
          }
        }
      } as AxiosError

      const result = handler.standardizeError(axiosError)

      expect(result.type).toBe(ErrorType.VALIDATION)
      expect(result.severity).toBe(ErrorSeverity.LOW)
      expect(result.canRetry).toBe(false)
      expect(result.userFriendlyMessage).toContain('Field is required，Invalid format')
    })

    it('应该处理500服务器错误', () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 500,
          data: { message: 'Internal Server Error' }
        }
      } as AxiosError

      const result = handler.standardizeError(axiosError)

      expect(result.type).toBe(ErrorType.SERVER)
      expect(result.severity).toBe(ErrorSeverity.HIGH)
      expect(result.canRetry).toBe(false)
    })

    it('应该处理JavaScript原生错误', () => {
      const nativeError = new TypeError('Cannot read property of undefined')

      const result = handler.standardizeError(nativeError)

      expect(result.type).toBe(ErrorType.UNKNOWN)
      expect(result.severity).toBe(ErrorSeverity.MEDIUM)
      expect(result.message).toBe(nativeError.message)
      expect(result.details?.stack).toBeDefined()
    })

    it('应该处理字符串错误', () => {
      const stringError = '发生了错误'

      const result = handler.standardizeError(stringError)

      expect(result.type).toBe(ErrorType.UNKNOWN)
      expect(result.message).toBe(stringError)
      expect(result.userFriendlyMessage).toBe(stringError)
    })
  })

  describe('handleError', () => {
    it('应该调用错误报告服务', async () => {
      const error = new Error('Test error')

      await handler.handleError(error, { reportError: true })

      expect(mockErrorReporting).toHaveBeenCalledOnce()
      const reportedError = mockErrorReporting.mock.calls[0][0]
      expect(reportedError.message).toBe('Test error')
    })

    it('应该显示通知', async () => {
      const error = new Error('Test error')

      await handler.handleError(error, { showNotification: true })

      expect(mockNotification).toHaveBeenCalledWith(
        expect.stringContaining('应用程序发生错误'),
        'error'
      )
    })

    it('应该使用备用消息', async () => {
      const error = new Error('Test error')
      const fallbackMessage = '自定义错误消息'

      await handler.handleError(error, { 
        showNotification: true,
        fallbackMessage 
      })

      expect(mockNotification).toHaveBeenCalledWith(
        fallbackMessage,
        'error'
      )
    })

    it('不应该在禁用通知时显示通知', async () => {
      const error = new Error('Test error')

      await handler.handleError(error, { showNotification: false })

      expect(mockNotification).not.toHaveBeenCalled()
    })
  })

  describe('canRetry', () => {
    it('应该对网络错误返回true', () => {
      const networkError = {
        isAxiosError: true,
        code: 'ERR_NETWORK'
      } as AxiosError

      const result = handler.canRetry(networkError)

      expect(result).toBe(true)
    })

    it('应该对认证错误返回false', () => {
      const authError = {
        isAxiosError: true,
        response: { status: 401 }
      } as AxiosError

      const result = handler.canRetry(authError)

      expect(result).toBe(false)
    })
  })

  describe('getUserFriendlyMessage', () => {
    it('应该返回标准化的用户友好消息', () => {
      const error = new Error('Technical error message')

      const result = handler.getUserFriendlyMessage(error)

      expect(result).toBe('应用程序发生错误，请刷新页面重试')
    })

    it('应该返回备用消息', () => {
      const error = new Error('Technical error message')
      const fallback = '自定义备用消息'

      const result = handler.getUserFriendlyMessage(error, fallback)

      expect(result).toBe(fallback)
    })
  })
})

describe('全局错误处理函数', () => {
  it('handleError应该正常工作', async () => {
    const error = new Error('Test error')
    
    const result = await handleError(error)
    
    expect(result.message).toBe('Test error')
    expect(result.type).toBe(ErrorType.UNKNOWN)
  })

  it('canRetryError应该正常工作', () => {
    const networkError = {
      isAxiosError: true,
      code: 'ERR_NETWORK'
    } as AxiosError

    const result = canRetryError(networkError)

    expect(result).toBe(true)
  })

  it('getErrorMessage应该正常工作', () => {
    const error = new Error('Test error')

    const result = getErrorMessage(error, '备用消息')

    expect(result).toBe('备用消息')
  })
})