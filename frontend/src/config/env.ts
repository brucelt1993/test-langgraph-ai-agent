/**
 * 环境配置
 */

// 环境变量类型
interface EnvConfig {
  API_BASE_URL: string
  APP_NAME: string
  VERSION: string
  DEBUG: boolean
}

// 获取环境配置
function getEnvConfig(): EnvConfig {
  const isDevelopment = import.meta.env.DEV
  const isProduction = import.meta.env.PROD
  
  return {
    // API基础地址
    API_BASE_URL: isDevelopment 
      ? 'http://localhost:8000/api'  // 开发环境
      : '/api',                      // 生产环境使用相对路径
    
    // 应用名称
    APP_NAME: 'AI Agent',
    
    // 版本号
    VERSION: '0.1.0',
    
    // 调试模式
    DEBUG: isDevelopment
  }
}

// 导出配置
export const config = getEnvConfig()

// 导出类型
export type { EnvConfig }