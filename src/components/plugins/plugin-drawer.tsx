/**
 * 插件详情抽屉组件
 * 展示插件详细信息和代码预览
 */
'use client'

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Icons } from '@/components/ui/icons'
import type { Plugin } from '@/hooks/use-plugins'
import { formatDateTime } from '@/lib/utils'

interface PluginDrawerProps {
  plugin: Plugin | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onEdit: () => void
}

export function PluginDrawer({
  plugin,
  open,
  onOpenChange,
  onEdit,
}: PluginDrawerProps) {
  if (!plugin) return null

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-xl">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            {plugin.name}
            <Badge variant={plugin.is_enabled ? 'default' : 'secondary'}>
              {plugin.is_enabled ? '启用' : '禁用'}
            </Badge>
          </SheetTitle><SheetDescription>
            {plugin.author || '未知作者'} · v{plugin.version}
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-12rem)] mt-6">
          <div className="space-y-6">
            {/* 基本信息 */}
            <div>
              <h4 className="text-sm font-medium mb-3">基本信息</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">插件 ID</span>
                  <span className="font-mono">{plugin.plugin_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">版本</span>
                  <span>{plugin.version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">排序</span>
                  <span>{plugin.order}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">创建时间</span>
                  <span>{formatDateTime(plugin.created_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">更新时间</span>
                  <span>{formatDateTime(plugin.updated_at)}</span>
                </div>
              </div>
            </div><Separator />

            {/* 用户变量 */}
            {plugin.user_vars && Object.keys(plugin.user_vars).length > 0 && (
              <>
                <div>
                  <h4 className="text-sm font-medium mb-3">用户变量</h4>
                  <pre className="rounded-lg bg-muted p-4 text-xs overflow-x-auto">
                    {JSON.stringify(plugin.user_vars, null, 2)}
                  </pre>
                </div>
                <Separator />
              </>
            )}

            {/* 代码预览 */}
            <div>
              <h4 className="text-sm font-medium mb-3">代码预览</h4>
              <pre className="rounded-lg bg-muted p-4 text-xs overflow-x-auto max-h-[300px]">
                <code>{plugin.code.substring(0, 2000)}</code>
                {plugin.code.length > 2000 && (
                  <span className="text-muted-foreground">
                    {'\n'}...代码过长，请点击编辑查看完整内容
                  </span>
                )}
              </pre>
            </div></div>
        </ScrollArea><div className="mt-6">
          <Button className="w-full" onClick={onEdit}><Icons.edit className="mr-2 h-4 w-4" />
            编辑插件
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}