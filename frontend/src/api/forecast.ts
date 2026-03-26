import request from '@/utils/request'

// 预测类型
export type PredictionType = 'load' | 'solar' | 'wind'

// 预测结果
export interface ForecastPoint {
  forecast_time: string
  predicted_value: number
  confidence?: number
}

// 预测响应
export interface ForecastResponse {
  device_id?: number
  predictions: ForecastPoint[]
  forecast_hours: number
  algorithm: string
  count: number
}

export interface ForecastHistoryPoint extends ForecastPoint {
  id?: number
  actual_value?: number | null
  created_at?: string
}

export interface ForecastAccuracy {
  prediction_type: PredictionType
  device_id?: number
  total_predictions: number
  matched_actuals: number
  accuracy_rate: number
  mae?: number | null
  mape?: number | null
  rmse?: number | null
}

interface ForecastListItem {
  forecast_time: string
  predicted_value: number
  confidence?: number
}

interface SchedulerJob {
  id: string
  name: string
  next_run_time: string | null
  trigger: string
}

// 模型版本信息
export interface ModelVersion {
  version: string
  prediction_type: string
  device_id?: number
  model_path: string
  metadata_path: string
  metrics: {
    mae?: number
    mape?: number
    rmse?: number
    train_loss?: number
    val_loss?: number
  }
  created_at: string
  is_active: boolean
}

export interface VersionComparison {
  version1: ModelVersion
  version2: ModelVersion
  improvements: {
    mae?: number
    mape?: number
    rmse?: number
  }
}

// 训练参数
export interface TrainParams {
  sequence_length?: number
  lstm_units?: number[]
  dropout_rate?: number
  epochs?: number
  batch_size?: number
  validation_split?: number
  patience?: number
}

export interface HyperparameterSearchResult {
  best_params: TrainParams | null
  best_score: number
  all_results: Array<{
    params: TrainParams
    val_loss: number
    train_loss: number
    epochs_trained: number
  }>
  total_tested: number
}

// 训练请求
export interface TrainRequest {
  prediction_type: PredictionType
  device_id?: number
  days?: number
  params?: TrainParams
  retrain?: boolean
  use_multivariate?: boolean
  version?: string
}

// 负荷预测
export function forecastLoad(deviceId?: number, hours: number = 24, algorithm?: string) {
  const params: Record<string, string | number> = { hours }
  if (deviceId) params.device_id = deviceId
  if (algorithm) params.algorithm = algorithm
  
  return request.post<null, ForecastResponse>('/forecast/load', null, { params })
}

// 风光预测
export function forecastRenewable(
  type: 'solar' | 'wind',
  deviceId?: number,
  hours: number = 24,
  algorithm?: string
) {
  const params: Record<string, string | number> = { hours }
  if (deviceId) params.device_id = deviceId
  if (algorithm) params.algorithm = algorithm
  
  return request.post<null, ForecastResponse>(`/forecast/renewable/${type}`, null, { params })
}

// 获取最新预测
export function getLatestForecast(
  type: PredictionType,
  deviceId?: number,
  limit: number = 24
) {
  const params: Record<string, number> & { device_id?: number } = { limit }
  if (deviceId) params.device_id = deviceId
  
  return request.get<never, { predictions: ForecastListItem[]; count: number }>(
    `/forecast/latest/${type}`,
    { params }
  )
}

export function getForecastAccuracy(
  type: PredictionType,
  deviceId?: number,
  days: number = 7
) {
  const params: Record<string, number> & { device_id?: number } = { days }
  if (deviceId) params.device_id = deviceId

  return request
    .get<never, { success: boolean; data: ForecastAccuracy }>(`/forecast/accuracy/${type}`, { params })
    .then((response) => response.data)
}

export function getForecastHistory(
  type: PredictionType,
  params?: {
    device_id?: number
    start_time?: string
    end_time?: string
    limit?: number
  }
) {
  return request
    .get<never, { success: boolean; data: { predictions: ForecastHistoryPoint[]; count: number } }>(
      `/forecast/history/${type}`,
      { params }
    )
    .then((response) => response.data)
}

// 训练LSTM模型
export function trainLSTMModel(data: TrainRequest) {
  return request.post<TrainRequest, {
    status: string
    model_path: string
    train_loss: number
    val_loss: number
    epochs_trained: number
    multivariate: boolean
    version?: string
  }>('/forecast/lstm/train', data, { timeout: 900000 })
}

// 评估LSTM模型
export function evaluateLSTMModel(
  type: PredictionType,
  deviceId?: number,
  testDays: number = 7
) {
  const params: Record<string, number> & { device_id?: number } = { test_days: testDays }
  if (deviceId) params.device_id = deviceId
  
  return request.get<never, {
    mae: number
    mape: number
    rmse: number
    test_samples: number
  }>(`/forecast/lstm/evaluate/${type}`, { params })
}

// 获取模型版本列表
export function getModelVersions(
  type: PredictionType,
  deviceId?: number
) {
  const params: { device_id?: number } = {}
  if (deviceId) params.device_id = deviceId
  
  return request.get<never, {
    versions: ModelVersion[]
    count: number
  }>(`/forecast/lstm/versions/${type}`, { params })
}

// 激活模型版本
export function activateModelVersion(
  type: PredictionType,
  version: string,
  deviceId?: number
) {
  return request.post<{ version: string; device_id?: number }, {
    version: string
    is_active: boolean
  }>(`/forecast/lstm/versions/${type}/activate`, {
    version,
    device_id: deviceId
  })
}

// 对比模型版本
export function compareModelVersions(
  type: PredictionType,
  version1: string,
  version2: string,
  deviceId?: number
) {
  const params: { version1: string; version2: string; device_id?: number } = { version1, version2 }
  if (deviceId) params.device_id = deviceId
  
  return request
    .get<never, { success: boolean; data: VersionComparison }>(`/forecast/lstm/versions/${type}/compare`, { params })
    .then((response) => response.data)
}

// 获取定时任务列表
export function getSchedulerJobs() {
  return request.get<never, {
    jobs: SchedulerJob[]
    count: number
  }>('/forecast/scheduler/jobs')
}

// 超参数搜索
export function hyperparameterSearch(
  type: PredictionType,
  deviceId?: number,
  days: number = 60
) {
  return request
    .post<
      { prediction_type: PredictionType; device_id?: number; days: number },
      { success: boolean; data: HyperparameterSearchResult }
    >('/forecast/lstm/hyperparameter-search', {
      prediction_type: type,
      device_id: deviceId,
      days
    }, { timeout: 900000 })
    .then((response) => response.data)
}
