/**
 * TTS 配置管理 hooks
 * 提供分组和配置的增删改查、排序等功能
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { request } from '@/lib/api'
import { toast } from 'sonner'

//==================== 类型定义 ====================

/**
 * TTS 配置
 */
export interface TtsConfig {
  id: number
  name: string
  is_enabled: boolean
  source_type: string // plugin, local, http
  plugin_id: string | null
  locale: string
  voice: string
  voice_name: string
  speed: number
  volume: number
  pitch: number
  apply_rules: boolean
  audio_format: string
  speech_rule_id: number | null
  speech_rule_tag: string
  speech_rule_tag_name: string
  extra_data: Record<string, unknown>
  group_id: number
  order: number
  created_at: string
  updated_at: string
}

/**
 * TTS 分组
 */
export interface TtsGroup {
  id: number
  name: string
  order: number
  is_expanded: boolean
  audio_params: Record<string, unknown>
  created_at: string
  updated_at: string
}

/**
 * TTS 分组（包含配置列表）
 */
export interface TtsGroupWithConfigs extends TtsGroup {
  configs: TtsConfig[]
}

/**
 * 创建 TTS 配置参数
 */
export interface TtsConfigCreate {
  name: string
  group_id: number
  is_enabled?: boolean
  source_type: string
  plugin_id?: string | null
  locale?: string
  voice?: string
  voice_name?: string
  speed?: number
  volume?: number
  pitch?: number
  apply_rules?: boolean
  audio_format?: string
  speech_rule_id?: number | null
  speech_rule_tag?: string
  speech_rule_tag_name?: string
  extra_data?: Record<string, unknown>
}

/**
 * 更新 TTS 配置参数
 */
export interface TtsConfigUpdate {
  name?: string
  is_enabled?: boolean
  order?: number
  group_id?: number
  source_type?: string
  plugin_id?: string | null
  locale?: string
  voice?: string
  voice_name?: string
  speed?: number
  volume?: number
  pitch?: number
  apply_rules?: boolean
  audio_format?: string
  speech_rule_id?: number | null
  speech_rule_tag?: string
  speech_rule_tag_name?: string
  extra_data?: Record<string, unknown>
}

/**
 * 创建 TTS 分组参数
 */
export interface TtsGroupCreate {
  name: string
  is_expanded?: boolean
  audio_params?: Record<string, unknown>
}

/**
 * 更新 TTS 分组参数
 */
export interface TtsGroupUpdate {
  name?: string
  is_expanded?: boolean
  order?: number
  audio_params?: Record<string, unknown>
}

/**
 * 排序项
 */
export interface ReorderItem {
  id: number
  order: number
}

// ==================== Query Hooks ====================

/**
 * 获取所有分组及配置
 */
export function useTtsGroupsWithConfigs() {
  return useQuery({
    queryKey: ['ttsGroups'],
    queryFn: () => request<TtsGroupWithConfigs[]>({ url: '/tts-configs/groups' }),
  })
}

/**
 * 获取单个配置
 */
export function useTtsConfig(configId: number | undefined) {
  return useQuery({
    queryKey: ['ttsConfig', configId],
    queryFn: () => request<TtsConfig>({ url: `/tts-configs/configs/${configId}` }),
    enabled: !!configId,
  })
}

// ==================== 分组 Mutation Hooks ====================

/**
 * 创建分组
 */
export function useCreateTtsGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: TtsGroupCreate) =>
      request<TtsGroup>({ method: 'POST', url: '/tts-configs/groups', data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ttsGroups'] })
      toast.success('分组创建成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '创建分组失败')
    },
  })
}

/**
 * 更新分组
 */
export function useUpdateTtsGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TtsGroupUpdate }) =>
      request<TtsGroup>({ method: 'PUT', url: `/tts-configs/groups/${id}`, data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ttsGroups'] })
      toast.success('分组更新成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新分组失败')
    },
  })
}

/**
 * 删除分组
 */
export function useDeleteTtsGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) =>
      request<{ message: string }>({ method: 'DELETE', url: `/tts-configs/groups/${id}` }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ttsGroups'] })
      toast.success('分组删除成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '删除分组失败')
    },
  })
}

/**
 * 重新排序分组
 */
export function useReorderTtsGroups() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (items: ReorderItem[]) =>
      request<{ message: string }>({
        method: 'POST',
        url: '/tts-configs/groups/reorder',
        data: { items },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ttsGroups'] })},
    onError: (error: Error) => {
      toast.error(error.message || '分组排序失败')
    },
  })
}

// ==================== 配置 Mutation Hooks ====================

/**
 * 创建配置
 */
export function useCreateTtsConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: TtsConfigCreate) =>
      request<TtsConfig>({ method: 'POST', url: '/tts-configs/configs', data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ttsGroups'] })
      toast.success('配置创建成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '创建配置失败')
    },
  })
}

/**
 * 更新配置
 */
export function useUpdateTtsConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TtsConfigUpdate }) =>
      request<TtsConfig>({ method: 'PUT', url: `/tts-configs/configs/${id}`, data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ttsGroups'] })
      toast.success('配置更新成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新配置失败')
    },
  })
}

/**
 * 删除配置
 */
export function useDeleteTtsConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) =>
      request<{ message: string }>({ method: 'DELETE', url: `/tts-configs/configs/${id}` }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ttsGroups'] })
      toast.success('配置删除成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '删除配置失败')
    },
  })
}

/**
 * 切换配置启用状态
 */
export function useToggleTtsConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, is_enabled }: { id: number; is_enabled: boolean }) =>
      request<TtsConfig>({
        method: 'PUT',
        url: `/tts-configs/configs/${id}`,
        data: { is_enabled },
      }),
    onSuccess: (data: TtsConfig) => {
      queryClient.invalidateQueries({ queryKey: ['ttsGroups'] })
      toast.success(data.is_enabled ? '配置已启用' : '配置已禁用')
    },
    onError: (error: Error) => {
      toast.error(error.message || '操作失败')
    },
  })
}

/**
 * 重新排序配置
 */
export function useReorderTtsConfigs() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (items: ReorderItem[]) =>
      request<{ message: string }>({
        method: 'POST',
        url: '/tts-configs/configs/reorder',
        data: { items },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ttsGroups'] })
    },
    onError: (error: Error) => {
      toast.error(error.message || '配置排序失败')
    },
  })
}

/**
 * 批量移动配置
 */
export function useBatchMoveTtsConfigs() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { config_ids: number[]; target_group_id: number }) =>
      request<{ message: string }>({
        method: 'POST',
        url: '/tts-configs/configs/batch/move',
        data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ttsGroups'] })
      toast.success('批量移动成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '批量移动失败')
    },
  })
}

/**
 * 批量启用/禁用配置
 */
export function useBatchEnableTtsConfigs() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { config_ids: number[]; is_enabled: boolean }) =>
      request<{ message: string }>({
        method: 'POST',
        url: '/tts-configs/configs/batch/enable',
        data,
      }),
    onSuccess: (
      _data: { message: string },
      variables: { config_ids: number[]; is_enabled: boolean }
    ) => {
      queryClient.invalidateQueries({ queryKey: ['ttsGroups'] })
      toast.success(variables.is_enabled ? '批量启用成功' : '批量禁用成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '批量操作失败')
    },
  })
}