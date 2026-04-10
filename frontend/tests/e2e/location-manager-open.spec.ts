import { expect, test } from '@playwright/test'

test.skip(!!process.env.CI, 'Location manager e2e still depends on a fuller mocked runtime; keep PR CI focused on stable smoke paths.')

const sessionPayload = {
  access_token: 'e2e-access-token',
  refresh_token: 'e2e-refresh-token',
  token_type: 'bearer',
  role: 'admin',
  must_change_password: false,
}

const rootLocation = {
  id: 1,
  name: '园区 A',
  location_type: 'park',
  parent_id: null,
  full_path: '/园区 A',
  level: 1,
  code: 'PARK-A',
  description: '主园区',
  area_sqm: 12000,
  manager: '张三',
  contact: '13800000000',
  is_active: true,
  created_at: '2026-04-01T08:00:00',
  updated_at: '2026-04-01T08:00:00',
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

async function mockLocationManagerApis(page: Parameters<typeof test>[0]['page']) {
  await page.addInitScript(({ session }) => {
    window.localStorage.setItem('access_token', session.access_token)
    window.localStorage.setItem('refresh_token', session.refresh_token)
    window.localStorage.setItem('username', 'admin')
    window.localStorage.setItem('user_role', session.role)
    window.localStorage.setItem('must_change_password', 'false')
  }, { session: sessionPayload })

  await page.route('**/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(sessionPayload),
    })
  })

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

  await page.route('**/locations/', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([rootLocation]),
    })
  })

  await page.route('**/locations/types', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'ok',
        code: 'SUCCESS',
        data: [
          { value: 'park', label: '园区', description: '园区级空间' },
          { value: 'building', label: '楼栋', description: '楼栋级空间' },
        ],
      }),
    })
  })

  await page.route('**/locations/roots', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([rootLocation]),
    })
  })

  await page.route('**/locations/tree**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'ok',
        code: 'SUCCESS',
        data: [{ ...rootLocation, children: [], device_count: 1 }],
      }),
    })
  })

  await page.route('**/locations/1', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(rootLocation),
    })
  })

  await page.route('**/locations/1/devices**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 1,
          name: '一号电表',
          sn: 'SN-001',
          device_type: 'meter',
          energy_type: 'electricity',
          is_active: true,
          location: '园区 A',
        },
      ]),
    })
  })

  await page.route('**/locations/1/statistics**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'ok',
        code: 'SUCCESS',
        data: {
          location: {
            id: 1,
            name: '园区 A',
            location_type: 'park',
            full_path: '/园区 A',
            level: 1,
          },
          device_count: {
            total: 1,
            active: 1,
            by_energy_type: { electricity: 1 },
            by_category: { meter: 1 },
          },
          child_locations_count: 0,
          area_sqm: 12000,
          manager: '张三',
        },
      }),
    })
  })

  await page.route('**/locations/1/children**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    })
  })

  await page.route('**/campus/overview', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        campus_entities: [{ id: 1, name: '园区 A', location_type: 'park' }],
        hierarchy_summary: {
          location_counts: { park: 1, building: 0 },
          device_count: 1,
          active_device_count: 1,
          meter_count: 1,
        },
        analysis_summary: {
          time_window: { start_time: '2026-04-10T00:00:00', end_time: '2026-04-10T23:59:59' },
          total_consumption: 128.5,
          realtime_load: 64.2,
          active_alarm_count: 0,
          device_count: 1,
          meter_count: 1,
          building_count: 0,
          estimated_carbon: 12.6,
        },
        energy_category_summary: [],
        subitem_statistics: [],
        location_rankings: { areas: [], buildings: [] },
        realtime_load_trend: [],
        alarm_summary: {
          total_count: 0,
          unresolved_count: 0,
          resolved_count: 0,
          by_severity: {},
          top_locations: [],
          latest: [],
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
          name: '一号电表',
          sn: 'SN-001',
          device_type: 'meter',
          energy_type: 'electricity',
          is_active: true,
          location: '园区 A',
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
}

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

  await stubWebSocket(page)
  await mockLocationManagerApis(page)
  await page.goto('/login')
  await page.locator('#username').fill('admin')
  await page.locator('#password').fill('123456')
  await page.getByRole('button', { name: /进入园区 EMS|登录中/ }).click()

  await page.waitForURL(/\/dashboard$/, { timeout: 15000 })
  await page.waitForLoadState('networkidle')
  await page.getByRole('menuitem', { name: '园区空间' }).click({ force: true })
  await page.waitForURL(/\/spaces$/, { timeout: 15000 })

  await expect(page.getByRole('heading', { name: '园区空间', exact: true })).toBeVisible({ timeout: 15000 })

  expect(pageErrors, `page errors: ${pageErrors.join('\n')}`).toEqual([])
  expect(consoleErrors, `console errors: ${consoleErrors.join('\n')}`).toEqual([])
})
