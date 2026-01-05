/**
 * 规则管理 Hooks
 * 包含替换规则和朗读规则的 CRUD 操作
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { request } from '@/lib/api'
import { toast } from 'sonner'

//============ 替换规则类型 ============

export interface ReplaceRule {
  id: number
  name: string
  group: string
  pattern: string
  replacement: string
  is_regex: boolean
  is_enabled: boolean
  order: number
  created_at: string
  updated_at: string
}

export interface ReplaceRuleCreate {
  name: string
  group?: string
  pattern: string
  replacement: string
  is_regex?: boolean
  is_enabled?: boolean
}

export interface ReplaceRuleUpdate {
  name?: string
  group?: string
  pattern?: string
  replacement?: string
  is_regex?: boolean
  is_enabled?: boolean
  order?: number
}

// ============ 朗读规则类型 ============

export interface SpeechRule {
  id: number
  name: string
  group: string
  tag: string
  tag_rule_id: string
  content_rule: string
  is_enabled: boolean
  order: number
  created_at: string
  updated_at: string
}

export interface SpeechRuleCreate {
  name: string
  group?: string
  tag: string
  tag_rule_id: string
  content_rule: string
  is_enabled?: boolean
}

export interface SpeechRuleUpdate {
  name?: string
  group?: string
  tag?: string
  tag_rule_id?: string
  content_rule?: string
  is_enabled?: boolean
  order?: number
}

// ============ 替换规则 Hooks ============

/**
 * 获取所有替换规则
 */
export function useReplaceRules() {
  return useQuery({
    queryKey: ['replaceRules'],
    queryFn: () => request<ReplaceRule[]>({ url: '/replace-rules' }),})
}

/**
 * 创建替换规则
 */
export function useCreateReplaceRule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ReplaceRuleCreate) =>
      request<ReplaceRule>({ method: 'POST', url: '/replace-rules', data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['replaceRules'] })
      toast.success('规则创建成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '创建失败')
    },
  })
}

/**
 * 更新替换规则
 */
export function useUpdateReplaceRule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ReplaceRuleUpdate }) =>
      request<ReplaceRule>({
        method: 'PUT',
        url: `/replace-rules/${id}`,
        data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['replaceRules'] })
      toast.success('规则更新成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新失败')
    },
  })
}

/**
 * 删除替换规则
 */
export function useDeleteReplaceRule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) =>
      request<{ message: string }>({
        method: 'DELETE',
        url: `/replace-rules/${id}`,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['replaceRules'] })
      toast.success('规则删除成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '删除失败')
    },
  })
}

/**
 * 重新排序替换规则
 */
export function useReorderReplaceRules() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (ruleIds: number[]) =>
      request<{ message: string }>({
        method: 'POST',
        url: '/replace-rules/reorder',
        data: ruleIds,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['replaceRules'] })},
    onError: (error: Error) => {
      toast.error(error.message || '排序失败')
    },
  })
}

/**
 * 测试替换规则
 */
export function useTestReplaceRule() {
  return useMutation({
    mutationFn: (data: {
      pattern: string
      replacement: string
      is_regex: boolean
      text: string
    }) =>
      request<{ result: string }>({
        method: 'POST',
        url: '/replace-rules/test',
        data,
      }),
  })
}

/**
 * 导入替换规则
 */
export function useImportReplaceRules() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (rules: ReplaceRuleCreate[]) =>
      request<{ imported: number; message: string }>({
        method: 'POST',
        url: '/replace-rules/import',
        data: rules,
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['replaceRules'] })
      toast.success(`成功导入 ${data.imported} 条规则`)
    },
    onError: (error: Error) => {
      toast.error(error.message || '导入失败')
    },
  })
}

/**
 * 导出替换规则
 */
export function useExportReplaceRules() {
  return useMutation({
    mutationFn: () =>
      request<ReplaceRule[]>({
        url: '/replace-rules/export/all',
      }),
  })
}

// ============ 朗读规则 Hooks ============

/**
 * 获取所有朗读规则
 */
export function useSpeechRules() {
  return useQuery({
    queryKey: ['speechRules'],
    queryFn: () => request<SpeechRule[]>({ url: '/speech-rules' }),
  })
}

/**
 * 创建朗读规则
 */
export function useCreateSpeechRule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: SpeechRuleCreate) =>
      request<SpeechRule>({ method: 'POST', url: '/speech-rules', data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['speechRules'] })
      toast.success('规则创建成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '创建失败')
    },
  })
}

/**
 * 更新朗读规则
 */
export function useUpdateSpeechRule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: SpeechRuleUpdate }) =>
      request<SpeechRule>({
        method: 'PUT',
        url: `/speech-rules/${id}`,
        data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['speechRules'] })
      toast.success('规则更新成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新失败')
    },
  })
}

/**
 * 删除朗读规则
 */
export function useDeleteSpeechRule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) =>
      request<{ message: string }>({
        method: 'DELETE',
        url: `/speech-rules/${id}`,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['speechRules'] })
      toast.success('规则删除成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '删除失败')
    },
  })
}

/**
 * 重新排序朗读规则
 */
export function useReorderSpeechRules() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (ruleIds: number[]) =>
      request<{ message: string }>({
        method: 'POST',
        url: '/speech-rules/reorder',
        data: ruleIds,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['speechRules'] })
    },
    onError: (error: Error) => {
      toast.error(error.message || '排序失败')
    },
  })
}