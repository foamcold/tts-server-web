/**
 * 仪表盘相关 hooks
 * 用于获取仪表盘统计数据
 */
import { useQuery } from '@tanstack/react-query'
import { request } from '@/lib/api'

/** 仪表盘统计数据接口 */
interface DashboardStats {
  plugin_count: number
  enabled_plugin_count: number
  config_count: number
  replace_rule_count: number
  speech_rule_count: number
}

/** 插件数据接口 */
interface PluginData {
  id: number
  is_enabled: boolean
}

/** 配置数据接口 */
interface ConfigData {
  id: number
}

/** 规则数据接口 */
interface RuleData {
  id: number
}

/**
 * 获取仪表盘统计数据 hook
 * 并行请求多个 API 获取统计信息
 */
export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboardStats'],
    queryFn: async(): Promise<DashboardStats> => {
            // 并行请求多个统计数据
      const [plugins, groups, replaceRules, speechRules] = await Promise.all([
        request<PluginData[]>({ url: '/plugins' }).catch(() => []),
        request<Array<{ configs: ConfigData[] }>>({ url: '/tts-configs/groups' }).catch(() => []),
        request<RuleData[]>({ url: '/replace-rules' }).catch(() => []),
        request<RuleData[]>({ url: '/speech-rules' }).catch(() => []),
      ])
      
      // 从分组中提取所有配置
      const configs = groups.flatMap(group => group.configs || [])

      return {
        plugin_count: plugins.length,
        enabled_plugin_count: plugins.filter((p) => p.is_enabled).length,
        config_count: configs.length,
        replace_rule_count: replaceRules.length,
        speech_rule_count: speechRules.length,
      }
    },
    staleTime: 30 * 1000, // 30秒内不重新请求
  })
}