import { expect, test } from '@playwright/test'

test('admin can open locations page without runtime crash', async ({ page }) => {
  const pageErrors: string[] = []
  const consoleErrors: string[] = []

  page.on('pageerror', (error) => {
    pageErrors.push(error.message)
  })

  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text())
    }
  })

  await page.goto('/login')
  await page.locator('#username').fill('admin')
  await page.locator('#password').fill('123456')
  await page.getByRole('button', { name: /进入园区 EMS|登录中/ }).click()

  await page.waitForURL(/\/dashboard$/, { timeout: 15000 })
  await page.goto('/spaces')

  await expect(page.getByRole('heading', { name: '园区空间', exact: true })).toBeVisible({ timeout: 15000 })

  expect(pageErrors, `page errors: ${pageErrors.join('\n')}`).toEqual([])
  expect(consoleErrors, `console errors: ${consoleErrors.join('\n')}`).toEqual([])
})
