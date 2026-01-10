'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Icons } from '@/components/ui/icons'
import { Separator } from '@/components/ui/separator'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import {
  useApiKey,
  useRegenerateApiKey,
  useApiAuthSettings,
  useUpdateApiAuthSettings,
} from '@/hooks/use-settings'
import { useProfile } from '@/hooks/use-settings'
import { toast } from 'sonner'

/**
 * API 密钥管理表单组件
 * 包含 API 鉴权开关（仅管理员）和个人 API Key 管理
 */
export function ApiKeyForm() {
  const { data: profile } = useProfile()
  const { data: apiKeyData, isLoading: apiKeyLoading } = useApiKey()
  const { data: authSettings, isLoading: authSettingsLoading } = useApiAuthSettings()
  const updateAuthSettings = useUpdateApiAuthSettings()
  const regenerateApiKey = useRegenerateApiKey()

  const [showRegenerateConfirm, setShowRegenerateConfirm] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)

  // 复制 API Key 到剪贴板
  const handleCopyApiKey = async () => {
    if (apiKeyData?.api_key) {
      try {
        await navigator.clipboard.writeText(apiKeyData.api_key)
        toast.success('API Key 已复制到剪贴板')
      } catch {
        toast.error('复制失败，请手动复制')
      }
    }
  }

  // 切换 API 鉴权开关
  const handleToggleAuth = (enabled: boolean) => {
    updateAuthSettings.mutate({ api_auth_enabled: enabled })
  }

  // 重新生成 API Key
  const handleRegenerateApiKey = () => {
    regenerateApiKey.mutate()
    setShowRegenerateConfirm(false)
  }

  // 加载状态
  if (apiKeyLoading || authSettingsLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>密钥管理</CardTitle>
          <CardDescription>管理 API 访问密钥和鉴权设置</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="animate-pulse space-y-4">
            <div className="h-10 bg-muted rounded" />
            <div className="h-10 bg-muted rounded" />
            <div className="h-10 bg-muted rounded" />
          </div>
        </CardContent>
      </Card>
    )
  }

  const isAdmin = profile?.is_admin ?? false
  const authEnabled = authSettings?.api_auth_enabled ?? false

  return (
    <div className="space-y-6">
      {/* API 鉴权设置卡片（仅管理员可见） */}
      {isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Icons.shield className="h-5 w-5" />
              API 鉴权设置
            </CardTitle>
            <CardDescription>
              控制公开 API 是否需要密钥验证
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="api_auth_enabled">启用 API 鉴权</Label>
                <p className="text-sm text-muted-foreground">
                  开启后，调用公开 TTS API 时需要提供有效的 API Key
                </p>
              </div>
              <Switch
                id="api_auth_enabled"
                checked={authEnabled}
                onCheckedChange={handleToggleAuth}
                disabled={updateAuthSettings.isPending}
              />
            </div>

            {authEnabled && (
              <div className="mt-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800">
                <div className="flex items-start gap-2">
                  <Icons.alertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5" />
                  <div className="text-sm text-amber-800 dark:text-amber-200">
                    <p className="font-medium">API 鉴权已启用</p>
                    <p className="mt-1">
                      所有公开 API 请求都需要携带有效的 API Key 参数。
                      用户可以在下方查看和管理自己的 API Key。
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 个人 API Key 卡片 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Icons.key className="h-5 w-5" />
            我的 API Key
          </CardTitle>
          <CardDescription>
            用于调用公开 TTS API 的身份验证密钥
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* API Key 显示 */}
          <div className="space-y-2">
            <Label>API Key</Label>
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Input
                  type={showApiKey ? 'text' : 'password'}
                  value={apiKeyData?.api_key || ''}
                  readOnly
                  className="pr-20 font-mono"
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2"
                    onClick={() => setShowApiKey(!showApiKey)}
                  >
                    {showApiKey ? (
                      <Icons.eyeOff className="h-4 w-4" />
                    ) : (
                      <Icons.eye className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2"
                    onClick={handleCopyApiKey}
                  >
                    <Icons.copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              请妥善保管您的 API Key，不要分享给他人
            </p>
          </div>

          <Separator />

          {/* 使用说明 */}
          <div className="space-y-3">
            <Label>使用方式</Label>
            <div className="text-sm text-muted-foreground space-y-2">
              <p>在调用 TTS API 时，将 API Key 作为查询参数传递：</p>
              <code className="block p-3 rounded bg-muted font-mono text-xs break-all">
                /api/tts?text=你好&api_key={showApiKey ? (apiKeyData?.api_key || 'YOUR_API_KEY') : '***'}
              </code>
            </div>
          </div>

          <Separator />

          {/* 重新生成按钮 */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-sm font-medium">重新生成 API Key</p>
              <p className="text-xs text-muted-foreground">
                生成新的 API Key 后，旧的 Key 将立即失效
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => setShowRegenerateConfirm(true)}
              disabled={regenerateApiKey.isPending}
            >
              {regenerateApiKey.isPending ? (
                <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Icons.refresh className="mr-2 h-4 w-4" />
              )}
              重新生成
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 重新生成确认对话框 */}
      <ConfirmDialog
        open={showRegenerateConfirm}
        onOpenChange={setShowRegenerateConfirm}
        title="重新生成 API Key"
        description="确定要重新生成 API Key 吗？生成后，当前的 API Key 将立即失效，所有使用旧 Key 的应用将无法正常工作。"
        confirmText="确认重新生成"
        cancelText="取消"
        variant="destructive"
        onConfirm={handleRegenerateApiKey}
      />
    </div>
  )
}
