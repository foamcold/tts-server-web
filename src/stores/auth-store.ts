import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { QueryClient } from '@tanstack/react-query'

/**
 * 用户信息接口
 */
interface User {
  id: number
  username: string
  is_admin: boolean
  created_at: string
}

/**
 * 认证状态接口
 */
interface AuthState {
  /** 当前用户信息 */
  user: User | null
  /** 认证令牌 */
  token: string | null
  /** 是否已认证 */
  isAuthenticated: boolean
  /** 是否已完成水合（从localStorage 读取状态） */
  hasHydrated: boolean
  /** 更新用户信息 */
  setUser: (user: User) => void
  /** 设置认证信息 */
  setAuth: (user: User, token: string) => void
  /** 退出登录 */
  logout: () => void
  /** 设置水合完成状态 */
  setHasHydrated: (state: boolean) => void
}

/**
 * 认证状态管理
 *使用 zustand 进行状态管理，并持久化到 localStorage
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      hasHydrated: false,
      setUser: (user) => {
        set({ user })
      },
      setAuth: (user, token) => {
        // 同时保存到 localStorage，方便 API 请求使用
        if (typeof window !== 'undefined') {
          localStorage.setItem('token', token)
        }
        set({ user, token, isAuthenticated: true })
      },
      logout: () => {
        // 清除 localStorage 中的令牌
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token')
          
          // 清除 React Query 缓存，防止切换账号后看到旧数据
          // 我们不能在这里直接使用 queryClient，因为它在 Providers 中定义
          // 但是可以通过全局窗口对象或者其他方式访问，或者在 logout 时触发一个事件
          // 最简单的方法是直接刷新页面，或者通过 window 暴露 queryClient
          if ((window as any).queryClient) {
            ((window as any).queryClient as QueryClient).clear()
          }
        }
        set({ user: null, token: null, isAuthenticated: false })
      },
      setHasHydrated: (state) => {
        set({ hasHydrated: state })
      },
    }),
    {
      name: 'auth-storage',
      onRehydrateStorage: () => (state) => {
        // 水合完成时设置标志
        state?.setHasHydrated(true)
      },
    }
  )
)
