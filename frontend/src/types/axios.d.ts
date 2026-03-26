import 'axios'

declare module 'axios' {
  interface AxiosRequestConfig<D = unknown> {
    silent?: boolean
    skipAuthRefresh?: boolean
    _retry?: boolean
  }

  interface InternalAxiosRequestConfig<D = unknown> {
    silent?: boolean
    skipAuthRefresh?: boolean
    _retry?: boolean
  }
}
