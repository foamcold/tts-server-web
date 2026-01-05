'use client'

import { useMutation, useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { request } from '@/lib/api'
import { useAuthStore } from '@/stores/auth-store'
import { toast } from 'sonner'

// 类型定义
interface LoginRequest {
  username: string
  password: string
}

interface RegisterRequest {
  username: string
  password: string
}

interface AuthResponse {
  access_token: string
  token_type: string
  user: {
    id: number
    username: string
    is_admin: boolean
    created_at: string
  }
}

interface UserInfo {
  id: number
  username: string
  is_admin: boolean
  created_at: string
}

/**
 * 登录 Hook
 * 处理用户登录逻辑
 */
export function useLogin() {
  const router = useRouter()
  const { setAuth } = useAuthStore()

  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      // 使用 JSON 格式发送登录请求
      return request<AuthResponse>({
        method: 'POST',
        url: '/auth/login',
        data,
      })
    },
    onSuccess: (data) => {
      // 登录成功时，先清除旧的查询缓存，确保新账号看到的是新鲜数据
      if (typeof window !== 'undefined' && (window as any).queryClient) {
        (window as any).queryClient.clear()
      }
      setAuth(data.user, data.access_token)
      toast.success('登录成功')
      router.push('/dashboard')
    },
    onError: (error: Error) => {
      toast.error(error.message || '登录失败')
    },
  })
}

/**
 * 注册 Hook
 * 处理用户注册逻辑
 */
export function useRegister() {
  const router = useRouter()

  return useMutation({
    mutationFn: async (data: RegisterRequest) => {
      return request<{ message: string }>({
        method: 'POST',
        url: '/auth/register',
        data,
      })
    },
    onSuccess: () => {
      toast.success('注册成功，请登录')
      router.push('/login')
    },
    onError: (error: Error) => {
      toast.error(error.message || '注册失败')
    },
  })
}

/**
 * 获取当前用户信息Hook
 */
export function useCurrentUser() {
  const { isAuthenticated, setUser } = useAuthStore()

  return useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const user = await request<UserInfo>({ url: '/auth/me' })
      // 确保 store 中的用户信息与后端同步
      if (user) {
        setUser({
          id: user.id,
          username: user.username,
          is_admin: user.is_admin,
          created_at: user.created_at,
        })
      }
      return user
    },
    enabled: isAuthenticated,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5分钟
  })
}

/**
 * 修改密码 Hook
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: async (data: { old_password: string; new_password: string }) => {
      return request<{ message: string }>({
        method: 'POST',
        url: '/auth/change-password',
        data,
      })
    },
    onSuccess: () => {
      toast.success('密码修改成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '密码修改失败')
    },
  })
}
