import { computed, onBeforeUnmount, onMounted, ref, watch, type ComputedRef } from 'vue'
import {
  getDeviceMonitorControlLogs,
  getDeviceMonitorOverview,
  type MonitorOverview,
} from '@/api/deviceMonitor'
import {
  getCompensationCapacitorBankControlProfile,
  type CompensationCapacitorBankControlProfile,
} from '@/api/compensation'
import { resolveCompensationSubtype } from '@/shared/compensationDevices'
import { extractControlConsoleErrorMessage } from '@/features/device-control/controlConsoleUtils'

const REFRESH_INTERVAL_IDLE_MS = 5000
const REFRESH_INTERVAL_PENDING_MS = 2000

export function useControlConsoleData(input: {
  deviceId: ComputedRef<number>
  enableLifecycle?: boolean
}) {
  const loading = ref(false)
  const overview = ref<MonitorOverview | null>(null)
  const controlProfile = ref<CompensationCapacitorBankControlProfile | null>(null)
  const controlLogs = ref<Awaited<ReturnType<typeof getDeviceMonitorControlLogs>>['items']>([])
  const loadError = ref('')
  let refreshTimer: ReturnType<typeof setInterval> | null = null
  let currentInterval = REFRESH_INTERVAL_IDLE_MS

  function hasPendingLogs() {
    return controlLogs.value.some((log) => log.result === 'accepted' || log.result === 'running')
  }

  function scheduleRefresh() {
    if (refreshTimer) clearInterval(refreshTimer)
    const interval = hasPendingLogs() ? REFRESH_INTERVAL_PENDING_MS : REFRESH_INTERVAL_IDLE_MS
    currentInterval = interval
    refreshTimer = setInterval(() => {
      void loadPage().then(() => {
        const next = hasPendingLogs() ? REFRESH_INTERVAL_PENDING_MS : REFRESH_INTERVAL_IDLE_MS
        if (next !== currentInterval) scheduleRefresh()
      })
    }, interval)
  }

  const archive = computed(() => overview.value?.archive)
  const runtimeStatus = computed(() => overview.value?.runtime_status)
  const compensationSubtype = computed(() => resolveCompensationSubtype(
    archive.value?.device_type,
    archive.value?.device_subtype,
  ) || '')
  const isCapacitorBankController = computed(() => compensationSubtype.value === 'capacitor_bank_controller')
  const controlCapabilities = computed(() => controlProfile.value?.capabilities)

  async function loadPage() {
    if (!input.deviceId.value) return
    loading.value = true
    loadError.value = ''
    try {
      const [overviewResponse, profileResponse] = await Promise.all([
        getDeviceMonitorOverview(input.deviceId.value),
        getCompensationCapacitorBankControlProfile(input.deviceId.value),
      ])
      overview.value = overviewResponse
      controlProfile.value = profileResponse
      const logs = await getDeviceMonitorControlLogs(input.deviceId.value, { limit: 10, hours: 168 })
      controlLogs.value = logs.items
      if (resolveCompensationSubtype(
        overviewResponse.archive?.device_type,
        overviewResponse.archive?.device_subtype,
      ) !== 'capacitor_bank_controller') {
        loadError.value = '当前设备不是电容补偿控制器，暂不支持进入控制台。'
      }
    } catch (error) {
      loadError.value = extractControlConsoleErrorMessage(error, '控制台数据加载失败，请稍后重试。')
    } finally {
      loading.value = false
    }
  }

  watch(() => input.deviceId.value, () => {
    void loadPage()
  })

  if (input.enableLifecycle !== false) {
    onMounted(() => {
      void loadPage().then(scheduleRefresh)
    })

    onBeforeUnmount(() => {
      if (refreshTimer) clearInterval(refreshTimer)
    })
  }

  return {
    loading,
    overview,
    controlProfile,
    controlLogs,
    loadError,
    archive,
    runtimeStatus,
    compensationSubtype,
    isCapacitorBankController,
    controlCapabilities,
    loadPage,
  }
}
