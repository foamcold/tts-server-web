'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Icons } from '@/components/ui/icons'
import { Separator } from '@/components/ui/separator'
import {
  useCacheSettings,
  useUpdateCacheSettings,
  useCacheStats,
  useCleanupCache,
  useClearCache,
  formatFileSize,
  CacheSettings,
} from '@/hooks/use-settings'
import { formatDateTime } from '@/lib/utils'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { useState } from 'react'

// 表单验证 schema
const cacheSettingsSchema = z.object({
  cache_audio_enabled: z.boolean(),
  cache_audio_max_age_days: z.number().min(1).max(365),
  cache_audio_max_count: z.number().min(100).max(100000),
})

type CacheSettingsFormData = z.infer<typeof cacheSettingsSchema>

/**
 * 缓存设置表单组件
 * 管理音频缓存配置和统计信息
 */
export function CacheSettingsForm() {
  const { data: settings, isLoading: settingsLoading } = useCacheSettings()
  const { data: stats, isLoading: statsLoading } = useCacheStats()
  const updateSettings = useUpdateCacheSettings()
  const cleanupCache = useCleanupCache()
  const clearCache = useClearCache()

  const [showClearConfirm, setShowClearConfirm] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isDirty },
  } = useForm<CacheSettingsFormData>({
    resolver: zodResolver(cacheSettingsSchema),
    defaultValues: {
      cache_audio_enabled: true,
      cache_audio_max_age_days: 7,
      cache_audio_max_count: 1000,
    },
  })

  // 监听启用状态
  const isEnabled = watch('cache_audio_enabled')

  // 当settings数据加载完成后，重置表单值
  useEffect(() => {
    if (settings) {
      reset({
        cache_audio_enabled: settings.cache_audio_enabled,
        cache_audio_max_age_days: settings.cache_audio_max_age_days,
        cache_audio_max_count: settings.cache_audio_max_count,
      })
    }
  }, [settings, reset])

  // 提交表单
  const onSubmit = (data: CacheSettingsFormData) => {
    updateSettings.mutate(data as CacheSettings)
  }

  // 处理清空缓存
  const handleClearCache = () => {
    clearCache.mutate()
    setShowClearConfirm(false)
  }

  // 加载状态
  if (settingsLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>缓存设置</CardTitle>
          <CardDescription>管理音频缓存配置</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="animate-pulse space-y-4">
            <div className="h-10 bg-muted rounded" />
            <div className="h-10 bg-muted rounded" />
            <div className="h-10 bg-muted rounded" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* 缓存设置卡片 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Icons.database className="h-5 w-5" />
            缓存设置
          </CardTitle>
          <CardDescription>
            配置音频缓存策略，缓存可以加速重复文本的合成速度
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* 启用缓存开关 */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="cache_audio_enabled">启用音频缓存</Label>
                <p className="text-sm text-muted-foreground">
                  开启后，合成的音频将被缓存以加速后续相同请求
                </p>
              </div>
              <Switch
                id="cache_audio_enabled"
                checked={isEnabled}
                onCheckedChange={(checked) => setValue('cache_audio_enabled', checked, { shouldDirty: true })}
              />
            </div>

            <Separator />

            {/* 缓存时间设置 */}
            <div className="space-y-2">
              <Label htmlFor="cache_audio_max_age_days">
                缓存过期天数
              </Label>
              <div className="flex items-center gap-2">
                <Input
                  id="cache_audio_max_age_days"
                  type="number"
                  min={1}
                  max={365}
                  disabled={!isEnabled}
                  {...register('cache_audio_max_age_days', { valueAsNumber: true })}
                  className="w-32"
                />
                <span className="text-sm text-muted-foreground">天</span>
              </div>
              {errors.cache_audio_max_age_days && (
                <p className="text-sm text-destructive">
                  {errors.cache_audio_max_age_days.message || '请输入1-365之间的数字'}
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                超过此天数的缓存将被自动清理
              </p>
            </div>

            {/* 缓存数量设置 */}
            <div className="space-y-2">
              <Label htmlFor="cache_audio_max_count">
                最大缓存数量
              </Label>
              <div className="flex items-center gap-2">
                <Input
                  id="cache_audio_max_count"
                  type="number"
                  min={100}
                  max={100000}
                  disabled={!isEnabled}
                  {...register('cache_audio_max_count', { valueAsNumber: true })}
                  className="w-32"
                />
                <span className="text-sm text-muted-foreground">条</span>
              </div>
              {errors.cache_audio_max_count && (
                <p className="text-sm text-destructive">
                  {errors.cache_audio_max_count.message || '请输入100-100000之间的数字'}
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                超过此数量时，最早的缓存将被自动清理
              </p>
            </div>

            {/* 提交按钮 */}
            <Button
              type="submit"
              disabled={!isDirty || updateSettings.isPending}
            >
              {updateSettings.isPending && (
                <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
              )}
              保存设置
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* 缓存统计卡片 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Icons.barChart className="h-5 w-5" />
            缓存统计
          </CardTitle>
          <CardDescription>
            查看当前缓存使用情况
          </CardDescription>
        </CardHeader>
        <CardContent>
          {statsLoading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-20 bg-muted rounded" />
            </div>
          ) : stats ? (
            <div className="space-y-6">
              {/* 统计网格 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg border bg-card">
                  <div className="text-2xl font-bold">{stats.total_count}</div>
                  <div className="text-sm text-muted-foreground">缓存数量</div>
                </div>
                <div className="p-4 rounded-lg border bg-card">
                  <div className="text-2xl font-bold">
                    {stats.total_size_mb.toFixed(2)} MB
                  </div>
                  <div className="text-sm text-muted-foreground">占用空间</div>
                </div>
                <div className="p-4 rounded-lg border bg-card">
                  <div className="text-2xl font-bold">{stats.total_hits}</div>
                  <div className="text-sm text-muted-foreground">命中次数</div>
                </div>
                <div className="p-4 rounded-lg border bg-card">
                  <div className="text-2xl font-bold">
                    {stats.enabled ? '启用' : '禁用'}
                  </div>
                  <div className="text-sm text-muted-foreground">缓存状态</div>
                </div>
              </div>

              {/* 时间信息 */}
              {(stats.oldest_cache_date || stats.newest_cache_date) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  {stats.oldest_cache_date && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Icons.clock className="h-4 w-4" />
                      <span>最早缓存：{formatDateTime(stats.oldest_cache_date)}</span>
                    </div>
                  )}
                  {stats.newest_cache_date && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Icons.clock className="h-4 w-4" />
                      <span>最新缓存：{formatDateTime(stats.newest_cache_date)}</span>
                    </div>
                  )}
                </div>
              )}

              <Separator />

              {/* 操作按钮 */}
              <div className="flex flex-wrap gap-3">
                <Button
                  variant="outline"
                  onClick={() => cleanupCache.mutate()}
                  disabled={cleanupCache.isPending || stats.total_count === 0}
                >
                  {cleanupCache.isPending ? (
                    <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Icons.refresh className="mr-2 h-4 w-4" />
                  )}
                  清理过期缓存
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => setShowClearConfirm(true)}
                  disabled={clearCache.isPending || stats.total_count === 0}
                >
                  {clearCache.isPending ? (
                    <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Icons.trash className="mr-2 h-4 w-4" />
                  )}
                  清空所有缓存
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground">无法加载缓存统计信息</p>
          )}
        </CardContent>
      </Card>

      {/* 清空确认对话框 */}
      <ConfirmDialog
        open={showClearConfirm}
        onOpenChange={setShowClearConfirm}
        title="清空所有缓存"
        description={`确定要清空所有 ${stats?.total_count || 0} 条缓存吗？此操作无法撤销。`}
        confirmText="确认清空"
        cancelText="取消"
        variant="destructive"
        onConfirm={handleClearCache}
      />
    </div>
  )
}
