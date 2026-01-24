import request from '@/utils/request'

/**
 * 清理指定小时数之前的数据
 * @param hours 清理多少小时之前的数据（1-24小时）
 */
export async function cleanupData(hours: number = 1) {
  return request.post(`/data-cleanup/cleanup?hours=${hours}`)
}

/**
 * 获取数据统计信息
 */
export async function getCleanupStats() {
  return request.get('/data-cleanup/stats')
}

/**
 * 清除所有数据（危险操作）
 */
export async function cleanupAllData() {
  return request.post('/data-cleanup/cleanup-all')
}
