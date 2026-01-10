'use client'

/**
 * 语音合成配置面板组件
 * 提供合成模式选择、语言、声音、语速等参数配置
 */
import { useEffect, useState, useMemo, useCallback, useRef } from 'react'
import { Check, ChevronsUpDown, BookOpen } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import { cn } from '@/lib/utils'
import {
  useTtsConfigs,
  usePlugins,
  usePluginVoices,
  TtsConfig,
  Plugin,
} from '@/hooks/use-synthesize'
import { useApiAuthStatus } from '@/hooks/use-settings'

/**
 * 合成配置状态
 */
export interface SynthesizeConfig {
  /** 合成模式: config=使用配置, plugin=使用插件 */
  mode: 'config' | 'plugin'
  /** TTS 配置 ID */
  configId?: number
  /** 插件 ID */
  pluginId?: number
  /** 语言区域 */
  locale: string
  /** 声音代码 */
  voice: string
  /** 语速 (0-100) */
  speed: number
  /** 音量 (0-100) */
  volume: number
  /** 音调 (0-100) */
  pitch: number
  /** 是否应用替换规则 */
  applyRules: boolean
  /** 音频格式 */
  format: 'mp3' | 'wav' | 'ogg'
}

interface ConfigPanelProps {
  /** 当前配置 */
  config: SynthesizeConfig
  /** 配置变更回调 */
  onChange: (config: Partial<SynthesizeConfig>) => void
}

/**
 * 配置面板组件
 * 管理语音合成的各项参数
 */
export function ConfigPanel({ config, onChange }: ConfigPanelProps) {
  // 获取数据
  const { data: ttsConfigs, isLoading: configsLoading } = useTtsConfigs()
  const { data: plugins, isLoading: pluginsLoading } = usePlugins()
  const { data: pluginVoices } = usePluginVoices(config.pluginId)

  // 声音选择器的弹出状态
  const [voiceOpen, setVoiceOpen] = useState(false)
  // 声音搜索关键字
  const [voiceSearch, setVoiceSearch] = useState('')

  // 当选择配置时，加载配置的参数
  useEffect(() => {
    if (config.mode === 'config' && config.configId && ttsConfigs) {
      const selectedConfig = ttsConfigs.find(
        (c: TtsConfig) => c.id === config.configId
      )
      if (selectedConfig) {
        onChange({
          pluginId: selectedConfig.plugin_id,
          locale: selectedConfig.locale,
          voice: selectedConfig.voice,
          speed: selectedConfig.speed,
          volume: selectedConfig.volume,
          pitch: selectedConfig.pitch,
        })
      }
    }
  }, [config.mode, config.configId, ttsConfigs, onChange])

  /**
   * 标记语言是否已初始化，避免重复设置默认语言覆盖用户选择
   */
  const localeInitializedRef = useRef(false)
  
  /**
   * 当插件切换或首次加载声音列表时，自动选中合适的语言
   * 优先选中 zh-CN，如果没有则选中 "全部"
   * 只在首次加载时设置，不会覆盖用户的手动选择
   */
  useEffect(() => {
    // 当插件 ID 改变时，重置初始化标记
    localeInitializedRef.current = false
  }, [config.pluginId])
  
  useEffect(() => {
    // 只在首次加载且有语言列表时设置默认值
    if (
      config.mode === 'plugin' &&
      pluginVoices &&
      pluginVoices.locales.length > 0 &&
      !localeInitializedRef.current
    ) {
      localeInitializedRef.current = true
      // 检查是否包含 zh-CN
      if (pluginVoices.locales.includes('zh-CN')) {
        onChange({ locale: 'zh-CN', voice: '' })
      } else {
        // 没有 zh-CN，选中"全部"
        onChange({ locale: 'all', voice: '' })
      }
    }
  }, [config.mode, config.pluginId, pluginVoices, onChange])

  /**
   * 获取当前可用的声音列表
   */
  const getVoiceOptions =(): Array<{ code: string; name: string }> => {
    if (config.mode === 'plugin' && pluginVoices) {
      if (config.locale === 'all') {
        return pluginVoices.allVoices || []
      }
      //兼容某些插件可能直接返回平铺列表但locales 为空的情况
      const voices = pluginVoices.voices[config.locale] || []
      if (voices.length === 0 && config.locale === 'zh-CN' && pluginVoices.allVoices?.length) {
        return pluginVoices.allVoices
      }
      return voices
    }
    return []
  }

  /**
   * 获取当前可用的语言列表
   */
  const getLocaleOptions = (): Array<{ code: string; name: string }> => {
    if (config.mode === 'plugin' && pluginVoices) {
      const options = pluginVoices.locales.map(l => ({ code: l, name: l }))
      // 如果没有语言分类，默认也显示"全部"
      return [{ code: 'all', name: '全部' }, ...options]
    }
    return [{ code: 'zh-CN', name: 'zh-CN' }]
  }

  /**
   * 获取筛选后的声音列表
   * 支持不区分大小写的关键字搜索
   */
  const filteredVoices = useMemo(() => {
    const voices = getVoiceOptions()
    if (!voiceSearch.trim()) {
      return voices
    }
    const keyword = voiceSearch.toLowerCase()
    return voices.filter(v =>
      v.name.toLowerCase().includes(keyword) ||
      v.code.toLowerCase().includes(keyword)
    )
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config.mode, config.locale, pluginVoices, voiceSearch])

  /**
   * 获取当前选中声音的显示名称
   */
  const selectedVoiceName = useMemo(() => {
    if (!config.voice) return null
    const voices = getVoiceOptions()
    const voice = voices.find(v => v.code === config.voice)
    return voice?.name || config.voice
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config.voice, config.mode, config.locale, pluginVoices])

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="text-lg">合成配置</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 合成模式 */}
        <div className="space-y-2">
          <Label>合成模式</Label>
          <Select
            value={config.mode}
            onValueChange={(value: SynthesizeConfig['mode']) =>
              onChange({ mode: value })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="config">使用配置</SelectItem>
              <SelectItem value="plugin">使用插件</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 配置选择 -仅在config 模式下显示 */}
        {config.mode === 'config' && (
          <div className="space-y-2">
            <Label>TTS 配置</Label>
            {configsLoading ? (
              <Skeleton className="h-10 w-full" />
            ) : (
              <Select
                value={config.configId?.toString()}
                onValueChange={(value: string) =>
                  onChange({ configId: parseInt(value) })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择配置" />
                </SelectTrigger>
                <SelectContent>
                  {ttsConfigs?.filter((c: TtsConfig) => c.is_enabled)
                    .map((c: TtsConfig) => (
                      <SelectItem key={c.id} value={c.id.toString()}>
                        {c.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            )}
          </div>
        )}

        {/* 插件选择 - 仅在 plugin 模式下显示 */}
        {config.mode === 'plugin' && (
          <div className="space-y-2">
            <Label>选择插件</Label>
            {pluginsLoading ? (
              <Skeleton className="h-10 w-full" />
            ) : (
              <Select
                value={config.pluginId?.toString()}
                onValueChange={(value: string) =>
                  onChange({ pluginId: parseInt(value) })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择插件" />
                </SelectTrigger>
                <SelectContent>
                  {plugins
                    ?.filter((p: Plugin) => p.is_enabled)
                    .map((p: Plugin) => (
                      <SelectItem key={p.id} value={p.id.toString()}>
                        {p.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            )}
          </div>
        )}

        {/* 语言选择 - plugin 模式下显示 */}
        {config.mode === 'plugin' && (
          <div className="space-y-2">
            <Label>语言</Label>
            <Select
              value={config.locale}
              onValueChange={(value: string) => onChange({ locale: value, voice: '' })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {getLocaleOptions().map((option) => (
                  <SelectItem key={option.code} value={option.code}>
                    {option.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* 声音选择 - plugin 模式下显示，支持搜索筛选 */}
        {config.mode === 'plugin' && (
          <div className="space-y-2">
            <Label>声音</Label><Popover open={voiceOpen} onOpenChange={setVoiceOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={voiceOpen}
                  className="w-full justify-between font-normal"
                >
                  {selectedVoiceName || '选择声音'}
                  <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start">
                <Command shouldFilter={false}>
                  <CommandInput
                    placeholder="搜索声音..."
                    value={voiceSearch}
                    onValueChange={setVoiceSearch}/>
                  <CommandList><CommandEmpty>未找到匹配的声音</CommandEmpty><CommandGroup>
                      {filteredVoices.map((v) => (
                        <CommandItem
                          key={v.code}
                          value={v.code}
                          onSelect={() => {
                            onChange({ voice: v.code })
                            setVoiceOpen(false)
                setVoiceSearch('') // 清空搜索关键字
                          }}
                        >
                          {v.name}<Check
                            className={cn(
                              "ml-auto h-4 w-4",
                              config.voice === v.code ? "opacity-100" : "opacity-0"
                            )}
                          />
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          </div>
        )}

        {/* 语速滑块 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>语速</Label>
            <span className="text-sm text-muted-foreground">
              {config.speed}%
            </span>
          </div>
          <Slider
            value={[config.speed]}
            min={0}
            max={100}
            step={1}
            onValueChange={([value]: number[]) => onChange({ speed: value })}
          />
        </div>

        {/* 音量滑块 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>音量</Label>
            <span className="text-sm text-muted-foreground">
              {config.volume}%
            </span>
          </div>
          <Slider
            value={[config.volume]}
            min={0}
            max={100}
            step={1}
            onValueChange={([value]: number[]) => onChange({ volume: value })}
          />
        </div>

        {/* 音调滑块 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>音调</Label>
            <span className="text-sm text-muted-foreground">
              {config.pitch}%
            </span>
          </div>
          <Slider
            value={[config.pitch]}
            min={0}
            max={100}
            step={1}
            onValueChange={([value]: number[]) => onChange({ pitch: value })}
          />
        </div>

        {/* 应用规则开关 */}
        <div className="flex items-center justify-between">
          <Label>应用替换规则</Label>
          <Switch
            checked={config.applyRules}
            onCheckedChange={(checked: boolean) => onChange({ applyRules: checked })}
          />
        </div>

        {/* 音频格式选择 */}
        <div className="space-y-2">
          <Label>音频格式</Label>
          <Select
            value={config.format}
            onValueChange={(value: SynthesizeConfig['format']) =>
              onChange({ format: value })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="选择音频格式" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="mp3">MP3</SelectItem>
              <SelectItem value="wav">WAV</SelectItem>
              <SelectItem value="ogg">OGG</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 一键导入阅读 Legado */}
        <LegadoImportButton
          pluginId={config.pluginId}
          voice={config.voice}
          pitch={config.pitch}
          voiceName={selectedVoiceName || ''}
          format={config.format}
        />
      </CardContent>
    </Card>
  )
}

/**
 * 阅读 Legado 一键导入按钮组件
 *
 * 实现方式参考 tts-server-android 项目:
 * - 参考文件: lib-server/src/main/resources/forwarder/index.html (第219-231行)
 * - 参考文件: lib-server/src/main/java/com/github/jing332/server/forwarder/LegadoUtils.kt
 *
 * 流程说明:
 * 1. 构建指向 /api/legado 的 URL，该端点返回 Legado httpTTS JSON 配置
 * 2. 使用 legado://import/httpTTS?src= 协议导入，src 参数为上述 URL（经过 encodeURIComponent 编码）
 * 3. 阅读 APP 会请求该 URL 获取 JSON 配置并导入
 */
interface LegadoImportButtonProps {
  pluginId?: number
  voice: string
  pitch: number
  voiceName: string
  format: 'mp3' | 'wav' | 'ogg'
}

function LegadoImportButton({ pluginId, voice, pitch, voiceName, format }: LegadoImportButtonProps) {
  // 获取 API 鉴权状态
  const { data: authStatus } = useApiAuthStatus()
  
  /**
   * 构建 Legado 导入 URL 并触发导入
   *
   * 参考 tts-server-android 的实现：
   * - index.html 第219-231行：构建 /api/legado URL
   * - LegadoUtils.kt：生成 httpTTS 配置 JSON
   *
   * 阅读 APP 模板变量（由后端 /api/legado 端点生成）：
   * - {{speakText}}: 要朗读的文本
   * - {{speakSpeed}}: 语速 (范围 -50 到 50)
   * - {{java.encodeURI(speakText)}}: URL 编码后的文本
   * - rate 公式: {{speakSpeed * 2}} (参考 LegadoUtils.kt 第27行)
   */
  const handleImport = useCallback(async () => {
    const baseUrl = typeof window !== 'undefined' ? window.location.origin : ''
    // TTS API 地址（用于 Legado 配置中的实际请求）
    const ttsApiUrl = `${baseUrl}/api/tts`
    // 配置显示名称
    const name = voiceName ? `TTS-${voiceName}` : 'TTS-Server'
    
    // 构建 /api/legado URL
    // 参考 index.html 第225-227行的实现
    const urlParts = [
      `${baseUrl}/api/legado`,
      `?api=${encodeURIComponent(ttsApiUrl)}`,
      `&name=${encodeURIComponent(name)}`,
      `&plugin_id=${pluginId || 0}`,
      `&pitch=${pitch}`,
      `&voice=${encodeURIComponent(voice)}`,
      `&format=${format}`,
    ]
    
    // 如果 API 鉴权已开启且有 API Key，添加到 URL 中
    if (authStatus?.auth_enabled && authStatus?.api_key) {
      urlParts.push(`&api_key=${encodeURIComponent(authStatus.api_key)}`)
    }
    
    const legadoApiUrl = urlParts.join('')
    
    // === 调试日志 ===
    console.log('=== Legado 导入调试 ===')
    console.log('baseUrl:', baseUrl)
    console.log('ttsApiUrl:', ttsApiUrl)
    console.log('name:', name)
    console.log('API 鉴权状态:', authStatus?.auth_enabled ? '已开启' : '已关闭')
    console.log('legadoApiUrl:', legadoApiUrl)
    
    // 预览 JSON 内容（先用 fetch 获取并打印）
    try {
      const response = await fetch(legadoApiUrl)
      const json = await response.json()
      console.log('=== Legado JSON 响应 ===')
      console.log(JSON.stringify(json, null, 2))
    } catch (e) {
      console.error('获取 Legado JSON 失败:', e)
    }
    
    // 使用 legado:// 协议导入
    // 参考 index.html 第216行：legado://import/httpTTS?src= + encodeURIComponent(url)
    const importUrl = `legado://import/httpTTS?src=${encodeURIComponent(legadoApiUrl)}`
    console.log('legado:// 导入 URL:', importUrl)
    
    window.location.href = importUrl
  }, [pluginId, voice, pitch, voiceName, format, authStatus])

  return (
    <Button
      variant="outline"
      className="w-full"
      onClick={handleImport}
    >
      <BookOpen className="mr-2 h-4 w-4" />
      一键导入阅读 Legado
    </Button>
  )
}