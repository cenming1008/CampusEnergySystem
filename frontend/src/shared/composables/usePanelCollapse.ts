import { ref, watch } from 'vue'

export function usePanelCollapse(storageKey: string, defaultCollapsed = false) {
  const collapsed = ref(readInitial())

  function readInitial(): boolean {
    try {
      const raw = localStorage.getItem(storageKey)
      if (raw === '1') return true
      if (raw === '0') return false
    } catch {
      // localStorage 不可用（隐私模式等）时回退默认值
    }
    return defaultCollapsed
  }

  watch(collapsed, (value) => {
    try {
      localStorage.setItem(storageKey, value ? '1' : '0')
    } catch {
      // 忽略写入失败
    }
  })

  function toggle() {
    collapsed.value = !collapsed.value
  }

  return { collapsed, toggle }
}
