import request from '@/utils/request'

interface SuccessResponse<T> {
  success: boolean
  data: T
  message?: string
  code?: string
}

export interface CleanupResult {
  status: string
  total_deleted: number
  energy_data: number
  alarm_data: number
  carbon_emission: number
  errors: string[]
  timestamp?: string
  cutoff_time?: string
  hours?: number
}

/**
 * 清理指定小时数之前的数据
 * @param hours 清理多少小时之前的数据（1-24小时）
 */
export async function cleanupData(hours: number = 1) {
  return request
    .post<never, SuccessResponse<CleanupResult>>(`/data-cleanup/cleanup?hours=${hours}`)
    .then((response) => response.data)
}

/**
 * 获取数据统计信息
 */
export async function getCleanupStats() {
  return request
    .get<never, SuccessResponse<Record<string, unknown>>>('/data-cleanup/stats')
    .then((response) => response.data)
}

/**
 * 清除所有数据（危险操作）
 */
export async function cleanupAllData() {
  return request
    .post<never, SuccessResponse<CleanupResult>>('/data-cleanup/cleanup-all')
    .then((response) => response.data)
}
