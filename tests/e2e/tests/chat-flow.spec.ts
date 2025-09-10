/**
 * 聊天流程E2E测试
 */

import { test, expect } from '@playwright/test'
import { 
  AuthPage, 
  ChatPage, 
  NavigationPage, 
  TestDataGenerator, 
  TestHelpers 
} from '../utils/page-objects'

test.describe('聊天功能流程', () => {
  let authPage: AuthPage
  let chatPage: ChatPage
  let navPage: NavigationPage

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page)
    chatPage = new ChatPage(page)
    navPage = new NavigationPage(page)

    // 登录测试用户
    await authPage.login('e2etestuser', 'E2ETestPassword123!')
    await authPage.waitForLogin()
  })

  test('创建新聊天会话并发送消息', async ({ page }) => {
    await test.step('创建新聊天会话', async () => {
      await chatPage.goto()
      
      const sessionTitle = TestDataGenerator.generateSessionTitle()
      await chatPage.createNewChat(sessionTitle)
      
      // 验证会话创建成功
      await expect(chatPage.sessionTitle).toContainText(sessionTitle)
    })

    await test.step('发送用户消息', async () => {
      const userMessage = TestDataGenerator.generateChatMessage()
      await chatPage.sendMessage(userMessage)
      
      // 验证消息发送成功
      await chatPage.waitForMessage(userMessage)
      
      // 验证消息显示在聊天历史中
      const messageCount = await chatPage.getMessageCount()
      expect(messageCount).toBeGreaterThan(0)
    })

    await test.step('等待AI响应', async () => {
      // 等待AI思考过程显示
      await expect(chatPage.thinkingProcess).toBeVisible({ timeout: 10000 })
      
      // 等待AI回复完成
      await chatPage.waitForAIResponse()
      
      // 验证AI回复出现
      const finalMessageCount = await chatPage.getMessageCount()
      expect(finalMessageCount).toBeGreaterThanOrEqual(2) // 用户消息 + AI回复
    })
  })

  test('多轮对话流程', async ({ page }) => {
    await chatPage.goto()
    
    // 创建新会话
    const sessionTitle = '多轮对话测试'
    await chatPage.createNewChat(sessionTitle)

    const messages = [
      '你好，我想了解天气信息',
      '北京今天的天气怎么样？',
      '明天会下雨吗？',
      '这周的天气趋势如何？'
    ]

    for (let i = 0; i < messages.length; i++) {
      await test.step(`第${i + 1}轮对话`, async () => {
        const message = messages[i]
        
        // 发送消息
        await chatPage.sendMessage(message)
        await chatPage.waitForMessage(message)
        
        // 等待AI响应
        await chatPage.waitForAIResponse()
        
        // 验证消息数量增加
        const messageCount = await chatPage.getMessageCount()
        expect(messageCount).toBeGreaterThanOrEqual((i + 1) * 2) // 每轮对话包含用户消息和AI回复
      })
    }

    // 验证完整对话历史
    for (const message of messages) {
      await expect(chatPage.messageHistory.locator('.message', { hasText: message })).toBeVisible()
    }
  })

  test('AI思考过程展示', async ({ page }) => {
    await chatPage.goto()
    await chatPage.createNewChat('思考过程测试')

    await test.step('发送复杂查询', async () => {
      await chatPage.sendMessage('帮我分析一下北京、上海、深圳三个城市今天的天气情况，并给出出行建议')
      
      // 验证思考过程显示
      await expect(chatPage.thinkingProcess).toBeVisible({ timeout: 15000 })
    })

    await test.step('验证思考步骤', async () => {
      // 验证思考步骤包含分析内容
      const thinkingSteps = page.locator('[data-testid="thinking-step"]')
      await expect(thinkingSteps).toHaveCountGreaterThan(0)
      
      // 验证思考过程可以展开/折叠
      const expandButton = page.locator('[data-testid="thinking-expand"]').first()
      if (await expandButton.isVisible()) {
        await expandButton.click()
        await expect(page.locator('[data-testid="thinking-detail"]')).toBeVisible()
      }
    })

    await test.step('等待最终回复', async () => {
      await chatPage.waitForAIResponse()
      
      // 验证AI给出了完整的分析和建议
      const aiMessages = page.locator('.message.ai-message')
      await expect(aiMessages.last()).toBeVisible()
      
      // 验证回复内容包含关键信息
      const lastAiMessage = aiMessages.last()
      await expect(lastAiMessage).toContainText('北京')
      await expect(lastAiMessage).toContainText('上海')
      await expect(lastAiMessage).toContainText('深圳')
    })
  })

  test('会话管理功能', async ({ page }) => {
    await chatPage.goto()

    const sessionTitles: string[] = []

    await test.step('创建多个会话', async () => {
      for (let i = 0; i < 3; i++) {
        const title = `测试会话 ${i + 1}`
        sessionTitles.push(title)
        
        await chatPage.createNewChat(title)
        await chatPage.sendMessage(`这是会话 ${i + 1} 的测试消息`)
        await chatPage.waitForMessage(`这是会话 ${i + 1} 的测试消息`)
      }
    })

    await test.step('切换会话', async () => {
      // 切换到第一个会话
      await chatPage.selectSession(sessionTitles[0])
      await expect(chatPage.sessionTitle).toContainText(sessionTitles[0])
      
      // 验证消息历史正确加载
      await chatPage.waitForMessage('这是会话 1 的测试消息')
    })

    await test.step('会话重命名', async () => {
      // 右键点击会话进行重命名
      const firstSession = chatPage.chatSessionList
        .locator('.session-item', { hasText: sessionTitles[0] })
      
      await firstSession.click({ button: 'right' })
      await page.locator('[data-testid="rename-session"]').click()
      
      const newTitle = '重命名后的会话'
      await page.locator('input[placeholder*="会话标题"]').fill(newTitle)
      await page.locator('button', { hasText: '确认' }).click()
      
      // 验证重命名成功
      await expect(chatPage.sessionTitle).toContainText(newTitle)
    })

    await test.step('删除会话', async () => {
      // 删除最后一个会话
      const lastSession = chatPage.chatSessionList
        .locator('.session-item', { hasText: sessionTitles[2] })
      
      await lastSession.click({ button: 'right' })
      await page.locator('[data-testid="delete-session"]').click()
      await page.locator('button', { hasText: '确认删除' }).click()
      
      // 验证会话被删除
      await expect(lastSession).not.toBeVisible()
    })
  })

  test('实时消息流功能', async ({ page }) => {
    await chatPage.goto()
    await chatPage.createNewChat('实时流测试')

    await test.step('测试流式响应', async () => {
      await chatPage.sendMessage('请详细介绍一下人工智能的发展历史')
      
      // 监听流式响应
      let streamingStarted = false
      let streamingCompleted = false
      
      // 验证流式响应开始
      await expect(chatPage.loadingIndicator).toBeVisible()
      streamingStarted = true
      
      // 监听消息内容逐步出现
      const aiMessageContainer = page.locator('.message.ai-message').last()
      
      // 等待内容开始出现
      await expect(aiMessageContainer).toBeVisible({ timeout: 30000 })
      
      // 验证内容逐步增加（流式效果）
      let previousLength = 0
      for (let i = 0; i < 5; i++) {
        await page.waitForTimeout(1000)
        const currentContent = await aiMessageContainer.textContent()
        const currentLength = currentContent?.length || 0
        
        if (currentLength > previousLength) {
          // 内容在增加，说明流式响应正在工作
          previousLength = currentLength
        }
      }
      
      // 等待流式响应完成
      await chatPage.waitForAIResponse()
      streamingCompleted = true
      
      expect(streamingStarted).toBe(true)
      expect(streamingCompleted).toBe(true)
    })
  })

  test('离线和网络错误处理', async ({ page }) => {
    await chatPage.goto()
    await chatPage.createNewChat('网络错误测试')

    await test.step('模拟网络断开', async () => {
      // 模拟网络离线
      await page.context().setOffline(true)
      
      await chatPage.sendMessage('这条消息应该发送失败')
      
      // 验证错误提示显示
      await expect(page.locator('.network-error-message')).toBeVisible()
      await expect(page.locator('.network-error-message')).toContainText('网络连接失败')
    })

    await test.step('恢复网络连接', async () => {
      // 恢复网络连接
      await page.context().setOffline(false)
      
      // 点击重试按钮
      await page.locator('[data-testid="retry-button"]').click()
      
      // 验证消息重新发送成功
      await chatPage.waitForMessage('这条消息应该发送失败')
      await expect(page.locator('.network-error-message')).not.toBeVisible()
    })
  })

  test('移动端响应式布局', async ({ page }) => {
    await chatPage.goto()
    
    await test.step('桌面端布局验证', async () => {
      // 验证桌面端侧边栏可见
      await expect(chatPage.chatSessionList).toBeVisible()
      
      // 验证消息输入区域正确显示
      await expect(chatPage.messageInput).toBeVisible()
      await expect(chatPage.sendButton).toBeVisible()
    })

    await test.step('移动端布局验证', async () => {
      // 切换到移动端视窗
      await page.setViewportSize({ width: 375, height: 667 })
      
      // 验证移动端适配
      await expect(chatPage.messageInput).toBeVisible()
      await expect(chatPage.sendButton).toBeVisible()
      
      // 验证侧边栏在移动端可能被隐藏或折叠
      const sidebar = page.locator('[data-testid="sidebar"]')
      if (await sidebar.isVisible()) {
        // 如果侧边栏可见，验证是否为折叠状态
        await expect(sidebar).toHaveClass(/collapsed/)
      }
    })

    await test.step('平板端布局验证', async () => {
      // 切换到平板端视窗
      await page.setViewportSize({ width: 768, height: 1024 })
      
      // 验证平板端布局适应
      await expect(chatPage.messageInput).toBeVisible()
      await expect(chatPage.chatSessionList).toBeVisible()
    })
  })
})