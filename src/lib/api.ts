import axios, { AxiosError } from 'axios'
import { useAuthStore } from '@/stores/auth-store'

// 是否正在跳转登录页，防止重复跳转
let isRedirecting = false

// 创建 Axios 实例
export const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use((config) => {
  // 从 localStorage 获取token
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token 过期，清除状态
      if (typeof window !== 'undefined') {
        // 使用 store 的 logout 方法，确保状态同步
        useAuthStore.getState().logout()
        
        // 避免重复跳转和 401 请求风暴
        if (!isRedirecting && !window.location.pathname.startsWith('/login')) {
          isRedirecting = true
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// API 类型定义
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  detail: string
}

// 通用请求函数
export async function request<T>(config: Parameters<typeof api.request>[0]): Promise<T> {
  try {
    const response = await api.request<T>(config)
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data) {
      throw new Error((error.response.data as ApiError).detail || '请求失败')
    }
    throw error
  }
}