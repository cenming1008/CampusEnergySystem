// 导出 CSV 的 URL
export const REPORT_EXPORT_URL = '/api/reports/export_csv'

/**
 * 触发下载
 * 这种二进制文件流下载，通常直接用 window.open 或动态创建 a 标签
 * 如果需要带 Token，则比较麻烦，需要用 axios download，
 * 但目前的后端 /export_csv 接口如果加了锁，这里就需要特殊处理。
 * 假设目前该接口需要 Token：
 */
import request from '@/utils/request'

export function downloadReport() {
  return request.get('/reports/export_csv', {
    responseType: 'blob' // 关键：指定响应类型为二进制流
  })
}