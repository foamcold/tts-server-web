/**
 * 快捷操作组件
 * 提供常用功能的快速入口
 */
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { LucideIcon, Mic, Package, Sliders, FileText } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface QuickAction {
  title: string
  description: string
  href: string
  icon: LucideIcon
  color: string
}

/** 快捷操作列表 */
const actions: QuickAction[] = [
  {
    title: '语音合成',
    description: '快速生成语音',
    href: '/synthesize',
    icon: Mic,
    color: 'bg-blue-500/10 text-blue-600',
  },
  {
    title: '管理插件',
    description: '添加或编辑插件',
    href: '/plugins',
    icon: Package,
    color: 'bg-purple-500/10 text-purple-600',
  },
  {
    title: 'TTS配置',
    description: '调整语音参数',
    href: '/tts-configs',
    icon: Sliders,
    color: 'bg-orange-500/10 text-orange-600',
  },
  {
    title: '替换规则',
    description: '管理文本替换',
    href: '/rules',
    icon: FileText,
    color: 'bg-green-500/10 text-green-600',
  },
]

/**
 * 快捷操作卡片
 * 展示常用功能的快速入口链接
 */
export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">快捷操作</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {actions.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className="group flex flex-col items-center gap-2 rounded-lg border p-4 text-center transition-colors hover:bg-muted"
            >
              {/* 图标 */}
              <div className={cn('rounded-lg p-2.5', action.color)}><action.icon className="h-5 w-5" />
              </div>
              {/* 文字信息 */}
              <div>
                <p className="font-medium group-hover:text-primary">
                  {action.title}
                </p>
                <p className="text-xs text-muted-foreground">
                  {action.description}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}