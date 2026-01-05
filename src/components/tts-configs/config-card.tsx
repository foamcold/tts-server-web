'use client'

/**
 * TTS 配置卡片组件
 * 显示单个配置的信息和操作按钮
 */
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
import type { TtsConfig } from '@/hooks/use-tts-configs'

interface ConfigCardProps {
  /** TTS 配置对象 */
  config: TtsConfig
  /** 编辑回调 */
  onEdit: () => void
  /** 删除回调 */
  onDelete: () => void
  /** 复制回调 */
  onCopy: () => void
  /** 切换启用状态回调 */
  onToggle: (enabled: boolean) => void
  /** 测试播放回调 */
  onTest: () => void
  /** 是否正在拖拽 */
  isDragging?: boolean/** 拖拽手柄属性 */
  dragHandleProps?: Record<string, unknown>
}

/**
 * 获取来源类型标签
 */
function getSourceTypeLabel(sourceType: string): string {
  switch (sourceType) {
    case 'plugin':
      return '插件'
    case 'local':
      return '本地'
    case 'http':
      return 'HTTP'
    default:
      return sourceType
  }
}

/**
 * 获取来源类型徽章变体
 */
function getSourceTypeBadgeVariant(
  sourceType: string
): 'default' | 'secondary' | 'outline' {
  switch (sourceType) {
    case 'plugin':
      return 'default'
    case 'local':
      return 'secondary'
    case 'http':
      return 'outline'
    default:
      return 'outline'
  }
}

export function ConfigCard({
  config,
  onEdit,
  onDelete,
  onCopy,
  onToggle,
  onTest,
  isDragging = false,
  dragHandleProps,
}: ConfigCardProps) {
  return (
    <Card
      className={cn(
        'transition-all duration-200',
        isDragging && 'shadow-lg ring-2 ring-primary opacity-90',
        !config.is_enabled && 'opacity-60'
      )}>
      <CardContent className="p-6">
        <div className="flex items-center gap-3">
          {/* 拖拽手柄 */}<div
            {...dragHandleProps}
            className="cursor-grab text-muted-foreground hover:text-foreground active:cursor-grabbing"
          >
            <Icons.grip className="h-5 w-5" />
          </div>

          {/* 配置信息 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-medium truncate">{config.name}</h3>
              <Badge variant="outline" className="text-xs shrink-0">
                {config.locale}
              </Badge>
              <Badge
                variant={getSourceTypeBadgeVariant(config.source_type)}
                className="text-xs shrink-0"
              >
                {getSourceTypeLabel(config.source_type)}
              </Badge>
            </div><div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
              <span
                className="truncate max-w-[200px]"
                title={config.voice_name || config.voice}
              >
                {config.voice_name || config.voice || '未选择声音'}
              </span>
              <span className="shrink-0">语速: {config.speed}%</span>
              <span className="shrink-0">音量: {config.volume}%</span>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex items-center gap-2 shrink-0">
            {/* 测试播放按钮 */}
            <Button
              variant="ghost"
              size="icon"
              onClick={onTest}
              title="测试播放"
            >
              <Icons.play className="h-4 w-4" />
            </Button>

            {/* 启用/禁用开关 */}
            <Switch
              checked={config.is_enabled}
              onCheckedChange={onToggle}
              aria-label={config.is_enabled ? '禁用配置' : '启用配置'}
            />

            {/* 更多操作菜单 */}
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
                <DropdownMenuItem onClick={onCopy}>
                  <Icons.copy className="mr-2 h-4 w-4" />
                  复制
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onDelete}
                  className="text-destructive focus:text-destructive"
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