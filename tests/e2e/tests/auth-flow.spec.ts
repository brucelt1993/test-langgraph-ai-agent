/**
 * 认证流程E2E测试
 */

import { test, expect } from '@playwright/test'
import { AuthPage, NavigationPage, TestDataGenerator } from '../utils/page-objects'

test.describe('用户认证流程', () => {
  let authPage: AuthPage
  let navPage: NavigationPage

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page)
    navPage = new NavigationPage(page)
  })

  test('用户注册和登录完整流程', async ({ page }) => {
    // 生成测试用户数据
    const userData = TestDataGenerator.generateUser()

    // 1. 用户注册
    await test.step('用户注册', async () => {
      await authPage.register(userData)
      
      // 验证注册成功
      await expect(page.locator('.success-message')).toBeVisible()
      await expect(page.locator('.success-message')).toContainText('注册成功')
    })

    // 2. 用户登录
    await test.step('用户登录', async () => {
      await authPage.login(userData.username, userData.password)
      
      // 验证登录成功，跳转到主页
      await authPage.waitForLogin()
      await expect(page).toHaveURL(/.*\/chat/)
    })

    // 3. 验证用户信息
    await test.step('验证用户信息', async () => {
      await authPage.userMenuButton.click()
      
      // 验证用户名显示正确
      await expect(page.locator('[data-testid="user-name"]')).toContainText(userData.fullName)
      await expect(page.locator('[data-testid="user-email"]')).toContainText(userData.email)
    })

    // 4. 用户登出
    await test.step('用户登出', async () => {
      await authPage.logout()
      
      // 验证登出成功，跳转到登录页
      await authPage.waitForLogout()
      await expect(page).toHaveURL(/.*\/login/)
    })
  })

  test('登录表单验证', async ({ page }) => {
    await authPage.goto()

    await test.step('空表单提交', async () => {
      await authPage.loginButton.click()
      
      // 验证必填字段提示
      await expect(page.locator('.field-error')).toHaveCount(2) // 用户名和密码
    })

    await test.step('无效用户名', async () => {
      await authPage.usernameInput.fill('nonexistentuser')
      await authPage.passwordInput.fill('wrongpassword')
      await authPage.loginButton.click()
      
      // 验证登录失败提示
      await expect(authPage.errorMessage).toBeVisible()
      await expect(authPage.errorMessage).toContainText('用户名或密码错误')
    })
  })

  test('注册表单验证', async ({ page }) => {
    await authPage.gotoRegister()

    await test.step('密码强度验证', async () => {
      await authPage.usernameInput.fill('testuser')
      await authPage.emailInput.fill('test@example.com')
      await authPage.passwordInput.fill('123') // 弱密码
      await authPage.registerButton.click()
      
      // 验证密码强度提示
      await expect(page.locator('.password-error')).toBeVisible()
      await expect(page.locator('.password-error')).toContainText('密码强度不够')
    })

    await test.step('邮箱格式验证', async () => {
      await authPage.emailInput.fill('invalid-email')
      await authPage.registerButton.click()
      
      // 验证邮箱格式提示
      await expect(page.locator('.email-error')).toBeVisible()
    })
  })

  test('记住登录状态', async ({ page, context }) => {
    // 使用已知的测试用户登录
    await authPage.login('e2etestuser', 'E2ETestPassword123!')
    await authPage.waitForLogin()

    // 关闭页面并重新打开
    await page.close()
    const newPage = await context.newPage()
    await newPage.goto('/chat')

    // 验证用户仍然处于登录状态
    await expect(newPage.locator('[data-testid="dashboard"]')).toBeVisible()
    await expect(newPage).toHaveURL(/.*\/chat/)
  })

  test('会话过期处理', async ({ page }) => {
    // 登录用户
    await authPage.login('e2etestuser', 'E2ETestPassword123!')
    await authPage.waitForLogin()

    // 模拟token过期
    await page.evaluate(() => {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    })

    // 尝试访问需要认证的页面
    await page.goto('/chat')

    // 验证被重定向到登录页
    await expect(page).toHaveURL(/.*\/login/)
    await expect(page.locator('.session-expired-message')).toBeVisible()
  })

  test('多设备登录管理', async ({ page }) => {
    // 登录用户
    await authPage.login('e2etestuser', 'E2ETestPassword123!')
    await authPage.waitForLogin()

    // 进入用户设置页面
    await navPage.goToProfile()

    // 查看活跃会话
    await page.locator('[data-testid="active-sessions-tab"]').click()

    // 验证当前会话显示
    await expect(page.locator('.session-item')).toHaveCountGreaterThan(0)

    // 撤销其他会话
    const otherSessions = page.locator('.session-item:not(.current-session)')
    if (await otherSessions.count() > 0) {
      await otherSessions.first().locator('.revoke-button').click()
      await page.locator('button', { hasText: '确认' }).click()

      // 验证会话被撤销
      await expect(page.locator('.success-message')).toBeVisible()
    }
  })
})