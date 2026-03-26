import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useAuthStore } from '../useAuthStore'
import { useSocketStore } from '../useSocketStore'

const { notificationMock } = vi.hoisted(() => ({
  notificationMock: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElNotification: notificationMock,
}))

class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3
  static instances: MockWebSocket[] = []

  readyState = MockWebSocket.CONNECTING
  url: string
  onopen: (() => void) | null = null
  onerror: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: ((event: { code: number }) => void) | null = null

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  close(code = 1000) {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.({ code })
  }
}

describe('useSocketStore', () => {
  beforeEach(() => {
    localStorage.clear()
    notificationMock.mockReset()
    MockWebSocket.instances = []
    setActivePinia(createPinia())
    vi.stubGlobal('WebSocket', MockWebSocket)
  })

  it('allows reconnect after a manual disconnect', () => {
    const authStore = useAuthStore()
    const socketStore = useSocketStore()
    authStore.token = 'token-1'

    socketStore.connect()
    expect(MockWebSocket.instances).toHaveLength(1)
    expect(MockWebSocket.instances[0].url).toContain('access_token=token-1')

    socketStore.disconnect()
    expect(socketStore.isConnected).toBe(false)

    socketStore.connect()
    expect(MockWebSocket.instances).toHaveLength(2)
    expect(MockWebSocket.instances[1].url).toContain('access_token=token-1')
  })
})
