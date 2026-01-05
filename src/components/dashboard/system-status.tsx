/**
 * 系统状态组件
 * 展示各服务的运行状态
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Icons } from '@/components/ui/icons'

/** 状态类型 */
type StatusType = 'online' | 'offline' | 'warning'

/** 状态项接口 */
interface StatusItem {
  name: string
  status: StatusType
  message?: string
}

interface SystemStatusProps {
  /** 状态项列表 */
  items?: StatusItem[]
}

/** 默认状态项 */
const defaultItems: StatusItem[] = [
  { name: 'API 服务', status: 'online' },
  { name:'Edge TTS', status: 'online' },
  { name: '插件引擎', status: 'online' },
]

/** 状态颜色映射 */
const statusColors: Record<StatusType, string> = {
  online: 'bg-green-500',
  offline: 'bg-red-500',
  warning: 'bg-yellow-500',
}

/** 状态文字映射 */
const statusTexts: Record<StatusType, string> = {
  online: '正常',
  offline: '离线',
  warning: '警告',
}

/**
 * 系统状态卡片
 *展示系统各服务的运行状态
 */
export function SystemStatus({ items = defaultItems }: SystemStatusProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Icons.zap className="h-5 w-5 text-primary" />
          系统状态
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {items.map((item) => (
            <div
              key={item.name}
              className="flex items-center justify-between">
              {/* 状态指示器和名称 */}
              <div className="flex items-center gap-2">
                <div
                  className={`h-2 w-2 rounded-full ${statusColors[item.status]}`}
                />
                <span className="text-sm">{item.name}</span>
              </div>
              {/* 状态标签 */}
              <Badge
                variant={item.status === 'online' ? 'default' : 'destructive'}
                className="text-xs"
              >
                {statusTexts[item.status]}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}