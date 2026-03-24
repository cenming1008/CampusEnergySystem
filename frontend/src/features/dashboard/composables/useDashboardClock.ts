import { onMounted, onUnmounted, ref } from 'vue'

export function useDashboardClock() {
  const currentTime = ref('')
  const currentDate = ref('')
  let timeTimer: ReturnType<typeof setInterval> | null = null

  const updateTime = () => {
    const now = new Date()
    currentTime.value = now.toLocaleTimeString('zh-CN', { hour12: false })
    currentDate.value = now.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      weekday: 'long'
    })
  }

  onMounted(() => {
    updateTime()
    timeTimer = setInterval(updateTime, 1000)
  })

  onUnmounted(() => {
    if (timeTimer) {
      clearInterval(timeTimer)
      timeTimer = null
    }
  })

  return {
    currentTime,
    currentDate,
    updateTime
  }
}
