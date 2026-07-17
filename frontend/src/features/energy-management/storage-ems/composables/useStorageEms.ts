import { computed, ref } from 'vue'
import {
  generateStorageDispatchPlan,
  getStorageEnergyOverview,
  getStorageStrategyComparison,
  type StorageEnergyOverview,
  type StorageDispatchGenerationResult,
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
  const generationResult = ref<StorageDispatchGenerationResult | null>(null)
  const overviewLoading = ref(false)
  const comparisonLoading = ref(false)
  const generationLoading = ref(false)
  const overviewError = ref<string | null>(null)
  const comparisonError = ref<string | null>(null)
  const generationError = ref<string | null>(null)
  const loading = computed(() => (
    overviewLoading.value || comparisonLoading.value || generationLoading.value
  ))
  const error = computed(() => (
    generationError.value || overviewError.value || comparisonError.value
  ))
  let refreshRequestToken = 0
  let comparisonRequestToken = 0

  async function refresh() {
    const requestToken = ++refreshRequestToken
    overviewLoading.value = true
    overviewError.value = null
    try {
      const result = await getStorageEnergyOverview()
      if (requestToken !== refreshRequestToken) return false
      overview.value = result
      return true
    } catch (reason) {
      if (requestToken !== refreshRequestToken) return false
      overviewError.value = toErrorMessage(reason)
      return false
    } finally {
      if (requestToken === refreshRequestToken) {
        overviewLoading.value = false
      }
    }
  }

  async function generatePlan(deviceId: number) {
    generationLoading.value = true
    generationError.value = null
    generationResult.value = null
    try {
      const result = await generateStorageDispatchPlan(deviceId, {
        dispatch_date: localDate(),
        scenario_key: scenario.value,
        seed: seed.value,
        initial_soc: initialSoc.value,
      })
      generationResult.value = result
      const successfulStatus = ['success', 'optimal'].includes(result.status.toLowerCase())
      if (!successfulStatus || result.failure_reason != null) {
        generationError.value = result.failure_reason
          || `调度计划生成失败（${result.status || 'unknown'}）`
        return false
      }
      return await refresh()
    } catch (reason) {
      generationError.value = toErrorMessage(reason)
      return false
    } finally {
      generationLoading.value = false
    }
  }

  async function compareStrategies() {
    const requestToken = ++comparisonRequestToken
    const params = {
      scenario_key: scenario.value,
      seed: seed.value,
      initial_soc: initialSoc.value,
      device_id: overview.value?.storage_device_ids[0],
    }
    comparisonLoading.value = true
    comparisonError.value = null
    comparison.value = null
    try {
      const result = await getStorageStrategyComparison(params)
      if (requestToken !== comparisonRequestToken) return false
      comparison.value = result
      return true
    } catch (reason) {
      if (requestToken !== comparisonRequestToken) return false
      comparisonError.value = toErrorMessage(reason)
      return false
    } finally {
      if (requestToken === comparisonRequestToken) {
        comparisonLoading.value = false
      }
    }
  }

  return {
    scenario,
    seed,
    initialSoc,
    overview,
    comparison,
    generationResult,
    loading,
    error,
    overviewLoading,
    comparisonLoading,
    generationLoading,
    overviewError,
    comparisonError,
    generationError,
    refresh,
    generatePlan,
    compareStrategies,
  }
}
