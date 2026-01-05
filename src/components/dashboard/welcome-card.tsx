/**
 * 欢迎卡片组件
 * 展示用户欢迎信息和快速入口按钮
 */
'use client'

import { useAuthStore } from '@/stores/auth-store'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Icons } from '@/components/ui/icons'
import Link from 'next/link'

/**
 * 根据当前时间获取问候语
 */
function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
}

/**
 * 欢迎卡片
 * 显示个性化问候和快捷操作按钮
 */
export function WelcomeCard() {
  const { user } = useAuthStore()

  return (
    <Card className="bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-primary/20">
      <CardContent className="p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          {/* 欢迎信息 */}
          <div>
            <h2 className="text-2xl font-bold">
              {getGreeting()}，{user?.username || '用户'} 👋
            </h2>
            <p className="mt-1 text-muted-foreground">欢迎使用 TTS Server Web，今天想要合成什么内容呢？
            </p>
          </div>
          {/* 快捷操作按钮 */}
          <div className="flex gap-2">
            <Button asChild>
              <Link href="/synthesize">
                <Icons.mic className="mr-2 h-4 w-4" />
                开始合成
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/plugins">
                <Icons.package className="mr-2 h-4 w-4" />
                管理插件
              </Link>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}