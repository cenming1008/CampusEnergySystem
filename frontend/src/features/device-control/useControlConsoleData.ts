import { computed, onBeforeUnmount, onMounted, ref, watch, type ComputedRef } from 'vue'
import {
  getDeviceMonitorControlLogs,
  getDeviceMonitorOverview,
  type MonitorOverview,
} from '@/api/deviceMonitor'
import {
  getCompensationCapacitorBankControlProfile,
  type CompensationCapacitorBankControlProfile,
  type CompensationCapacitorBankControlCapabilities,
} from '@/api/compensation'
import { resolveCompensationSubtype } from '@/shared/compensationDevices'
import { extractControlConsoleErrorMessage } from '@/features/device-control/controlConsoleUtils'

const REFRESH_INTERVAL_IDLE_MS = 5000
const REFRESH_INTERVAL_PENDING_MS = 2000

function buildDegradedCapabilities(): CompensationCapacitorBankControlCapabilities {
  return {
    supports_read: true,
    supports_write: false,
    supports_remote_control: true,
    write_status_message: '参数档案接口暂时不可用，当前已切换为降级视图并锁定参数写入。',
    remote_control_status_message: '参数档案接口暂时不可用，远程控制仍可继续使用。',
    protocol_version: 'campus-control.v1',
    command_message_type: 'control_command',
    receipt_message_type: 'control_receipt',
    control_topic_template: 'campus/control/{device_code}',
    receipt_topic: 'campus/telemetry',
    receipt_timeout_seconds: 120,
    supported_results: ['accepted', 'running', 'success', 'failed', 'timeout', 'rejected'],
  }
}

function buildDegradedControlProfile(deviceId: number): CompensationCapacitorBankControlProfile {
  return {
    device_id: deviceId,
    source_status: 'unknown',
    is_stale: false,
    split_capacity_expansion: {
      phase_a_groups: [],
      phase_b_groups: [],
      phase_c_groups: [],
    },
    common_capacity_expansion: {
      common_1_groups: [],
      common_2_groups: [],
      common_3_groups: [],
    },
    capabilities: buildDegradedCapabilities(),
  }
}

export function useControlConsoleData(input: {
  deviceId: ComputedRef<number>
  enableLifecycle?: boolean
}) {
  const loading = ref(false)
  const overview = ref<MonitorOverview | null>(null)
  const controlProfile = ref<CompensationCapacitorBankControlProfile | null>(null)
  const controlLogs = ref<Awaited<ReturnType<typeof getDeviceMonitorControlLogs>>['items']>([])
  const loadError = ref('')
  const profileWarning = ref('')
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
    profileWarning.value = ''
    try {
      const overviewResponse = await getDeviceMonitorOverview(input.deviceId.value)
      overview.value = overviewResponse
      const resolvedSubtype = resolveCompensationSubtype(
        overviewResponse.archive?.device_type,
        overviewResponse.archive?.device_subtype,
      )
      if (resolvedSubtype !== 'capacitor_bank_controller') {
        loadError.value = '当前设备不是电容补偿控制器，暂不支持进入控制台。'
        controlProfile.value = null
        controlLogs.value = []
        return
      }

      const logs = await getDeviceMonitorControlLogs(input.deviceId.value, { limit: 10, hours: 168 })
      controlLogs.value = logs.items

      try {
        controlProfile.value = await getCompensationCapacitorBankControlProfile(input.deviceId.value)
      } catch (error) {
        controlProfile.value = buildDegradedControlProfile(input.deviceId.value)
        profileWarning.value = extractControlConsoleErrorMessage(
          error,
          '参数档案暂时不可用，当前已切换为降级视图：参数快照与参数写入区域会被锁定，但概览、日志和远程控制仍可继续使用。',
        )
      }
    } catch (error) {
      controlProfile.value = null
      controlLogs.value = []
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
    profileWarning,
    archive,
    runtimeStatus,
    compensationSubtype,
    isCapacitorBankController,
    controlCapabilities,
    loadPage,
  }
}
