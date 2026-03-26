export interface SuccessResponse<T> {
  success: boolean
  data: T
  message?: string
  code?: string
}

export interface WrappedResponse<T> extends SuccessResponse<T> {}

export type JsonObject = Record<string, unknown>
