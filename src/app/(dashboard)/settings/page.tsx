'use client'

import { useState } from 'react'

import { ApiKeyForm, CacheSettingsForm, PasswordForm, ProfileForm, UpstreamSettingsForm } from '@/components/settings'
import { Button } from '@/components/ui/button'
import { Icons } from '@/components/ui/icons'
import { PageHeader } from '@/components/ui/page-header'
import { cn } from '@/lib/utils'

/**
 * 设置页面标签类型
 */
type SettingsTab = 'profile' | 'security' | 'apikey' | 'cache' | 'upstream'

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
  {
    id: 'upstream',
    label: '上游连接',
    icon: 'zap',
    description: '配置上游请求策略与容错行为',
  },
]

/**
 * 设置页面
 * 提供个人资料、安全设置、缓存和上游连接配置
 */
export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile')

  return (
    <div className="space-y-6">
      <PageHeader
        title="设置"
        description="管理个人资料、安全设置、缓存配置和上游连接策略"
      />

      <div className="flex flex-col gap-6 lg:flex-row">
        <nav className="w-full shrink-0 space-y-1 lg:w-56">
          {tabs.map((tab) => {
            const Icon = Icons[tab.icon]
            const isActive = activeTab === tab.id
            return (
              <Button
                key={tab.id}
                variant={isActive ? 'secondary' : 'ghost'}
                className={cn('h-auto w-full justify-start px-4 py-3', isActive && 'bg-muted')}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon className="mr-3 h-4 w-4 shrink-0" />
                <div className="text-left">
                  <div className="font-medium">{tab.label}</div>
                  <div className="text-xs font-normal text-muted-foreground">{tab.description}</div>
                </div>
              </Button>
            )
          })}
        </nav>

        <div className="max-w-2xl flex-1">
          {activeTab === 'profile' && <ProfileForm />}
          {activeTab === 'security' && <PasswordForm />}
          {activeTab === 'apikey' && <ApiKeyForm />}
          {activeTab === 'cache' && <CacheSettingsForm />}
          {activeTab === 'upstream' && <UpstreamSettingsForm />}
        </div>
      </div>
    </div>
  )
}
