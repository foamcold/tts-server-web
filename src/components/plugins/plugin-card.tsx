/**
 * 插件卡片组件
 * 展示单个插件的信息和操作
 */
'use client'

import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import {DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Icons } from '@/components/ui/icons'
import type { Plugin } from '@/hooks/use-plugins'

interface PluginCardProps {
  plugin: Plugin
  onView: () => void
  onEdit: () => void
  onDelete: () => void
  onExport: () => void
  onToggle: (enabled: boolean) => void
  loading?: boolean
}

export function PluginCard({
  plugin,
  onView,
  onEdit,
  onDelete,
  onExport,
  onToggle,
  loading = false,
}: PluginCardProps) {
  return (
    <Card
      className={cn(
        'transition-all hover:shadow-md',
        !plugin.is_enabled && 'opacity-60'
      )}
    >
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          {/* 图标 */}
          <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-lg bg-muted">
            <div className="flex h-full w-full items-center justify-center">
              <Icons.package className="h-6 w-6 text-muted-foreground" />
            </div>
          </div>

          {/* 信息 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold truncate">{plugin.name}</h3>
                <p className="text-sm text-muted-foreground truncate mt-1">
                  {plugin.author || '未知作者'}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <Badge variant="secondary" className="text-xs">
                  v{plugin.version}
                </Badge>
                <Badge
                  variant={plugin.compile_status === 'success' ? 'outline' : 'destructive'}
                  className={cn(
                    'text-xs whitespace-nowrap',
                    plugin.compile_status === 'success' && 'border-emerald-200 bg-emerald-50 text-emerald-700'
                  )}
                >
                  {plugin.compile_status === 'success' ? '已编译' : '编译失败'}
                </Badge>
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              ID: {plugin.plugin_id}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              引擎: {plugin.engine_type || 'native'}
            </p>
            {plugin.compile_error ? (
              <p className="text-xs text-destructive mt-2 line-clamp-2">{plugin.compile_error}</p>
            ) : null}
          </div>

          {/* 操作*/}
          <div className="flex items-center gap-2">
            <Switch
              checked={plugin.is_enabled}
              onCheckedChange={onToggle}
              disabled={loading}
            />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Icons.more className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={onView}>
                  <Icons.eye className="mr-2 h-4 w-4" />
                  查看
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onEdit}>
                  <Icons.edit className="mr-2 h-4 w-4" />
                  编辑
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onExport}>
                  <Icons.download className="mr-2 h-4 w-4" />
                  导出
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onDelete}
                  className="text-destructive"
                >
                  <Icons.trash className="mr-2 h-4 w-4" />
                  删除
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
