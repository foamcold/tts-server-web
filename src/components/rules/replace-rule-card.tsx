/**
 * 替换规则卡片组件
 * 显示规则信息、支持拖拽排序和各种操作
 */
'use client'

import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Icons } from '@/components/ui/icons'
import type { ReplaceRule } from '@/hooks/use-rules'

interface ReplaceRuleCardProps {
  rule: ReplaceRule
  onEdit: () => void
  onDelete: () => void
  onToggle: (enabled: boolean) => void
  onTest: () => void
  isDragging?: boolean
  dragHandleProps?: Record<string, unknown>
}

export function ReplaceRuleCard({
  rule,
  onEdit,
  onDelete,
  onToggle,
  onTest,
  isDragging = false,
  dragHandleProps,
}: ReplaceRuleCardProps) {
  return (
    <Card
      className={cn(
        'transition-all',
        isDragging && 'shadow-lg ring-2 ring-primary',
        !rule.is_enabled && 'opacity-60'
      )}
    >
      <CardContent className="p-6">
        <div className="flex items-center gap-3">
          {/*拖拽手柄 */}<div
            {...dragHandleProps}
            className="cursor-grab text-muted-foreground hover:text-foreground"
          >
            <Icons.grip className="h-5 w-5" />
          </div>

          {/* 规则信息 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-medium truncate">{rule.name}</h3>
              {rule.is_regex && (
                <Badge variant="secondary" className="text-xs">
                  正则
                </Badge>
              )}
              {rule.group && (
                <Badge variant="outline" className="text-xs">
                  {rule.group}
                </Badge>
              )}
            </div>
            <div className="mt-1 text-sm text-muted-foreground font-mono">
              <span className="text-red-500">{rule.pattern}</span>
              <span className="mx-2">→</span>
              <span className="text-green-500">
                {rule.replacement || '(删除)'}
              </span>
            </div>
          </div>

          {/* 操作*/}
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={onTest} title="测试规则">
              <Icons.play className="h-4 w-4" />
            </Button>
            <Switch
              checked={rule.is_enabled}
              onCheckedChange={onToggle}
            />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Icons.more className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={onEdit}>
                  <Icons.edit className="mr-2 h-4 w-4" />
                  编辑
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