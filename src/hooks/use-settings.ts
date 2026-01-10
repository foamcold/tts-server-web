'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { request } from '@/lib/api'
import { toast } from 'sonner'

/**
 * 用户资料接口
 */
export interface UserProfile {
  id: number
  username: string
  is_admin: boolean
  created_at: string
}

/**
 * 更新资料数据
 */
export interface UpdateProfileData {
  username?: string
}

/**
 * 修改密码数据
 */
export interface ChangePasswordData {
  old_password: string
  new_password: string
}

/**
 * 系统信息接口
 */
export interface SystemInfo {
  app_name: string
  version: string
  python_version: string
  os: string
  uptime: number
  tts_configs_count: number
  plugins_count: number
  replace_rules_count: number
  speech_rules_count: number
}

/**
 * 健康检查接口
 */
export interface HealthStatus {
  status: string
  database: string
  timestamp: string
}

/**
 * 缓存设置接口
 */
export interface CacheSettings {
  cache_audio_enabled: boolean
  cache_audio_max_age_days: number
  cache_audio_max_count: number
}

/**
 * 缓存统计接口
 */
export interface CacheStats {
  enabled: boolean
  total_count: number
  total_size_bytes: number
  total_size_mb: number
  total_hits: number
  oldest_cache_date: string | null
  newest_cache_date: string | null
  max_age_days: number
  max_count: number
}

/**
 * 缓存清理响应
 */
export interface CacheCleanupResponse {
  deleted_count: number
  deleted_size_bytes: number
  remaining_count: number
  message: string
}

/**
 * 缓存清空响应
 */
export interface CacheClearResponse {
  deleted_count: number
  deleted_size_bytes: number
  message: string
}

/**
 * 获取个人资料
 * 使用现有的 /auth/me 接口
 */
export function useProfile() {
  return useQuery({
    queryKey: ['profile'],
    queryFn: () => request<UserProfile>({ url: '/auth/me' }),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  })
}

/**
 * 更新个人资料
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateProfileData) =>
      request<UserProfile>({ method: 'PUT', url: '/auth/profile', data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      queryClient.invalidateQueries({ queryKey: ['currentUser'] })
      toast.success('资料更新成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新失败')
    },
  })
}

/**
 * 修改密码
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: (data: ChangePasswordData) =>
      request<{ message: string }>({
        method: 'POST',
        url: '/auth/change-password',
        data,
      }),
    onSuccess: () => {
      toast.success('密码修改成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '密码修改失败')
    },
  })
}

/**
 * 获取系统信息
 */
export function useSystemInfo() {
  return useQuery({
    queryKey: ['systemInfo'],
    queryFn: () => request<SystemInfo>({ url: '/info' }),
    staleTime: 30 * 1000, // 30秒缓存
  })
}

/**
 * 获取健康状态
 */
export function useHealthStatus() {
  return useQuery({
    queryKey: ['healthStatus'],
    queryFn: () => request<HealthStatus>({ url: '/health' }),
    staleTime: 10 * 1000, // 10秒缓存refetchInterval: 30 * 1000, // 每30秒自动刷新
  })
}

/**
 * 获取缓存设置
 */
export function useCacheSettings() {
  return useQuery({
    queryKey: ['cacheSettings'],
    queryFn: () => request<CacheSettings>({ url: '/settings/cache' }),
    staleTime: 60 * 1000, // 1分钟缓存
  })
}

/**
 * 更新缓存设置
 */
export function useUpdateCacheSettings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CacheSettings) =>
      request<CacheSettings>({ method: 'PUT', url: '/settings/cache', data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cacheSettings'] })
      queryClient.invalidateQueries({ queryKey: ['cacheStats'] })
      toast.success('缓存设置已更新')
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新失败')
    },
  })
}

/**
 * 获取缓存统计
 */
export function useCacheStats() {
  return useQuery({
    queryKey: ['cacheStats'],
    queryFn: () => request<CacheStats>({ url: '/cache/stats' }),
    staleTime: 30 * 1000, // 30秒缓存
    refetchInterval: 60 * 1000, // 每分钟自动刷新
  })
}

/**
 * 清理缓存
 */
export function useCleanupCache() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () =>
      request<CacheCleanupResponse>({ method: 'POST', url: '/cache/cleanup' }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['cacheStats'] })
      toast.success(data.message)
    },
    onError: (error: Error) => {
      toast.error(error.message || '清理失败')
    },
  })
}

/**
 * 清空所有缓存
 */
export function useClearCache() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () =>
      request<CacheClearResponse>({ method: 'DELETE', url: '/cache' }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['cacheStats'] })
      toast.success(data.message)
    },
    onError: (error: Error) => {
      toast.error(error.message || '清空失败')
    },
  })
}

/**
 * 格式化运行时间
 * @param seconds 秒数
 * @returns 格式化的时间字符串
 */
export function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  const parts: string[] = []
  if (days > 0) parts.push(`${days}天`)
  if (hours > 0) parts.push(`${hours}小时`)
  if (minutes > 0) parts.push(`${minutes}分钟`)
  if (secs > 0 || parts.length === 0) parts.push(`${secs}秒`)

  return parts.join(' ')
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化的大小字符串
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}