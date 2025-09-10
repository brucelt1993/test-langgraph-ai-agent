/**
 * E2E测试全局清理
 */

import { chromium, type FullConfig } from '@playwright/test'

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting E2E test environment cleanup...')
  
  const baseURL = config.projects[0].use?.baseURL || 'http://localhost:3000'
  const apiURL = baseURL.replace(':3000', ':8000')
  
  const browser = await chromium.launch()
  const page = await browser.newPage()
  
  try {
    // 清理测试数据
    console.log('🗑️ Cleaning up test data...')
    
    // 如果需要，这里可以添加清理逻辑
    // 例如：删除测试用户、清理测试会话等
    
    console.log('✅ E2E test environment cleanup completed!')
    
  } catch (error) {
    console.log('⚠️ Error during cleanup:', error)
  } finally {
    await browser.close()
  }
}

export default globalTeardown