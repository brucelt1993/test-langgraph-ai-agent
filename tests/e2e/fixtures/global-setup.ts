/**
 * E2E测试全局设置
 */

import { chromium, type FullConfig } from '@playwright/test'

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E test environment setup...')
  
  const baseURL = config.projects[0].use?.baseURL || 'http://localhost:3000'
  
  // 启动浏览器进行初始化
  const browser = await chromium.launch()
  const page = await browser.newPage()
  
  try {
    console.log(`📡 Checking application availability at ${baseURL}`)
    
    // 等待应用启动
    let retries = 30
    while (retries > 0) {
      try {
        await page.goto(baseURL, { timeout: 5000 })
        console.log('✅ Application is ready!')
        break
      } catch (error) {
        retries--
        if (retries === 0) {
          throw new Error(`Application not available at ${baseURL} after 30 retries`)
        }
        console.log(`⏳ Waiting for application... (${31 - retries}/30)`)
        await page.waitForTimeout(1000)
      }
    }
    
    // 初始化测试数据
    console.log('🗄️ Setting up test data...')
    
    // 这里可以调用API创建测试用户等初始化操作
    try {
      // 创建测试用户
      const response = await page.request.post(`${baseURL.replace(':3000', ':8000')}/api/auth/register`, {
        data: {
          username: 'e2etestuser',
          email: 'e2etest@example.com',
          password: 'E2ETestPassword123!',
          full_name: 'E2E Test User'
        }
      })
      
      if (response.ok()) {
        console.log('✅ Test user created successfully')
      } else {
        console.log('ℹ️ Test user might already exist, continuing...')
      }
    } catch (error) {
      console.log('⚠️ Could not create test user, tests might fail:', error)
    }
    
    console.log('✅ E2E test environment setup completed!')
    
  } finally {
    await browser.close()
  }
}

export default globalSetup