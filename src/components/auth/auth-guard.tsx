'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuthStore } from '@/stores/auth-store'
import { FullPageLoading } from '@/components/ui/loading'

interface AuthGuardProps {
  children: React.ReactNode
}

// 不需要认证的路径
const publicPaths = ['/login', '/register']

/** 路由跳转超时时间（毫秒） */
const REDIRECT_TIMEOUT = 5000

/**
 * 认证守卫组件
 * 用于保护需要登录才能访问的页面
 *
 * 增强功能：
 * - 跳转状态追踪，避免重复跳转
 * - 超时保护，防止路由跳转失败导致永久卡住
 * - 路径变化检测，跳转成功后自动清除重定向状态
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { isAuthenticated, hasHydrated } = useAuthStore()
  
  // 跟踪重定向状态
  const [isRedirecting, setIsRedirecting] = useState(false)
  const [targetPath, setTargetPath] = useState<string | null>(null)
  const redirectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const prevPathnameRef = useRef<string>(pathname)

  // 清理超时定时器
  const clearRedirectTimeout = useCallback(() => {
    if (redirectTimeoutRef.current) {
      clearTimeout(redirectTimeoutRef.current)
      redirectTimeoutRef.current = null
    }
  }, [])

  // 执行安全跳转（带超时保护）
  const safeRedirect = useCallback((path: string) => {
    // 如果已经在目标路径，不需要跳转
    if (pathname === path) {
      return
    }

    // 如果已经在跳转到同一目标，不重复跳转
    if (isRedirecting && targetPath === path) {
      return
    }

    console.log(`[AuthGuard] 开始跳转: ${pathname} -> ${path}`)
    
    setIsRedirecting(true)
    setTargetPath(path)
    clearRedirectTimeout()

    // 尝试使用 Next.js router 跳转
    router.replace(path)

    // 设置超时保护：如果路由跳转失败，使用 window.location 强制跳转
    redirectTimeoutRef.current = setTimeout(() => {
      console.warn(`[AuthGuard] 路由跳转超时 (${REDIRECT_TIMEOUT}ms)，使用 window.location 强制跳转`)
      window.location.href = path
    }, REDIRECT_TIMEOUT)
  }, [pathname, isRedirecting, targetPath, router, clearRedirectTimeout])

  // 监听路径变化，检测跳转是否成功
  useEffect(() => {
    if (prevPathnameRef.current !== pathname) {
      console.log(`[AuthGuard] 路径变化: ${prevPathnameRef.current} -> ${pathname}`)
      prevPathnameRef.current = pathname
      
      // 路径已变化，跳转成功，清理状态
      if (isRedirecting) {
        clearRedirectTimeout()
        setIsRedirecting(false)
        setTargetPath(null)
      }
    }
  }, [pathname, isRedirecting, clearRedirectTimeout])

  // 主要的认证检查逻辑
  useEffect(() => {
    // 等待水合完成后再进行路由跳转
    if (!hasHydrated) return

    const isPublicPath = publicPaths.some((path) => pathname.startsWith(path))

    if (!isAuthenticated && !isPublicPath) {
      // 未登录且不是公开页面，跳转登录
      safeRedirect('/login')
    } else if (isAuthenticated && isPublicPath) {
      // 已登录且在公开页面，跳转仪表盘
      safeRedirect('/dashboard')
    }
  }, [isAuthenticated, hasHydrated, pathname, safeRedirect])

  // 组件卸载时清理定时器
  useEffect(() => {
    return () => {
      clearRedirectTimeout()
    }
  }, [clearRedirectTimeout])

  // 水合未完成时，显示加载状态
  if (!hasHydrated) {
    return <FullPageLoading />
  }

  // 正在跳转时，显示加载状态
  if (isRedirecting) {
    return <FullPageLoading />
  }

  // 检查中显示加载（作为后备保护）
  const isPublicPath = publicPaths.some((path) => pathname.startsWith(path))
  if (!isAuthenticated && !isPublicPath) {
    return <FullPageLoading />
  }

  return <>{children}</>
}
