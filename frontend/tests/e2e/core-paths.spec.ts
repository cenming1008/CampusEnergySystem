import { expect, test } from '@playwright/test'

const sessionPayload = {
  access_token: 'e2e-access-token',
  refresh_token: 'e2e-refresh-token',
  token_type: 'bearer',
  role: 'admin',
  must_change_password: false,
}

async function stubWebSocket(page: Parameters<typeof test>[0]['page']) {
  await page.addInitScript(() => {
    class FakeWebSocket {
      static CONNECTING = 0
      static OPEN = 1
      static CLOSING = 2
      static CLOSED = 3

      readyState = FakeWebSocket.OPEN
      url: string
      onopen: ((event: Event) => void) | null = null
      onmessage: ((event: MessageEvent) => void) | null = null
      onerror: ((event: Event) => void) | null = null
      onclose: ((event: CloseEvent) => void) | null = null

      constructor(url: string) {
        this.url = url
        setTimeout(() => {
          this.onopen?.(new Event('open'))
        }, 0)
      }

      send() {}

      close() {
        this.readyState = FakeWebSocket.CLOSED
        this.onclose?.(new CloseEvent('close', { code: 1000, reason: 'test-close' }))
      }
    }

    Object.defineProperty(window, 'WebSocket', {
      configurable: true,
      writable: true,
      value: FakeWebSocket,
    })
  })
}

async function mockAuthenticatedApis(page: Parameters<typeof test>[0]['page']) {
  await page.route('**/users/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'ok',
        code: 'SUCCESS',
        data: {
          id: 1,
          username: 'admin',
          role: 'admin',
          location_scope: null,
          is_active: true,
          must_change_password: false,
          failed_login_attempts: 0,
          locked_until: null,
        },
      }),
    })
  })

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

  await page.route('**/alarms/', async (route) => {
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

  await page.route('**/analysis/*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        device_id: 1,
        is_active: true,
        current_power: 64.2,
        voltage: 220,
        current: 8.6,
        today_energy: 256.4,
        today_cost: 128.2,
      }),
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

test('unauthenticated user is redirected to login when opening dashboard', async ({ page }) => {
  await stubWebSocket(page)
  await page.goto('/dashboard')
  await expect(page).toHaveURL(/\/login(\?redirect=%2Fdashboard|\?redirect=\/dashboard)?$/)
  await expect(page.getByRole('heading', { name: '登录系统' })).toBeVisible()
})

test('authenticated user can open report center and export csv', async ({ page }) => {
  await stubWebSocket(page)
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
