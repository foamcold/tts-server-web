'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Icons } from '@/components/ui/icons'
import { useSystemInfo, useHealthStatus, formatUptime } from '@/hooks/use-settings'
import { formatDateTimeFull } from '@/lib/utils'

/**
 * 系统信息展示组件
 * 显示系统状态、版本信息和健康检查结果
 */
export function SystemInfoCard() {
  const { data: systemInfo, isLoading: infoLoading, refetch: refetchInfo } = useSystemInfo()
  const { data: healthStatus, isLoading: healthLoading, refetch: refetchHealth } = useHealthStatus()

  const isLoading = infoLoading || healthLoading

  // 刷新所有数据
  const handleRefresh = () => {
    refetchInfo()
    refetchHealth()
  }

  // 加载状态
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>系统信息</CardTitle>
          <CardDescription>查看系统运行状态和版本信息</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="animate-pulse space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex justify-between">
                <div className="h-5 w-24 bg-muted rounded" />
                <div className="h-5 w-32 bg-muted rounded" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <div>
          <CardTitle>系统信息</CardTitle>
          <CardDescription>查看系统运行状态和版本信息</CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh}>
          <Icons.refresh className="h-4 w-4 mr-1" />
          刷新
        </Button>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 健康状态 */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <Icons.zap className="h-4 w-4" />
            服务状态
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">服务状态</span>
              <Badge variant={healthStatus?.status === 'healthy' ? 'default' : 'destructive'}>
                {healthStatus?.status === 'healthy' ? '正常' : '异常'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">数据库</span>
              <Badge variant={healthStatus?.database === 'connected' ? 'default' : 'destructive'}>
                {healthStatus?.database === 'connected' ? '已连接' : '断开'}
              </Badge>
            </div>
          </div>
        </div>

        <Separator />

        {/* 应用信息 */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <Icons.info className="h-4 w-4" />
            应用信息
          </h4>
          <div className="space-y-2">
            <InfoRow label="应用名称" value={systemInfo?.app_name || '-'} />
            <InfoRow label="版本号" value={systemInfo?.version || '-'} />
            <InfoRow label="Python版本" value={systemInfo?.python_version || '-'} />
            <InfoRow label="操作系统" value={systemInfo?.os || '-'} />
            <InfoRow
              label="运行时间" 
              value={systemInfo?.uptime ? formatUptime(systemInfo.uptime) : '-'} 
            />
          </div>
        </div>

        <Separator />

        {/* 数据统计 */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <Icons.file className="h-4 w-4" />
            数据统计
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <StatCard
              label="TTS 配置"
              value={systemInfo?.tts_configs_count || 0}
              icon={<Icons.sliders className="h-4 w-4" />}
            />
            <StatCard
              label="插件数量"
              value={systemInfo?.plugins_count || 0}
              icon={<Icons.package className="h-4 w-4" />}
            />
            <StatCard
              label="替换规则"
              value={systemInfo?.replace_rules_count || 0}
              icon={<Icons.edit className="h-4 w-4" />}
            /><StatCard
              label="朗读规则"
              value={systemInfo?.speech_rules_count || 0}
              icon={<Icons.file className="h-4 w-4" />}
            />
          </div>
        </div>

        <Separator />

        {/* 上次检查时间 */}
        <div className="text-xs text-muted-foreground text-center">
          上次检查：
          {healthStatus?.timestamp
            ? formatDateTimeFull(healthStatus.timestamp)
            : '-'}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * 信息行组件
 */
function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  )
}

/**
 * 统计卡片组件
 */
function StatCard({
  label,
  value,
  icon,
}: {
  label: string
  value: number
  icon: React.ReactNode
}) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
      <div className="text-muted-foreground">{icon}</div>
      <div>
        <p className="text-lg font-semibold">{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    </div>
  )
}