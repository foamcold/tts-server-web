'use client'

import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { Icons } from './icons'

interface LoadingProps {
  className?: string
  size?: 'sm' | 'md' | 'lg'
  text?: string
}

const sizeMap = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
}

/**
 * 加载指示器组件
 */
export function Loading({ className, size = 'md', text }: LoadingProps) {
  return (
    <div className={cn('flex items-center justify-center gap-2', className)}>
      <Icons.spinner className={cn('animate-spin', sizeMap[size])} />
      {text && <span className="text-muted-foreground">{text}</span>}
    </div>
  )
}

/**
 * 页面加载组件
 * 用于页面内容加载时的占位显示
 */
export function PageLoading() {
  return (
    <div className="flex h-[50vh] items-center justify-center">
      <Loading size="lg" text="加载中..." />
    </div>
  )
}

/** 全屏加载超时提示时间（毫秒） */
const LOADING_TIMEOUT_HINT = 10000

interface FullPageLoadingProps {
  /** 超时提示时间（毫秒），默认 10 秒 */
  timeoutMs?: number
  /** 是否显示超时提示，默认 true */
  showTimeoutHint?: boolean
}

/**
 * 全屏加载组件
 * 用于全局操作时的遮罩加载
 *
 * 增强功能：
 * - 超时提示：长时间加载后显示刷新建议
 * - 刷新按钮：用户可手动刷新页面恢复
 */
export function FullPageLoading({
  timeoutMs = LOADING_TIMEOUT_HINT,
  showTimeoutHint = true
}: FullPageLoadingProps = {}) {
  const [showTimeout, setShowTimeout] = useState(false)

  useEffect(() => {
    if (!showTimeoutHint) return

    const timer = setTimeout(() => {
      setShowTimeout(true)
      console.warn(`[FullPageLoading] 加载超过 ${timeoutMs}ms，显示超时提示`)
    }, timeoutMs)

    return () => clearTimeout(timer)
  }, [timeoutMs, showTimeoutHint])

  // 刷新页面
  const handleRefresh = () => {
    window.location.reload()
  }

  // 返回首页
  const handleGoHome = () => {
    window.location.href = '/'
  }

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm">
      <Loading size="lg" text="加载中..." />
      
      {showTimeout && (
        <div className="mt-6 flex flex-col items-center text-sm text-muted-foreground animate-in fade-in duration-300">
          <p className="mb-3">加载时间较长，您可以尝试：</p>
          <div className="flex gap-3">
            <button
              onClick={handleRefresh}
              className="px-4 py-2 text-primary hover:text-primary/80 underline underline-offset-4 transition-colors"
            >
              刷新页面
            </button>
            <button
              onClick={handleGoHome}
              className="px-4 py-2 text-muted-foreground hover:text-foreground underline underline-offset-4 transition-colors"
            >
              返回首页
            </button>
          </div>
        </div>
      )}
    </div>
  )
}