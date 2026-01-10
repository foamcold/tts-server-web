/**
 * 语音合成相关hooks
 * 提供语音合成、TTS配置、插件和声音列表等功能
 */
import { useMutation, useQuery } from '@tanstack/react-query'
import { api, request } from '@/lib/api'
import { toast } from 'sonner'

//==================== 类型定义 ====================

/**
 * 合成请求参数
 */
export interface SynthesizeRequest {
  text: string
  config_id?: number
  plugin_id?: number
  locale?: string
  voice?: string
  speed?: number
  volume?: number
  pitch?: number
  format?: 'mp3' | 'wav' | 'ogg'
  apply_rules?: boolean
}

/**
 * TTS 配置
 */
export interface TtsConfig {
  id: number
  name: string
  /** 插件标识符（字符串，如 "xfpeiyin.Mr.Wang"），不是数据库 ID */
  plugin_id: string | null
  voice: string
  locale: string
  speed: number
  volume: number
  pitch: number
  is_enabled: boolean
}

/**
 * 插件信息
 */
export interface Plugin {
  id: number
  plugin_id: string
  name: string
  is_enabled: boolean
}

/**
 * 插件声音列表
 */
export interface PluginVoice {
  code: string
  name: string
  locale?: string
}

export interface PluginVoices {
  /** 语言列表 */
  locales: string[]
  /**
   * 声音列表，按语言分类
   * 如果插件没有语言分类，可能会包含一个空字符串 key 或直接是所有声音
   */
  voices: Record<string, PluginVoice[]>
  /** 所有声音的平铺列表，用于“全部”选项 */
  allVoices?: PluginVoice[]
}

//==================== Query Hooks ====================

/**
 * 获取 TTS 配置列表
 * 从 /tts-configs/groups 获取分组及配置，然后提取所有配置
 */
export function useTtsConfigs() {
  return useQuery({
    queryKey: ['ttsConfigs'],
    queryFn: async () => {
      const groups = await request<Array<{ configs: TtsConfig[] }>>({ url: '/tts-configs/groups' })
      // 从所有分组中提取配置
      return groups.flatMap(group => group.configs || [])
    },})
}

/**
 * 获取插件列表
 */
export function usePlugins() {
  return useQuery({
    queryKey: ['plugins'],
    queryFn: () => request<Plugin[]>({ url: '/plugins' }),
  })
}

/**
 * 获取插件声音列表
 * 使用 React Query 内存缓存，避免重复请求
 * 页面刷新后缓存自动清空
 *
 * @param pluginId 插件ID
 */
export function usePluginVoices(pluginId: number | undefined) {
  return useQuery({
    queryKey: ['pluginVoices', pluginId],
    queryFn: async () => {
      const data = await request<PluginVoices>({ url: `/plugins/${pluginId}/voices` })
      
      // 预处理数据：生成 allVoices 平铺列表
      const allVoices: Array<{ code: string; name: string; locale?: string }> = []
      const seenCodes = new Set<string>()

      Object.entries(data.voices).forEach(([locale, voices]) => {
        voices.forEach(v => {
          if (!seenCodes.has(v.code)) {
            allVoices.push({ ...v, locale })
            seenCodes.add(v.code)
          }
        })
      })

      return {
        ...data,
        allVoices
      }
    },
    enabled: !!pluginId,
    // 内存缓存：5分钟内数据视为新鲜，不重新请求
    staleTime: 5 * 60 * 1000,
    // 缓存保留时间：30分钟
    gcTime: 30 * 60 * 1000,
  })
}

// ==================== Mutation Hooks ====================

/**
 * 合成语音
 * 使用 TTS 配置或插件进行语音合成
 */
export function useSynthesize() {
  return useMutation({
    mutationFn: async (data: SynthesizeRequest): Promise<Blob> => {
      const response = await api.post('/synthesize', data, {
        responseType: 'blob',
      })
      return response.data
    },
    onError: (error: Error) => {
      toast.error(error.message || '合成失败')
    },
  })
}