/**
 * 仪表盘页面
 * 展示系统概览、统计信息和快捷操作
 */
'use client'

import { Package, Sliders, FileText, Code } from 'lucide-react'
import { StatCard } from '@/components/dashboard/stat-card'
import { QuickActions } from '@/components/dashboard/quick-actions'
import { WelcomeCard } from '@/components/dashboard/welcome-card'
import { useDashboardStats } from '@/hooks/use-dashboard'

export default function DashboardPage() {
  const { data: stats, isLoading } = useDashboardStats()

  return (
    <div className="space-y-6">
      {/* 欢迎区域 */}
      <WelcomeCard />

      {/* 统计卡片 */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="插件总数"
          value={stats?.plugin_count ?? 0}
          description={`${stats?.enabled_plugin_count ?? 0} 个已启用`}
          icon={Package}
          loading={isLoading}
        />
        <StatCard
          title="TTS 配置"
          value={stats?.config_count ?? 0}
          description="语音配置方案"
          icon={Sliders}
          loading={isLoading}
        />
        <StatCard
          title="替换规则"
          value={stats?.replace_rule_count ?? 0}
          description="文本替换规则"
          icon={FileText}
          loading={isLoading}
        />
        <StatCard
          title="朗读规则"
          value={stats?.speech_rule_count ?? 0}
          description="多音色朗读规则"
          icon={Code}
          loading={isLoading}
        />
      </div>

      {/* 快捷操作 */}
      <QuickActions />
    </div>
  )
}