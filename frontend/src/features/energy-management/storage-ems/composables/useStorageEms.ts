import { ref } from 'vue'
import {
  generateStorageDispatchPlan,
  getStorageEnergyOverview,
  getStorageStrategyComparison,
  type StorageEnergyOverview,
  type StorageScenarioKey,
  type StorageStrategyComparisonResult,
} from '@/api/storageEnergy'

function toErrorMessage(reason: unknown): string {
  return reason instanceof Error && reason.message
    ? reason.message
    : '光储 EMS 数据加载失败'
}

function localDate(): string {
  const date = new Date()
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function useStorageEms() {
  const scenario = ref<StorageScenarioKey>('sunny_workday')
  const seed = ref(20260716)
  const initialSoc = ref(50)
  const overview = ref<StorageEnergyOverview | null>(null)
  const comparison = ref<StorageStrategyComparisonResult | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function refresh() {
    loading.value = true
    error.value = null
    try {
      overview.value = await getStorageEnergyOverview()
    } catch (reason) {
      error.value = toErrorMessage(reason)
    } finally {
      loading.value = false
    }
  }

  async function generatePlan(deviceId: number) {
    loading.value = true
    error.value = null
    try {
      await generateStorageDispatchPlan(deviceId, {
        dispatch_date: localDate(),
        scenario_key: scenario.value,
        seed: seed.value,
        initial_soc: initialSoc.value,
      })
      await refresh()
    } catch (reason) {
      error.value = toErrorMessage(reason)
      loading.value = false
    }
  }

  async function compareStrategies() {
    loading.value = true
    error.value = null
    try {
      comparison.value = await getStorageStrategyComparison({
        scenario_key: scenario.value,
        seed: seed.value,
        initial_soc: initialSoc.value,
        device_id: overview.value?.storage_device_ids[0],
      })
    } catch (reason) {
      error.value = toErrorMessage(reason)
    } finally {
      loading.value = false
    }
  }

  return {
    scenario,
    seed,
    initialSoc,
    overview,
    comparison,
    loading,
    error,
    refresh,
    generatePlan,
    compareStrategies,
  }
}
