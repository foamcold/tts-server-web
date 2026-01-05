/**
 * 插件管理 Hooks
 * 提供插件的 CRUD 操作
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { request } from '@/lib/api'
import { toast } from 'sonner'

// 类型定义
export interface Plugin {
  id: number
  plugin_id: string
  name: string
  author: string
  version: number
  code: string
  icon_url: string
  is_enabled: boolean
  user_vars: Record<string, unknown>
  order: number
  created_at: string
  updated_at: string
}

export interface PluginCreate {
  plugin_id: string
  name: string
  author?: string
  version?: number
  code: string
  icon_url?: string
  is_enabled?: boolean
  user_vars?: Record<string, unknown>
}

export interface PluginUpdate {
  name?: string
  author?: string
  version?: number
  code?: string
  icon_url?: string
  is_enabled?: boolean
  order?: number
  user_vars?: Record<string, unknown>
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
 * 获取单个插件
 */
export function usePlugin(id: number | undefined) {
  return useQuery({
    queryKey: ['plugin', id],
    queryFn: () => request<Plugin>({ url: `/plugins/${id}` }),
    enabled: !!id,
  })
}

/**
 * 创建插件
 */
export function useCreatePlugin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: PluginCreate) =>
      request<Plugin>({ method: 'POST', url: '/plugins', data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] })
      toast.success('插件创建成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '创建失败')
    },
  })
}

/**
 * 更新插件
 */
export function useUpdatePlugin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: PluginUpdate }) =>
      request<Plugin>({ method: 'PUT', url: `/plugins/${id}`, data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] })
      toast.success('插件更新成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新失败')
    },
  })
}

/**
 * 删除插件
 */
export function useDeletePlugin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) =>
      request<{ message: string }>({ method: 'DELETE', url: `/plugins/${id}` }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] })
      toast.success('插件删除成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '删除失败')
    },
  })
}

/**
 * 导入插件
 */
export function useImportPlugin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (jsonData: string) =>
      request<Plugin>({
        method: 'POST',
        url: '/plugins/import',
        data: { json_data: jsonData },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] })
      toast.success('插件导入成功')
    },
    onError: (error: Error) => {
      toast.error(error.message || '导入失败')
    },
  })
}

/**
 * 导出插件
 */
export function useExportPlugin() {
  return useMutation({
    mutationFn: (id: number) =>
      request<{ json_data: string }>({ url: `/plugins/${id}/export` }),
    onError: (error: Error) => {
      toast.error(error.message || '导出失败')
    },
  })
}

/**
 * 切换插件启用状态
 */
export function useTogglePlugin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, is_enabled }: { id: number; is_enabled: boolean }) =>
      request<Plugin>({
        method: 'PUT',
        url: `/plugins/${id}`,
        data: { is_enabled },
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] })
      toast.success(data.is_enabled ? '插件已启用' : '插件已禁用')
    },
    onError: (error: Error) => {
      toast.error(error.message || '操作失败')
    },
  })
}