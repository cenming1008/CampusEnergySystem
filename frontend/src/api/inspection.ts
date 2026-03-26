import request from '@/utils/request'
import type { SuccessResponse } from '@/types/api'

// ==================== 类型定义 ====================

export interface InspectionRoute {
  id?: number
  name: string
  code?: string
  description?: string
  estimated_duration: number
  device_count: number
  is_active: boolean
  created_at?: string
}

export interface InspectionPoint {
  id?: number
  route_id: number
  device_id?: number
  name: string
  location?: string
  sequence: number
  check_items?: string | string[]
  qr_code?: string
  is_required: boolean
  is_active: boolean
}

export interface InspectionPlan {
  id?: number
  route_id: number
  name: string
  plan_type: string
  start_date: string
  end_date?: string
  execution_time: string
  assigned_to?: string
  department?: string
  is_active: boolean
}

export interface InspectionTask {
  id?: number
  plan_id?: number
  route_id: number
  task_no: string
  task_date: string
  status: string
  inspector?: string
  start_time?: string
  end_time?: string
  duration_minutes?: number
  total_points: number
  completed_points: number
  abnormal_count: number
  remark?: string
}

export interface InspectionRecord {
  id?: number
  task_id: number
  point_id: number
  device_id?: number
  result: string
  check_time: string
  check_details?: string
  meter_reading?: number
  abnormal_description?: string
  abnormal_level?: string
  images?: string
  is_handled: boolean
  inspector?: string
}

export interface InspectionStatistics {
  period: {
    start_date: string
    end_date: string
  }
  tasks: {
    total: number
    completed: number
    pending: number
    overdue: number
    completion_rate: number
  }
  points: {
    total: number
    completed: number
    completion_rate: number
  }
  abnormal: {
    count: number
    rate: number
  }
}

interface InspectionMutationResult {
  success?: boolean
  message?: string
}

// ==================== 巡检路线 API ====================

export function getRoutes(is_active?: boolean, offset?: number, limit?: number) {
  return request.get<never, InspectionRoute[]>('/inspection/routes', {
    params: { is_active, offset, limit }
  })
}

export function createRoute(data: Partial<InspectionRoute>) {
  return request.post<Partial<InspectionRoute>, InspectionRoute>('/inspection/routes', data)
}

export function getRoute(id: number) {
  return request.get<never, InspectionRoute>(`/inspection/routes/${id}`)
}

export function updateRoute(id: number, data: Partial<InspectionRoute>) {
  return request.put<Partial<InspectionRoute>, InspectionRoute>(`/inspection/routes/${id}`, data)
}

export function deleteRoute(id: number, force: boolean = false) {
  return request.delete<never, InspectionMutationResult>(`/inspection/routes/${id}`, {
    params: { force }
  })
}

export function getRoutePoints(routeId: number) {
  return request.get<never, InspectionPoint[]>(`/inspection/routes/${routeId}/points`)
}

// ==================== 巡检点 API ====================

export function createPoint(data: Partial<InspectionPoint>) {
  return request.post<Partial<InspectionPoint>, InspectionPoint>('/inspection/points', data)
}

export function updatePoint(id: number, data: Partial<InspectionPoint>) {
  return request.put<Partial<InspectionPoint>, InspectionPoint>(`/inspection/points/${id}`, data)
}

export function deletePoint(id: number) {
  return request.delete<never, InspectionMutationResult>(`/inspection/points/${id}`)
}

// ==================== 巡检计划 API ====================

export function getPlans(is_active?: boolean, offset?: number, limit?: number) {
  return request.get<never, InspectionPlan[]>('/inspection/plans', {
    params: { is_active, offset, limit }
  })
}

export function createPlan(data: Partial<InspectionPlan>) {
  return request.post<Partial<InspectionPlan>, InspectionPlan>('/inspection/plans', data)
}

export function getPlan(id: number) {
  return request.get<never, InspectionPlan>(`/inspection/plans/${id}`)
}

export function updatePlan(id: number, data: Partial<InspectionPlan>) {
  return request.put<Partial<InspectionPlan>, InspectionPlan>(`/inspection/plans/${id}`, data)
}

export function deletePlan(id: number, force: boolean = false) {
  return request.delete<never, InspectionMutationResult>(`/inspection/plans/${id}`, {
    params: { force }
  })
}

// ==================== 巡检任务 API ====================

export function getTasks(params?: {
  status?: string
  inspector?: string
  start_date?: string
  end_date?: string
  limit?: number
}) {
  return request.get<never, InspectionTask[]>('/inspection/tasks', { params })
}

export function getTodayTasks() {
  return request.get<never, InspectionTask[]>('/inspection/tasks/today')
}

export function getPendingTasks(limit: number = 10) {
  return request.get<never, InspectionTask[]>('/inspection/tasks/pending', {
    params: { limit }
  })
}

export function createTask(data: {
  route_id: number
  task_date?: string
  plan_id?: number
  inspector?: string
}) {
  return request.post<typeof data, InspectionTask>('/inspection/tasks', data)
}

export function getTask(id: number) {
  return request.get<never, InspectionTask>(`/inspection/tasks/${id}`)
}

export function startTask(id: number, inspector?: string) {
  return request.post<never, InspectionTask>(`/inspection/tasks/${id}/start`, null, {
    params: { inspector }
  })
}

export function completeTask(id: number, remark?: string) {
  return request.post<never, InspectionTask>(`/inspection/tasks/${id}/complete`, null, {
    params: { remark }
  })
}

export function getTaskRecords(taskId: number) {
  return request.get<never, InspectionRecord[]>(`/inspection/tasks/${taskId}/records`)
}

// ==================== 巡检记录 API ====================

export function submitRecord(data: {
  task_id: number
  point_id: number
  result: string
  check_details?: object
  meter_reading?: number
  abnormal_description?: string
  abnormal_level?: string
  images?: string[]
  inspector?: string
}) {
  return request.post<typeof data, InspectionRecord>('/inspection/records', data)
}

// ==================== 统计 API ====================

export function getStatistics(params?: {
  start_date?: string
  end_date?: string
}) {
  return request
    .get<never, SuccessResponse<InspectionStatistics>>('/inspection/statistics', { params })
    .then((response) => response.data)
}
