'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Icons } from '@/components/ui/icons'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import {
  type UpstreamSettings,
  useUpdateUpstreamSettings,
  useUpstreamSettings,
} from '@/hooks/use-settings'

const upstreamSettingsSchema = z.object({
  connection_mode: z.enum(['concurrent', 'queue', 'replace']),
  timeout_seconds: z.number().min(1).max(300),
  retry_count: z.number().min(0).max(5),
})

type UpstreamSettingsFormData = z.infer<typeof upstreamSettingsSchema>

const connectionModeOptions = [
  {
    value: 'concurrent',
    label: '直接并发',
    description: '同一插件的多个请求会直接并发请求上游。',
  },
  {
    value: 'queue',
    label: '同插件顺序处理',
    description: '同一插件按顺序排队，必须等上一个请求完整返回后才会处理下一个。',
  },
  {
    value: 'replace',
    label: '新请求替换旧请求',
    description: '同一插件来了新请求后会取消旧请求，旧请求不会返回半段音频。',
  },
] as const

export function UpstreamSettingsForm() {
  const { data: settings, isLoading } = useUpstreamSettings()
  const updateSettings = useUpdateUpstreamSettings()

  const {
    handleSubmit,
    register,
    reset,
    setValue,
    watch,
    formState: { errors, isDirty },
  } = useForm<UpstreamSettingsFormData>({
    resolver: zodResolver(upstreamSettingsSchema),
    defaultValues: {
      connection_mode: 'concurrent',
      timeout_seconds: 30,
      retry_count: 1,
    },
  })

  const connectionMode = watch('connection_mode')
  const currentMode = connectionModeOptions.find((item) => item.value === connectionMode)

  useEffect(() => {
    if (settings) {
      reset(settings)
    }
  }, [settings, reset])

  const onSubmit = (data: UpstreamSettingsFormData) => {
    updateSettings.mutate(data as UpstreamSettings)
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>上游连接</CardTitle>
          <CardDescription>配置插件请求上游服务时的连接策略与容错行为。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="h-10 rounded bg-muted animate-pulse" />
          <div className="h-10 rounded bg-muted animate-pulse" />
          <div className="h-10 rounded bg-muted animate-pulse" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icons.zap className="h-5 w-5" />
          上游连接
        </CardTitle>
        <CardDescription>
          配置与上游 TTS 服务的连接策略与容错行为。策略按插件维度生效，不同插件之间互不影响。
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="connection_mode">连接方式</Label>
            <Select
              value={connectionMode}
              onValueChange={(value) => setValue('connection_mode', value as UpstreamSettingsFormData['connection_mode'], { shouldDirty: true })}
            >
              <SelectTrigger id="connection_mode">
                <SelectValue placeholder="请选择连接方式" />
              </SelectTrigger>
              <SelectContent>
                {connectionModeOptions.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              {currentMode?.description}
            </p>
            {errors.connection_mode && (
              <p className="text-sm text-destructive">{errors.connection_mode.message}</p>
            )}
          </div>

          <Separator />

          <div className="space-y-2">
            <Label htmlFor="timeout_seconds">连接超时（秒）</Label>
            <Input
              id="timeout_seconds"
              type="number"
              min={1}
              max={300}
              {...register('timeout_seconds', { valueAsNumber: true })}
            />
            <p className="text-sm text-muted-foreground">
              单次上游请求允许的最长耗时。超时后会按下方重试次数重试；只在拿到完整音频后才会返回结果。
            </p>
            {errors.timeout_seconds && (
              <p className="text-sm text-destructive">{errors.timeout_seconds.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="retry_count">失败重试次数</Label>
            <Input
              id="retry_count"
              type="number"
              min={0}
              max={5}
              {...register('retry_count', { valueAsNumber: true })}
            />
            <p className="text-sm text-muted-foreground">
              仅对超时、连接失败、429 和 5xx 这类可恢复错误重试，不会对插件参数错误或上游明确拒绝的请求重试。
            </p>
            {errors.retry_count && (
              <p className="text-sm text-destructive">{errors.retry_count.message}</p>
            )}
          </div>

          <div className="rounded-lg border bg-muted/30 p-4 text-sm text-muted-foreground">
            <p>说明：</p>
            <p>1. 排队与替换旧请求都是“按插件维度”处理。</p>
            <p>2. 替换旧请求时，旧请求会被服务端取消，不会返回半段音频。</p>
            <p>3. 当前规则面向非流式合成；如果后续接入流式接口，再单独处理流式中断语义。</p>
          </div>

          <Button type="submit" disabled={!isDirty || updateSettings.isPending}>
            {updateSettings.isPending && <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />}
            保存设置
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
