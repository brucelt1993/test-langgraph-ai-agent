/**
 * 历史记录管理E2E测试
 */

import { test, expect } from '@playwright/test'
import { 
  AuthPage, 
  ChatPage, 
  HistoryPage, 
  NavigationPage,
  TestDataGenerator 
} from '../utils/page-objects'

test.describe('历史记录管理功能', () => {
  let authPage: AuthPage
  let chatPage: ChatPage
  let historyPage: HistoryPage
  let navPage: NavigationPage

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page)
    chatPage = new ChatPage(page)
    historyPage = new HistoryPage(page)
    navPage = new NavigationPage(page)

    // 登录测试用户
    await authPage.login('e2etestuser', 'E2ETestPassword123!')
    await authPage.waitForLogin()
  })

  test('会话历史记录查看和管理', async ({ page }) => {
    // 首先创建一些测试会话
    await test.step('创建测试会话', async () => {
      await chatPage.goto()
      
      const sessionTitles = ['天气查询会话', '工作讨论', '学习笔记']
      
      for (const title of sessionTitles) {
        await chatPage.createNewChat(title)
        await chatPage.sendMessage(`这是${title}的测试消息`)
        await chatPage.waitForMessage(`这是${title}的测试消息`)
      }
    })

    await test.step('访问历史记录页面', async () => {
      await historyPage.goto()
      
      // 验证历史记录页面加载
      await expect(historyPage.sessionList).toBeVisible()
      
      // 验证至少有创建的会话
      const sessionCount = await historyPage.getSessionCount()
      expect(sessionCount).toBeGreaterThanOrEqual(3)
    })

    await test.step('搜索历史会话', async () => {
      await historyPage.searchSessions('天气')
      
      // 验证搜索结果
      await expect(historyPage.sessionList.locator('.session-item')).toContainText('天气查询会话')
      
      // 清除搜索
      await historyPage.searchInput.fill('')
      await page.keyboard.press('Enter')
    })

    await test.step('查看会话详情', async () => {
      await historyPage.selectSession('工作讨论')
      
      // 验证会话详情页面
      await expect(page.locator('[data-testid="session-detail"]')).toBeVisible()
      await expect(page.locator('[data-testid="session-title"]')).toContainText('工作讨论')
      
      // 验证消息历史显示
      await expect(page.locator('.message-history')).toBeVisible()
      await expect(page.locator('.message', { hasText: '这是工作讨论的测试消息' })).toBeVisible()
    })

    await test.step('删除历史会话', async () => {
      await historyPage.goto() // 返回历史列表
      
      const initialCount = await historyPage.getSessionCount()
      
      await historyPage.deleteSession('学习笔记')
      
      // 验证会话被删除
      const newCount = await historyPage.getSessionCount()
      expect(newCount).toBe(initialCount - 1)
      
      // 验证删除的会话不再显示
      await expect(historyPage.sessionList.locator('.session-item', { hasText: '学习笔记' })).not.toBeVisible()
    })
  })

  test('会话导出功能', async ({ page }) => {
    await chatPage.goto()
    
    // 创建一个有多条消息的会话
    await test.step('创建详细会话', async () => {
      await chatPage.createNewChat('导出测试会话')
      
      const messages = [
        '你好，这是第一条消息',
        '请介绍一下人工智能',
        '谢谢你的回答'
      ]
      
      for (const message of messages) {
        await chatPage.sendMessage(message)
        await chatPage.waitForMessage(message)
      }
    })

    await test.step('导出会话数据', async () => {
      await historyPage.goto()
      await historyPage.selectSession('导出测试会话')
      
      // 设置下载监听
      const downloadPromise = page.waitForEvent('download')
      
      // 点击导出按钮
      await page.locator('[data-testid="export-session"]').click()
      await page.locator('[data-testid="export-json"]').click()
      
      const download = await downloadPromise
      expect(download.suggestedFilename()).toContain('.json')
      
      // 验证导出成功提示
      await expect(page.locator('.export-success-message')).toBeVisible()
    })
  })

  test('会话统计和分析', async ({ page }) => {
    await historyPage.goto()
    
    await test.step('查看整体统计', async () => {
      // 验证统计面板显示
      await expect(page.locator('[data-testid="stats-panel"]')).toBeVisible()
      
      // 验证统计数据
      const totalSessions = page.locator('[data-testid="total-sessions"]')
      await expect(totalSessions).toBeVisible()
      
      const totalMessages = page.locator('[data-testid="total-messages"]')
      await expect(totalMessages).toBeVisible()
      
      // 验证数字大于0
      const sessionsText = await totalSessions.textContent()
      const messagesText = await totalMessages.textContent()
      
      expect(parseInt(sessionsText || '0')).toBeGreaterThan(0)
      expect(parseInt(messagesText || '0')).toBeGreaterThan(0)
    })

    await test.step('查看使用趋势', async () => {
      // 点击趋势图标签
      await page.locator('[data-testid="trends-tab"]').click()
      
      // 验证趋势图显示
      await expect(page.locator('[data-testid="usage-chart"]')).toBeVisible()
      
      // 验证时间范围选择器
      await expect(page.locator('[data-testid="time-range-selector"]')).toBeVisible()
    })
  })

  test('批量操作功能', async ({ page }) => {
    await historyPage.goto()
    
    await test.step('批量选择会话', async () => {
      // 进入批量操作模式
      await page.locator('[data-testid="batch-mode-toggle"]').click()
      
      // 验证批量操作界面显示
      await expect(page.locator('[data-testid="batch-toolbar"]')).toBeVisible()
      
      // 选择多个会话
      const sessionItems = page.locator('.session-item')
      const count = await sessionItems.count()
      
      if (count >= 2) {
        await sessionItems.first().locator('.session-checkbox').check()
        await sessionItems.nth(1).locator('.session-checkbox').check()
        
        // 验证批量操作按钮启用
        await expect(page.locator('[data-testid="batch-delete-btn"]')).toBeEnabled()
        await expect(page.locator('[data-testid="batch-export-btn"]')).toBeEnabled()
      }
    })

    await test.step('批量导出', async () => {
      const downloadPromise = page.waitForEvent('download')
      
      await page.locator('[data-testid="batch-export-btn"]').click()
      await page.locator('[data-testid="export-format-json"]').click()
      
      const download = await downloadPromise
      expect(download.suggestedFilename()).toMatch(/batch_export.*\.zip/)
    })
  })

  test('会话标签和分类', async ({ page }) => {
    await chatPage.goto()
    
    await test.step('为会话添加标签', async () => {
      // 创建新会话
      await chatPage.createNewChat('标签测试会话')
      await chatPage.sendMessage('测试消息')
      await chatPage.waitForMessage('测试消息')
      
      // 添加标签
      await page.locator('[data-testid="session-settings"]').click()
      await page.locator('[data-testid="add-tags"]').click()
      
      const tagInput = page.locator('input[placeholder*="添加标签"]')
      await tagInput.fill('测试')
      await page.keyboard.press('Enter')
      
      await tagInput.fill('AI对话')
      await page.keyboard.press('Enter')
      
      // 保存标签
      await page.locator('button', { hasText: '保存' }).click()
    })

    await test.step('按标签筛选会话', async () => {
      await historyPage.goto()
      
      // 点击标签筛选
      await page.locator('[data-testid="filter-by-tags"]').click()
      await page.locator('[data-testid="tag-filter"]', { hasText: '测试' }).click()
      
      // 验证筛选结果
      await expect(historyPage.sessionList.locator('.session-item', { hasText: '标签测试会话' })).toBeVisible()
      
      // 清除筛选
      await page.locator('[data-testid="clear-filters"]').click()
    })
  })

  test('会话收藏功能', async ({ page }) => {
    await historyPage.goto()
    
    await test.step('收藏会话', async () => {
      const firstSession = historyPage.sessionList.locator('.session-item').first()
      
      // 鼠标悬停显示操作按钮
      await firstSession.hover()
      
      // 点击收藏按钮
      await firstSession.locator('[data-testid="favorite-btn"]').click()
      
      // 验证收藏状态
      await expect(firstSession.locator('[data-testid="favorite-icon"]')).toBeVisible()
    })

    await test.step('查看收藏会话', async () => {
      // 切换到收藏标签
      await page.locator('[data-testid="favorites-tab"]').click()
      
      // 验证收藏的会话显示
      await expect(historyPage.sessionList.locator('.session-item')).toHaveCountGreaterThan(0)
    })

    await test.step('取消收藏', async () => {
      const favoriteSession = historyPage.sessionList.locator('.session-item').first()
      await favoriteSession.hover()
      
      // 点击取消收藏
      await favoriteSession.locator('[data-testid="unfavorite-btn"]').click()
      
      // 验证会话从收藏列表移除
      await expect(favoriteSession).not.toBeVisible()
    })
  })
})