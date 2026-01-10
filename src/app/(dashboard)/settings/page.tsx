'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { PageHeader } from '@/components/ui/page-header'
import { Button } from '@/components/ui/button'
import { Icons } from '@/components/ui/icons'
import { ProfileForm, PasswordForm, CacheSettingsForm, ApiKeyForm } from '@/components/settings'

/**
 * 设置页面标签类型
 */
type SettingsTab = 'profile' | 'security' | 'apikey' | 'cache'

/**
 * 标签配置
 */
const tabs: { id: SettingsTab; label: string; icon: keyof typeof Icons; description: string }[] = [
  {
    id: 'profile',
    label: '个人资料',
    icon: 'user',
    description: '管理您的账户信息',
  },
  {
    id: 'security',
    label: '安全设置',
    icon: 'shield',
    description: '修改密码和安全选项',
  },
  {
    id: 'apikey',
    label: '密钥管理',
    icon: 'key',
    description: '管理 API 访问密钥',
  },
  {
    id: 'cache',
    label: '缓存设置',
    icon: 'database',
    description: '管理音频缓存配置',
  },
]

/**
 * 设置页面
 * 提供个人资料和安全设置的管理界面
 */
export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile')

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <PageHeader
        title="设置"
        description="管理个人资料、安全设置和缓存配置"
      />

      <div className="flex flex-col lg:flex-row gap-6">
        {/* 侧边导航 */}
        <nav className="w-full lg:w-56 shrink-0 space-y-1">
          {tabs.map((tab) => {
            const Icon = Icons[tab.icon]
            const isActive = activeTab === tab.id
            return (
              <Button
                key={tab.id}
                variant={isActive ? 'secondary' : 'ghost'}
                className={cn(
                  'w-full justify-start h-auto py-3 px-4',
                  isActive && 'bg-muted'
                )}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon className="mr-3 h-4 w-4 shrink-0" />
                <div className="text-left">
                  <div className="font-medium">{tab.label}</div>
                  <div className="text-xs text-muted-foreground font-normal">
                    {tab.description}
                  </div>
                </div>
              </Button>
            )
          })}
        </nav>

        {/* 内容区域 */}
        <div className="flex-1 max-w-2xl">
          {activeTab === 'profile' && <ProfileForm />}
          {activeTab === 'security' && <PasswordForm />}
          {activeTab === 'apikey' && <ApiKeyForm />}
          {activeTab === 'cache' && <CacheSettingsForm />}
        </div>
      </div>
    </div>
  )
}