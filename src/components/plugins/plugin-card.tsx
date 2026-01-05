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
            <div className="flex items-center gap-2">
              <h3 className="font-semibold truncate">{plugin.name}</h3>
              <Badge variant="secondary" className="text-xs">
                v{plugin.version}
              </Badge>
            </div><p className="text-sm text-muted-foreground truncate">
              {plugin.author || '未知作者'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              ID: {plugin.plugin_id}
            </p>
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