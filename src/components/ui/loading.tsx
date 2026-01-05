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
 *用于页面内容加载时的占位显示
 */
export function PageLoading() {
  return (
    <div className="flex h-[50vh] items-center justify-center">
      <Loading size="lg" text="加载中..." />
    </div>
  )
}

/**
 * 全屏加载组件
 * 用于全局操作时的遮罩加载
 */
export function FullPageLoading() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <Loading size="lg" text="加载中..." />
    </div>
  )
}