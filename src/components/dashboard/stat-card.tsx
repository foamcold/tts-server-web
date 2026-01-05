/**
 * 统计卡片组件
 * 用于仪表盘显示各类统计数据
 */
import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

interface StatCardProps {
  /**卡片标题 */
  title: string
  /** 统计值 */
  value: string | number
  /** 描述信息 */
  description?: string
  /** 图标组件 */
  icon: LucideIcon
  /** 趋势信息 */
  trend?: {
    value: number
    isPositive: boolean
  }
  /** 是否加载中 */
  loading?: boolean
  /** 自定义类名 */
  className?: string
}

/**
 * 统计卡片组件
 * 展示统计数据，支持图标、趋势和加载状态
 */
export function StatCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  loading = false,
  className,
}: StatCardProps) {
  // 加载状态显示骨架屏
  if (loading) {
    return (
      <Card className={cn('', className)}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <Skeleton className="h-10 w-10 rounded-lg" />
            <Skeleton className="h-4 w-16" />
          </div>
          <div className="mt-4"><Skeleton className="h-8 w-24" />
            <Skeleton className="mt-2 h-4 w-32" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn('transition-shadow hover:shadow-md', className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          {/* 图标区域 */}
          <div className="rounded-lg bg-primary/10 p-2.5">
            <Icon className="h-5 w-5 text-primary" />
          </div>
          {/* 趋势信息 */}
          {trend && (
            <span
              className={cn(
                'text-sm font-medium',
                trend.isPositive ? 'text-green-600' : 'text-red-600'
              )}
            >
              {trend.isPositive ? '+' : ''}
              {trend.value}%
            </span>
          )}
        </div>
        {/* 数值和标题 */}
        <div className="mt-4">
          <p className="text-3xl font-bold">{value}</p>
          <p className="mt-1 text-sm text-muted-foreground">{title}</p>{description && (
            <p className="mt-2 text-xs text-muted-foreground">{description}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}