import { ElMessage } from 'element-plus'
import { getCapacitorBankEditableParameterMeta } from '@/features/device-control/capacitorBankControlProfile'

export function formatWriteTargetValue(
  meta: NonNullable<ReturnType<typeof getCapacitorBankEditableParameterMeta>>,
  value: string | number | boolean,
) {
  if (typeof value === 'boolean') {
    return value ? '开启' : '关闭'
  }
  return meta.unit ? `${value} ${meta.unit}` : String(value)
}

export function normalizeWriteTargetValue(
  meta: NonNullable<ReturnType<typeof getCapacitorBankEditableParameterMeta>>,
  value: string | number | boolean | null,
) {
  if (meta.inputKind === 'boolean') {
    if (typeof value !== 'boolean') {
      return { value: null, message: `请确认 ${meta.label} 的开关状态` }
    }
    return { value, message: '' }
  }
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) {
      return { value: null, message: `请填写 ${meta.label}` }
    }
    return { value: trimmed, message: '' }
  }
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return { value: null, message: `请填写有效的 ${meta.label}` }
  }
  return { value, message: '' }
}

export function notifyInvalidWriteTarget(
  meta: NonNullable<ReturnType<typeof getCapacitorBankEditableParameterMeta>>,
  value: string | number | boolean | null,
) {
  const normalized = normalizeWriteTargetValue(meta, value)
  if (normalized.message) {
    ElMessage.warning(normalized.message)
  }
  return normalized.value
}

export function extractControlConsoleErrorMessage(error: unknown, fallback: string) {
  if (
    typeof error === 'object'
    && error
    && 'response' in error
    && typeof error.response === 'object'
    && error.response
    && 'data' in error.response
  ) {
    const responseData = error.response.data as { detail?: string; message?: string }
    if (typeof responseData.detail === 'string' && responseData.detail) return responseData.detail
    if (typeof responseData.message === 'string' && responseData.message) return responseData.message
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}

export function roleLabel(role: string) {
  if (role === 'admin') return '管理员'
  if (role === 'operator') return '操作员'
  if (role === 'maintainer') return '运维员'
  return '访客'
}
