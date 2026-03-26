import { onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAlarms, resolveAllAlarms, type Alarm } from '@/api/alarm'

interface UseAlarmPollingOptions {
  interval?: number
  autoStart?: boolean
}

export function useAlarmPolling(options: UseAlarmPollingOptions = {}) {
  const { interval = 5000, autoStart = true } = options

  const alarmCount = ref(0)
  const alarmList = ref<Alarm[]>([])
  const loading = ref(false)
  let pollTimer: ReturnType<typeof setInterval> | null = null

  const fetchAlarms = async () => {
    loading.value = true

    try {
      const alarms = await getAlarms()
      alarmList.value = alarms
      alarmCount.value = alarms.length
    } catch {
      alarmList.value = []
      alarmCount.value = 0
    } finally {
      loading.value = false
    }
  }

  const clearAlarms = async () => {
    try {
      const response = await resolveAllAlarms()
      const message = response?.message || `已解决 ${response?.data?.count || 0} 条报警`
      ElMessage.success(message)
      await fetchAlarms()
    } catch (error) {
      ElMessage.error('操作失败')
    }
  }

  const startPolling = () => {
    if (pollTimer) return

    fetchAlarms()
    pollTimer = setInterval(fetchAlarms, interval)
  }

  const stopPolling = () => {
    if (!pollTimer) return

    clearInterval(pollTimer)
    pollTimer = null
  }

  onMounted(() => {
    if (autoStart) {
      startPolling()
    }
  })

  onUnmounted(() => {
    stopPolling()
  })

  return {
    alarmCount,
    alarmList,
    loading,
    fetchAlarms,
    clearAlarms,
    startPolling,
    stopPolling
  }
}
