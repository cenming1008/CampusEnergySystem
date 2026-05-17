import { describe, expect, it, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { usePanelCollapse } from '../usePanelCollapse'

describe('usePanelCollapse', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('无存储记录时取默认值', () => {
    expect(usePanelCollapse('k:a', true).collapsed.value).toBe(true)
    expect(usePanelCollapse('k:b', false).collapsed.value).toBe(false)
  })

  it('读取已存储的折叠状态，覆盖默认值', () => {
    localStorage.setItem('k:c', '1')
    expect(usePanelCollapse('k:c', false).collapsed.value).toBe(true)
    localStorage.setItem('k:d', '0')
    expect(usePanelCollapse('k:d', true).collapsed.value).toBe(false)
  })

  it('toggle 翻转状态并写入 localStorage', async () => {
    const panel = usePanelCollapse('k:e', false)
    panel.toggle()
    await nextTick()
    expect(panel.collapsed.value).toBe(true)
    expect(localStorage.getItem('k:e')).toBe('1')
    panel.toggle()
    await nextTick()
    expect(localStorage.getItem('k:e')).toBe('0')
  })
})
