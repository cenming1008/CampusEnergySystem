import { expect, test } from '@playwright/test'

function buildWrappedResponse<T>(data: T) {
  return {
    success: true,
    message: 'ok',
    code: 'SUCCESS',
    data,
  }
}

async function stubAuthenticatedSession(page: Parameters<typeof test>[0]['page']) {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-access-token')
    localStorage.setItem('refresh_token', 'e2e-refresh-token')
    localStorage.setItem('username', 'admin')
    localStorage.setItem('user_role', 'admin')
    localStorage.setItem('must_change_password', 'false')

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
        setTimeout(() => this.onopen?.(new Event('open')), 0)
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

async function mockDeviceMonitorApis(page: Parameters<typeof test>[0]['page']) {
  await page.route('**/users/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(buildWrappedResponse({
        id: 1,
        username: 'admin',
        role: 'admin',
        location_scope: null,
        is_active: true,
        must_change_password: false,
        failed_login_attempts: 0,
        locked_until: null,
      })),
    })
  })

  await page.route('**/devices/2/monitor/overview', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(buildWrappedResponse({
        archive: {
          id: 2,
          name: '设备-CAP-001',
          sn: 'CAP-001',
          device_type: 'capacitor_bank_controller',
          device_subtype: 'capacitor_bank_controller',
          device_category: 'compensation',
          energy_type: 'electricity',
          location: '111',
          unit: 'kW',
          rated_capacity: 100,
        },
        runtime_status: {
          device_id: 2,
          code: 'running',
          label: '运行中',
          is_active: true,
          is_online: true,
          unresolved_alarm_count: 0,
          last_message_at: '2026-04-22T10:07:37',
          last_success_at: '2026-04-22T10:07:37',
        },
        realtime: {
          device_id: 2,
          timestamp: '2026-04-22T10:07:37',
          flow_rate: 59,
          voltage: 220.5,
          current: 84.57,
          power_factor: 0.9034,
          reactive_power: -28,
          temperature: 41.2,
        },
        ingestion_health: {},
        recent_alarms: [],
        recent_control_logs: [],
      })),
    })
  })

  await page.route('**/devices/2/monitor/realtime', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(buildWrappedResponse({
        device_id: 2,
        timestamp: '2026-04-22T10:07:37',
        flow_rate: 59,
        voltage: 220.5,
        current: 84.57,
        power_factor: 0.9034,
        reactive_power: -28,
        temperature: 41.2,
      })),
    })
  })

  await page.route('**/devices/2/monitor/trend**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(buildWrappedResponse({
        device_id: 2,
        start_time: '2026-04-22T09:07:47',
        end_time: '2026-04-22T10:07:47',
        points: [
          {
            timestamp: '2026-04-22T09:10:00',
            reactive_power: -20,
            power_factor: 0.92,
            voltage: 221,
            current: 80,
          },
          {
            timestamp: '2026-04-22T10:07:37',
            reactive_power: -28,
            power_factor: 0.9034,
            voltage: 220.5,
            current: 84.57,
          },
        ],
        summary: { latest: 59, peak: 65, valley: 54, average: 58.3 },
      })),
    })
  })

  await page.route('**/devices/2/monitor/alarms**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(buildWrappedResponse({ items: [] })),
    })
  })

  await page.route('**/devices/2/monitor/control-logs**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(buildWrappedResponse({ items: [] })),
    })
  })

  await page.route('**/devices/2/monitor/status-history**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(buildWrappedResponse({ items: [] })),
    })
  })

  await page.route('**/devices/2/compensation/capacitor-bank/telemetry/latest', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        device_id: 2,
        timestamp: '2026-04-22T10:07:37',
        temperature: 41.2,
        frequency: 49.98,
        circuit_state_phase_a: 1,
        circuit_state_phase_b: 2,
        circuit_state_phase_c: 2,
        circuit_state_common_1: 5,
      }),
    })
  })

  await page.route('**/devices/2/compensation/capacitor-bank/telemetry**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          device_id: 2,
          timestamp: '2026-04-22T09:10:00',
          temperature: 40.5,
          frequency: 49.98,
          circuit_state_phase_a: 1,
          circuit_state_phase_b: 2,
          circuit_state_phase_c: 2,
          circuit_state_common_1: 5,
        },
        {
          device_id: 2,
          timestamp: '2026-04-22T10:07:37',
          temperature: 41.2,
          frequency: 49.98,
          circuit_state_phase_a: 1,
          circuit_state_phase_b: 2,
          circuit_state_phase_c: 2,
          circuit_state_common_1: 5,
        },
      ]),
    })
  })

  await page.route('**/devices/2/compensation/capacitor-bank/control-profile', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        device_id: 2,
        source_status: 'fresh',
        is_stale: false,
        source: 'telemetry',
        snapshot_timestamp: '2026-04-22T10:07:00',
        terminal_assignment_scheme: '自动模式',
        split_capacity_expansion: { phase_a_groups: [], phase_b_groups: [], phase_c_groups: [] },
        common_capacity_expansion: { common_1_groups: [], common_2_groups: [], common_3_groups: [] },
        capabilities: {
          supports_read: true,
          supports_write: true,
          supports_remote_control: true,
          write_status_message: '',
          remote_control_status_message: '',
          protocol_version: 'campus-control.v1',
          command_message_type: 'control_command',
          receipt_message_type: 'control_receipt',
          control_topic_template: 'campus/control/{device_code}',
          receipt_topic: 'campus/telemetry',
          receipt_timeout_seconds: 120,
          supported_results: ['accepted', 'running', 'success', 'failed', 'timeout', 'rejected'],
        },
      }),
    })
  })

  await page.route('**/frontend-errors', async (route) => {
    await route.fulfill({ status: 204, body: '' })
  })
}

test('device monitor stays rendered after browser refresh', async ({ page }) => {
  await stubAuthenticatedSession(page)
  await mockDeviceMonitorApis(page)

  const pageErrors: string[] = []
  page.on('pageerror', (error) => {
    pageErrors.push(error.message)
  })

  await page.goto('/devices/2/monitor')
  await expect(page.getByText('历史趋势')).toBeVisible()

  await page.reload()

  await expect(page.getByText('历史趋势')).toBeVisible()
  expect(pageErrors).toEqual([])
})
