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
 * 获取个人资料
 *使用现有的 /auth/me 接口
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