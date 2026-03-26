import request from '@/utils/request'
import type { SuccessResponse } from '@/types/api'

export interface AuditEvent {
  id: number
  action: string
  actor: string
  target: string
  outcome: string
  actor_role?: string | null
  details: Record<string, unknown>
  created_at: string
}

export interface AuditSearchResponse {
  items: AuditEvent[]
  total: number
  offset: number
  limit: number
  has_more: boolean
  filters: Record<string, unknown>
}

export interface AuditSummaryResponse {
  window_hours: number
  total: number
  outcomes: Record<string, number>
  top_actions: Array<{ action: string; count: number }>
}

export function searchAuditEvents(params: Record<string, unknown>) {
  return request
    .get<never, SuccessResponse<AuditSearchResponse>>('/audit/events/search', { params })
    .then((response) => response.data)
}

export function getAuditSummary(hours = 24) {
  return request
    .get<never, SuccessResponse<AuditSummaryResponse>>('/audit/summary', {
      params: { hours }
    })
    .then((response) => response.data)
}
