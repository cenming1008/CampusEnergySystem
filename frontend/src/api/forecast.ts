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
  const params: any = { hours }
  if (deviceId) params.device_id = deviceId
  if (algorithm) params.algorithm = algorithm
  
  return request.post<any, ForecastResponse>('/forecast/load', null, { params })
}

// 风光预测
export function forecastRenewable(
  type: 'solar' | 'wind',
  deviceId?: number,
  hours: number = 24,
  algorithm?: string
) {
  const params: any = { hours }
  if (deviceId) params.device_id = deviceId
  if (algorithm) params.algorithm = algorithm
  
  return request.post<any, ForecastResponse>(`/forecast/renewable/${type}`, null, { params })
}

// 获取最新预测
export function getLatestForecast(
  type: PredictionType,
  deviceId?: number,
  limit: number = 24
) {
  const params: any = { limit }
  if (deviceId) params.device_id = deviceId
  
  return request.get<any, { predictions: any[], count: number }>(
    `/forecast/latest/${type}`,
    { params }
  )
}

// 训练LSTM模型
export function trainLSTMModel(data: TrainRequest) {
  return request.post<any, {
    status: string
    model_path: string
    train_loss: number
    val_loss: number
    epochs_trained: number
    multivariate: boolean
    version?: string
  }>('/forecast/lstm/train', data)
}

// 评估LSTM模型
export function evaluateLSTMModel(
  type: PredictionType,
  deviceId?: number,
  testDays: number = 7
) {
  const params: any = { test_days: testDays }
  if (deviceId) params.device_id = deviceId
  
  return request.get<any, {
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
  const params: any = {}
  if (deviceId) params.device_id = deviceId
  
  return request.get<any, {
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
  return request.post<any, {
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
  const params: any = { version1, version2 }
  if (deviceId) params.device_id = deviceId
  
  return request.get<any, {
    version1: any
    version2: any
    improvements: {
      mae?: number
      mape?: number
      rmse?: number
    }
  }>(`/forecast/lstm/versions/${type}/compare`, { params })
}

// 获取定时任务列表
export function getSchedulerJobs() {
  return request.get<any, {
    jobs: Array<{
      id: string
      name: string
      next_run_time: string | null
      trigger: string
    }>
    count: number
  }>('/forecast/scheduler/jobs')
}

// 超参数搜索
export function hyperparameterSearch(
  type: PredictionType,
  deviceId?: number,
  days: number = 60
) {
  return request.post<any, {
    best_params: TrainParams
    best_score: number
    all_results: Array<{
      params: TrainParams
      val_loss: number
      train_loss: number
      epochs_trained: number
    }>
    total_tested: number
  }>('/forecast/lstm/hyperparameter-search', {
    prediction_type: type,
    device_id: deviceId,
    days
  })
}
