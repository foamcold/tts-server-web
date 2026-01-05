'use client'

/**
 * TTS 配置编辑对话框
 * 支持创建和编辑配置
 */
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Icons } from '@/components/ui/icons'
import { usePlugins, usePluginVoices, Plugin } from '@/hooks/use-synthesize'
import type { TtsConfig, TtsConfigCreate, TtsGroup } from '@/hooks/use-tts-configs'

// 声音信息类型
interface VoiceOption {
  code: string
  name: string
}

// 表单验证schema
const configSchema = z.object({
  name: z.string().min(1, '请输入配置名称').max(100, '名称不能超过100个字符'),
  source_type: z.enum(['plugin', 'local', 'http'], { required_error: '请选择来源类型' }),
  plugin_id: z.string().optional(),
  voice: z.string().min(1, '请选择声音'),
  voice_name: z.string().optional(),
  locale: z.string().default('zh-CN'),
  speed: z.number().min(0).max(100).default(50),
  volume: z.number().min(0).max(100).default(50),
  pitch: z.number().min(0).max(100).default(50),
  is_enabled: z.boolean().default(true),
})

type ConfigFormData = z.infer<typeof configSchema>

interface ConfigDialogProps {
  /** 对话框是否打开 */
  open: boolean
  /** 打开状态变更回调 */
  onOpenChange: (open: boolean) => void
  /** 编辑的配置（null表示创建新配置） */
  config?: TtsConfig | null
  /** 当前分组 */
  group: TtsGroup | null
  /** 保存回调 */
  onSave: (data: TtsConfigCreate) => void
  /** 是否正在加载 */
  loading?: boolean
}

export function ConfigDialog({
  open,
  onOpenChange,
  config,
  group,
  onSave,
  loading = false,
}: ConfigDialogProps) {
  // 获取插件列表
  const { data: plugins } = usePlugins()

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<ConfigFormData>({
    resolver: zodResolver(configSchema),
    defaultValues: {
      name: '',
      source_type: 'plugin',
      plugin_id: '',
      locale: 'zh-CN',
      voice: '',
      voice_name: '',
      speed: 50,
      volume: 50,
      pitch: 50,
      is_enabled: true,
    },
  })

  // 监听表单字段
  const sourceType = watch('source_type')
  const pluginId = watch('plugin_id')
  const locale = watch('locale')

  // 获取插件声音列表
  const selectedPlugin = plugins?.find((p: Plugin) => p.plugin_id === pluginId)
  const { data: pluginVoices } = usePluginVoices(selectedPlugin?.id)

  // 编辑时填充数据
  useEffect(() => {
    if (config) {
      reset({
        name: config.name,
        source_type: config.source_type as'plugin' | 'local' | 'http',
        plugin_id: config.plugin_id || '',
        voice: config.voice,
        voice_name: config.voice_name,
        locale: config.locale,
        speed: config.speed,
        volume: config.volume,
        pitch: config.pitch,
        is_enabled: config.is_enabled,
      })
    } else {
      reset({
        name: '',
        source_type: 'plugin',
        plugin_id: '',
        locale: 'zh-CN',
        voice: '',
        voice_name: '',
        speed: 50,
        volume: 50,
        pitch: 50,
        is_enabled: true,
      })
    }
  }, [config, reset])

  // 提交表单
  const onSubmit = (data: ConfigFormData) => {
    if (!group) return

    onSave({
      name: data.name,
      group_id: group.id,
      source_type: data.source_type,
      plugin_id: data.plugin_id || null,
      voice: data.voice,
      voice_name: data.voice_name || '',
      locale: data.locale,
      speed: data.speed,
      volume: data.volume,
      pitch: data.pitch,
      is_enabled: data.is_enabled,
    })
  }

  // 语言选项
  const localeOptions: string[] = pluginVoices?.locales || ['zh-CN', 'en-US']

  // 声音选项
  const voiceOptions: VoiceOption[] = pluginVoices?.voices[locale] || []

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {config ? '编辑配置' : '新建配置'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* 配置名称 */}
          <div className="space-y-2">
            <Label htmlFor="name">配置名称</Label>
            <Input
              id="name"
              placeholder="请输入配置名称"
              {...register('name')}
            />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>

          {/* 来源类型 */}
          <div className="space-y-2">
            <Label>来源类型</Label>
            <Select
              value={sourceType}
              onValueChange={(value: 'plugin' | 'local' | 'http') => {
                setValue('source_type', value)
                setValue('plugin_id', '')
                setValue('voice', '')
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择来源类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="plugin">插件</SelectItem>
                <SelectItem value="local">本地</SelectItem>
                <SelectItem value="http">HTTP</SelectItem>
              </SelectContent>
            </Select>
            {errors.source_type && (
              <p className="text-sm text-destructive">
                {errors.source_type.message}
              </p>
            )}
          </div>

          {/* 插件选择（仅当来源类型为 plugin 时显示） */}
          {sourceType === 'plugin' && (
            <div className="space-y-2">
              <Label>选择插件</Label>
              <Select
                value={pluginId}
                onValueChange={(value: string) => {
                  setValue('plugin_id', value)
                    setValue('voice', '')
                  setValue('voice_name', '')
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择插件" />
                </SelectTrigger>
                <SelectContent>
                  {plugins
                    ?.filter((p: Plugin) => p.is_enabled)
                    .map((p: Plugin) => (
                      <SelectItem key={p.plugin_id} value={p.plugin_id}>
                        {p.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* 语言区域 */}
          <div className="space-y-2">
            <Label>语言</Label>
            <Select
              value={locale}
              onValueChange={(value: string) => {
                setValue('locale', value)
                setValue('voice', '')
                setValue('voice_name', '')
              }}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {localeOptions.map((loc: string) => (
                  <SelectItem key={loc} value={loc}>
                    {loc}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* 声音选择*/}
          <div className="space-y-2">
            <Label>声音</Label>
            <Select
              value={watch('voice')}
              onValueChange={(value: string) => {
                setValue('voice', value)
                // 同时设置声音名称
                const voice = voiceOptions.find((v: VoiceOption) => v.code === value)
                if (voice) {
                  setValue('voice_name', voice.name)
                }
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择声音" />
              </SelectTrigger>
              <SelectContent>
                {voiceOptions.map((v: VoiceOption) => (
                  <SelectItem key={v.code} value={v.code}>
                    {v.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.voice && (
              <p className="text-sm text-destructive">
                {errors.voice.message}
              </p>
            )}
          </div>

          {/* 语速滑块 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>语速</Label>
              <span className="text-sm text-muted-foreground">
                {watch('speed')}%
              </span>
            </div>
            <Slider
              value={[watch('speed')]}
              min={0}
              max={100}
              step={1}
              onValueChange={([value]) => setValue('speed', value)}
            />
          </div>

          {/* 音量滑块 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>音量</Label>
              <span className="text-sm text-muted-foreground">
                {watch('volume')}%
              </span>
            </div>
            <Slider
              value={[watch('volume')]}
              min={0}
              max={100}
              step={1}
              onValueChange={([value]) => setValue('volume', value)}
            />
          </div>

          {/* 音调滑块 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>音调</Label>
              <span className="text-sm text-muted-foreground">
                {watch('pitch')}%
              </span>
            </div>
            <Slider
              value={[watch('pitch')]}
              min={0}
              max={100}
              step={1}
              onValueChange={([value]) => setValue('pitch', value)}
            />
          </div>

          {/* 启用开关 */}
          <div className="flex items-center justify-between">
            <Label htmlFor="is_enabled">启用</Label>
            <Switch
              id="is_enabled"
              checked={watch('is_enabled')}
              onCheckedChange={(checked) => setValue('is_enabled', checked)}
            />
          </div>

          <DialogFooter className="pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
disabled={loading}
            >
              取消
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && (
                <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
              )}
              保存
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}