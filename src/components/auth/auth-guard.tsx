'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuthStore } from '@/stores/auth-store'
import { FullPageLoading } from '@/components/ui/loading'

interface AuthGuardProps {
  children: React.ReactNode
}

// 不需要认证的路径
const publicPaths = ['/login', '/register']

/**
 * 认证守卫组件
 * 用于保护需要登录才能访问的页面
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { isAuthenticated, hasHydrated } = useAuthStore()

  useEffect(() => {
    // 等待水合完成后再进行路由跳转
    if (!hasHydrated) return

    const isPublicPath = publicPaths.some((path) => pathname.startsWith(path))

    if (!isAuthenticated && !isPublicPath) {
      // 未登录且不是公开页面，跳转登录
      // 使用 replace 避免在历史记录中留下多余条目
      router.replace('/login')
    } else if (isAuthenticated && isPublicPath) {
      // 已登录且在公开页面，跳转仪表盘
      router.replace('/dashboard')
    }
  }, [isAuthenticated, hasHydrated, pathname, router])

  // 水合未完成时，显示加载状态
  if (!hasHydrated) {
    return <FullPageLoading />
  }

  // 检查中显示加载
  const isPublicPath = publicPaths.some((path) => pathname.startsWith(path))
  if (!isAuthenticated && !isPublicPath) {
    return<FullPageLoading />
  }

  return<>{children}</>
}
