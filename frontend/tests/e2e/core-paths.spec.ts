import { expect, test } from '@playwright/test'

const sessionPayload = {
  access_token: 'e2e-access-token',
  refresh_token: 'e2e-refresh-token',
  token_type: 'bearer',
  role: 'admin',
  must_change_password: false,
}

async function mockAuthenticatedApis(page: Parameters<typeof test>[0]['page']) {
  await page.route('**/devices/', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 1,
          name: '一号设备',
          sn: 'SN-001',
          device_type: 'meter',
          energy_type: 'electricity',
          is_active: true,
          location: '一采区',
        },
      ]),
    })
  })

  await page.route('**/alarms/active', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    })
  })

  await page.route('**/energy/statistics**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        electricity: { total_consumption: 123.4 },
        water: { total_consumption: 0 },
        gas: { total_consumption: 0 },
        heat: { total_consumption: 0 },
        cooling: { total_consumption: 0 },
      }),
    })
  })

  await page.route('**/devices/*/data**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    })
  })

  await page.route('**/reports/export_csv**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'text/csv',
      body: '时间,设备ID,设备名称\n2026-03-26 12:00:00,1,一号设备\n',
    })
  })
}

test('login redirects to dashboard on success', async ({ page }) => {
  await page.route('**/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(sessionPayload),
    })
  })
  await mockAuthenticatedApis(page)

  await page.goto('/login')
  await page.fill('#username', 'admin')
  await page.fill('#password', 'StrongPassword!123')
  await page.getByRole('button', { name: '建立连接' }).click()

  await expect(page).toHaveURL(/\/dashboard$/)
  await expect(page.getByText('驾驶舱首页', { exact: true })).toBeVisible()
})

test('authenticated user can open report center and export csv', async ({ page }) => {
  await page.addInitScript(({ session }) => {
    window.localStorage.setItem('access_token', session.access_token)
    window.localStorage.setItem('refresh_token', session.refresh_token)
    window.localStorage.setItem('username', 'admin')
    window.localStorage.setItem('user_role', session.role)
    window.localStorage.setItem('must_change_password', 'false')
  }, { session: sessionPayload })
  await mockAuthenticatedApis(page)

  const downloadPromise = page.waitForEvent('download')
  await page.goto('/report')
  await expect(page.getByRole('heading', { name: '多类型报表导出' })).toBeVisible()
  await page.getByRole('button', { name: '导出 CSV 报表' }).click()
  const download = await downloadPromise
  await expect(download.suggestedFilename()).toContain('.csv')
})
