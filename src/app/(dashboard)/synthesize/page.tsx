'use client'

/**
 * 语音合成页面
 * 提供文本输入、配置选择、音频预览和下载功能
 */
import { useState, useCallback } from 'react'
import { PageHeader } from '@/components/ui/page-header'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
import { Icons } from '@/components/ui/icons'
import { AudioPlayer } from '@/components/synthesize/audio-player'
import { ConfigPanel, SynthesizeConfig } from '@/components/synthesize/config-panel'
import { useSynthesize } from '@/hooks/use-synthesize'
import { toast } from 'sonner'

/**
 * 语音合成主页面
 */
export default function SynthesizePage() {
  // 文本内容
  const [text, setText] = useState('')
  // 音频URL
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  // 合成配置
  const [config, setConfig] = useState<SynthesizeConfig>({
    mode: 'config',
    locale: 'zh-CN',
    voice: '',
    speed: 50,
    volume: 50,
    pitch: 50,
    applyRules: true,
    format: 'mp3',
  })

  // 合成 hook
  const synthesize = useSynthesize()

  /**
   * 处理配置变更
   */
  const handleConfigChange = useCallback((updates: Partial<SynthesizeConfig>) => {
    setConfig((prev) => ({ ...prev, ...updates }))
  }, [])

  /**
   * 执行语音合成
   */
  const handleSynthesize = async () => {
    if (!text.trim()) {
      toast.error('请输入要合成的文本')
      return
    }

    // 验证：检查配置模式下是否选择了配置
    if (config.mode === 'config' && !config.configId) {
      toast.error('请选择 TTS 配置')
      return
    }

    // 验证：检查插件模式下是否选择了插件和声音
    if (config.mode === 'plugin' && (!config.pluginId || !config.voice)) {
      toast.error('请选择插件和声音')
      return
    }

    try {
      // 使用配置或插件合成
      const blob = await synthesize.mutateAsync({
        text,
        config_id: config.mode === 'config' ? config.configId : undefined,
        plugin_id: config.mode === 'plugin' ? config.pluginId : undefined,
        locale: config.locale || undefined,  // 空字符串转为undefined
        voice: config.voice || undefined,    // 空字符串转为 undefined
        speed: config.speed,
        volume: config.volume,
        pitch: config.pitch,
        apply_rules: config.applyRules,
        format: config.format,
      })

      // 释放之前的音频 URL
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }
      // 创建新的音频 URL
      const url = URL.createObjectURL(blob)
      setAudioUrl(url)
      toast.success('合成成功')
    } catch (error) {
      console.error('合成失败:', error)
    }
  }

  /**
   * 下载音频文件
   */
  const handleDownload = () => {
    if (!audioUrl) return

    const a = document.createElement('a')
    a.href = audioUrl
    a.download = `tts_${Date.now()}.${config.format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    toast.success('下载开始')
  }

  /**
   * 清空内容
   */
  const handleClear = () => {
    setText('')
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
      setAudioUrl(null)
    }
  }

  // 是否正在加载
  const isLoading = synthesize.isPending

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <PageHeader
        title="语音合成"
        description="输入文本，选择配置，生成语音"
      />

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
        {/* 左侧：文本输入和播放器 */}
        <div className="lg:col-span-2 space-y-4">
          {/* 文本输入卡片 */}
          <Card>
            <CardContent className="p-6">
              {/* 文本输入框 */}
              <Textarea
                placeholder="请输入要合成的文本..."
                className="min-h-[300px] resize-none border-0 focus-visible:ring-0 text-base"
                value={text}
                onChange={(e) => setText(e.target.value)}
                disabled={isLoading}
              />
              
              {/* 操作栏 */}
              <div className="flex items-center justify-between pt-4 border-t mt-4">
                {/* 字符计数 */}
                <span className="text-sm text-muted-foreground">
                  {text.length} 字符
                </span>
                
                {/* 操作按钮 */}
                <div className="flex gap-2">
                  {/* 清空按钮 */}
                  <Button
                    variant="outline"
                    onClick={handleClear}
                    disabled={isLoading || (!text && !audioUrl)}
                  >
                    <Icons.trash className="mr-2 h-4 w-4" />
                    清空
                  </Button>
                  {/* 合成按钮 */}
                  <Button
                    onClick={handleSynthesize}
                    disabled={isLoading || !text.trim()}
                  >
                    {isLoading ? (
                      <>
                        <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
                        合成中...
                      </>
                    ) : (
                      <>
                        <Icons.play className="mr-2 h-4 w-4" />
                        合成
                      </>
                    )}
                    </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 音频播放器 */}
          <AudioPlayer src={audioUrl} onDownload={handleDownload} />
        </div>

        {/* 右侧：配置面板 */}
        <div>
          <ConfigPanel config={config} onChange={handleConfigChange} />
        </div>
      </div>
    </div>
  )
}