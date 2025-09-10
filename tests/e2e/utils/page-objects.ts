/**
 * E2E测试工具函数和Page Objects
 */

import { type Page, type Locator, expect } from '@playwright/test'

/**
 * 认证相关的Page Object
 */
export class AuthPage {
  readonly page: Page
  readonly usernameInput: Locator
  readonly emailInput: Locator  
  readonly passwordInput: Locator
  readonly fullNameInput: Locator
  readonly loginButton: Locator
  readonly registerButton: Locator
  readonly logoutButton: Locator
  readonly userMenuButton: Locator
  readonly errorMessage: Locator

  constructor(page: Page) {
    this.page = page
    this.usernameInput = page.locator('input[name="username"]')
    this.emailInput = page.locator('input[name="email"]')
    this.passwordInput = page.locator('input[name="password"]')
    this.fullNameInput = page.locator('input[name="fullName"]')
    this.loginButton = page.locator('button[type="submit"]', { hasText: '登录' })
    this.registerButton = page.locator('button[type="submit"]', { hasText: '注册' })
    this.logoutButton = page.locator('button', { hasText: '退出登录' })
    this.userMenuButton = page.locator('[data-testid="user-menu"]')
    this.errorMessage = page.locator('[data-testid="error-message"]')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async gotoRegister() {
    await this.page.goto('/register')
  }

  async login(username: string, password: string) {
    await this.goto()
    await this.usernameInput.fill(username)
    await this.passwordInput.fill(password)
    await this.loginButton.click()
  }

  async register(userData: {
    username: string
    email: string
    password: string
    fullName?: string
  }) {
    await this.gotoRegister()
    await this.usernameInput.fill(userData.username)
    await this.emailInput.fill(userData.email)
    await this.passwordInput.fill(userData.password)
    
    if (userData.fullName) {
      await this.fullNameInput.fill(userData.fullName)
    }
    
    await this.registerButton.click()
  }

  async logout() {
    await this.userMenuButton.click()
    await this.logoutButton.click()
  }

  async waitForLogin() {
    await expect(this.page.locator('[data-testid="dashboard"]')).toBeVisible()
  }

  async waitForLogout() {
    await expect(this.page.locator('[data-testid="login-form"]')).toBeVisible()
  }
}

/**
 * 聊天相关的Page Object
 */
export class ChatPage {
  readonly page: Page
  readonly newChatButton: Locator
  readonly chatSessionList: Locator
  readonly messageInput: Locator
  readonly sendButton: Locator
  readonly messageHistory: Locator
  readonly sessionTitle: Locator
  readonly thinkingProcess: Locator
  readonly loadingIndicator: Locator

  constructor(page: Page) {
    this.page = page
    this.newChatButton = page.locator('[data-testid="new-chat-button"]')
    this.chatSessionList = page.locator('[data-testid="chat-session-list"]')
    this.messageInput = page.locator('[data-testid="message-input"]')
    this.sendButton = page.locator('[data-testid="send-button"]')
    this.messageHistory = page.locator('[data-testid="message-history"]')
    this.sessionTitle = page.locator('[data-testid="session-title"]')
    this.thinkingProcess = page.locator('[data-testid="thinking-process"]')
    this.loadingIndicator = page.locator('[data-testid="loading-indicator"]')
  }

  async goto() {
    await this.page.goto('/chat')
  }

  async createNewChat(title?: string) {
    await this.newChatButton.click()
    
    if (title) {
      const titleInput = this.page.locator('input[placeholder*="会话标题"]')
      await titleInput.fill(title)
      await this.page.locator('button', { hasText: '创建' }).click()
    }
  }

  async sendMessage(message: string) {
    await this.messageInput.fill(message)
    await this.sendButton.click()
  }

  async waitForMessage(content: string) {
    await expect(
      this.messageHistory.locator('.message', { hasText: content })
    ).toBeVisible()
  }

  async waitForAIResponse() {
    // 等待思考过程出现
    await expect(this.thinkingProcess).toBeVisible({ timeout: 30000 })
    
    // 等待AI回复完成
    await expect(this.loadingIndicator).toBeHidden({ timeout: 60000 })
  }

  async getMessageCount(): Promise<number> {
    const messages = this.messageHistory.locator('.message')
    return await messages.count()
  }

  async selectSession(sessionName: string) {
    await this.chatSessionList
      .locator('.session-item', { hasText: sessionName })
      .click()
  }
}

/**
 * 导航相关的Page Object
 */
export class NavigationPage {
  readonly page: Page
  readonly sidebar: Locator
  readonly chatNavItem: Locator
  readonly historyNavItem: Locator
  readonly settingsNavItem: Locator
  readonly profileNavItem: Locator

  constructor(page: Page) {
    this.page = page
    this.sidebar = page.locator('[data-testid="sidebar"]')
    this.chatNavItem = page.locator('[data-testid="nav-chat"]')
    this.historyNavItem = page.locator('[data-testid="nav-history"]')
    this.settingsNavItem = page.locator('[data-testid="nav-settings"]')
    this.profileNavItem = page.locator('[data-testid="nav-profile"]')
  }

  async goToChat() {
    await this.chatNavItem.click()
  }

  async goToHistory() {
    await this.historyNavItem.click()
  }

  async goToSettings() {
    await this.settingsNavItem.click()
  }

  async goToProfile() {
    await this.profileNavItem.click()
  }
}

/**
 * 历史记录相关的Page Object
 */
export class HistoryPage {
  readonly page: Page
  readonly sessionList: Locator
  readonly searchInput: Locator
  readonly filterButton: Locator
  readonly exportButton: Locator
  readonly deleteButton: Locator

  constructor(page: Page) {
    this.page = page
    this.sessionList = page.locator('[data-testid="history-session-list"]')
    this.searchInput = page.locator('[data-testid="history-search"]')
    this.filterButton = page.locator('[data-testid="history-filter"]')
    this.exportButton = page.locator('[data-testid="export-button"]')
    this.deleteButton = page.locator('[data-testid="delete-button"]')
  }

  async goto() {
    await this.page.goto('/history')
  }

  async searchSessions(query: string) {
    await this.searchInput.fill(query)
    await this.page.keyboard.press('Enter')
  }

  async selectSession(sessionTitle: string) {
    await this.sessionList
      .locator('.session-item', { hasText: sessionTitle })
      .click()
  }

  async deleteSession(sessionTitle: string) {
    const sessionItem = this.sessionList
      .locator('.session-item', { hasText: sessionTitle })
    
    await sessionItem.hover()
    await sessionItem.locator('[data-testid="delete-session"]').click()
    
    // 确认删除
    await this.page.locator('button', { hasText: '确认删除' }).click()
  }

  async getSessionCount(): Promise<number> {
    const sessions = this.sessionList.locator('.session-item')
    return await sessions.count()
  }
}

/**
 * 测试数据生成器
 */
export class TestDataGenerator {
  static generateUser() {
    const timestamp = Date.now()
    return {
      username: `testuser${timestamp}`,
      email: `test${timestamp}@example.com`,
      password: 'TestPassword123!',
      fullName: `Test User ${timestamp}`
    }
  }

  static generateChatMessage() {
    const messages = [
      '今天北京的天气怎么样？',
      '明天会下雨吗？',
      '这周的天气趋势如何？',
      '上海现在的温度是多少？',
      '深圳今天适合外出吗？'
    ]
    
    return messages[Math.floor(Math.random() * messages.length)]
  }

  static generateSessionTitle() {
    const titles = [
      '天气查询会话',
      '工作讨论',
      '学习笔记',
      '项目规划',
      '问题解决'
    ]
    
    const timestamp = Date.now()
    const title = titles[Math.floor(Math.random() * titles.length)]
    
    return `${title} - ${timestamp}`
  }
}

/**
 * 测试辅助函数
 */
export class TestHelpers {
  static async waitForNetworkIdle(page: Page, timeout: number = 2000) {
    await page.waitForLoadState('networkidle', { timeout })
  }

  static async takeFullScreenshot(page: Page, name: string) {
    await page.screenshot({ 
      path: `test-results/screenshots/${name}.png`,
      fullPage: true 
    })
  }

  static async mockAPIResponse(page: Page, url: string, response: any) {
    await page.route(url, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response)
      })
    })
  }

  static async interceptAPICall(page: Page, url: string): Promise<any> {
    return new Promise(resolve => {
      page.route(url, async route => {
        const response = await route.fetch()
        const json = await response.json()
        resolve(json)
        await route.continue()
      })
    })
  }
}