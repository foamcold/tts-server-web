'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

import { PageHeader } from '@/components/ui/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { PageLoading } from '@/components/ui/loading'
import { Icons } from '@/components/ui/icons'
import { usePlugin, useUpdatePlugin } from '@/hooks/use-plugins'
import { toast } from 'sonner'

export default function PluginEditPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const pluginId = useMemo(() => Number(searchParams.get('id') || ''), [searchParams])
  const { data: plugin, isLoading } = usePlugin(Number.isFinite(pluginId) ? pluginId : undefined)
  const updatePlugin = useUpdatePlugin()

  const [name, setName] = useState('')
  const [author, setAuthor] = useState('')
  const [iconUrl, setIconUrl] = useState('')
  const [version, setVersion] = useState('1')
  const [isEnabled, setIsEnabled] = useState(true)
  const [code, setCode] = useState('')
  const [defVars, setDefVars] = useState('{}')
  const [userVars, setUserVars] = useState('{}')

  useEffect(() => {
    if (!plugin) return
    setName(plugin.name)
    setAuthor(plugin.author || '')
    setIconUrl(plugin.icon_url || '')
    setVersion(String(plugin.version || 1))
    setIsEnabled(plugin.is_enabled)
    setCode(plugin.code || '')
    setDefVars(JSON.stringify(plugin.def_vars || {}, null, 2))
    setUserVars(JSON.stringify(plugin.user_vars || {}, null, 2))
  }, [plugin])

  const handleSave = async () => {
    if (!plugin) return
    try {
      const parsedDefVars = JSON.parse(defVars || '{}')
      const parsedUserVars = JSON.parse(userVars || '{}')
      await updatePlugin.mutateAsync({
        id: plugin.id,
        data: {
          name,
          author,
          icon_url: iconUrl,
          version: Number(version) || 1,
          is_enabled: isEnabled,
          code,
          def_vars: parsedDefVars,
          user_vars: parsedUserVars,
        },
      })
      toast.success('插件已保存')
      router.push('/plugins')
    } catch (error) {
      if (error instanceof SyntaxError) {
        toast.error('变量 JSON 格式不正确')
        return
      }
      throw error
    }
  }

  if (isLoading) {
    return <PageLoading />
  }

  if (!Number.isFinite(pluginId)) {
    return (
      <div className="space-y-6">
        <PageHeader title="参数错误" description="请从插件列表进入编辑页。" />
        <Button variant="outline" onClick={() => router.push('/plugins')}>
          返回插件列表
        </Button>
      </div>
    )
  }

  if (!plugin) {
    return (
      <div className="space-y-6">
        <PageHeader title="插件不存在" description="未找到对应插件。" />
        <Button variant="outline" onClick={() => router.push('/plugins')}>
          返回插件列表
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`编辑插件 | ${plugin.name}`}
        description="编辑插件基础信息、变量和原始代码"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push('/plugins')}>
              返回
            </Button>
            <Button onClick={handleSave} disabled={updatePlugin.isPending}>
              {updatePlugin.isPending ? <Icons.spinner className="mr-2 h-4 w-4 animate-spin" /> : null}
              保存插件
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>插件名称</Label>
              <Input value={name} onChange={(event) => setName(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>作者</Label>
              <Input value={author} onChange={(event) => setAuthor(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>图标地址</Label>
              <Input value={iconUrl} onChange={(event) => setIconUrl(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>版本</Label>
              <Input type="number" value={version} onChange={(event) => setVersion(event.target.value)} />
            </div>
          </div>
          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium">启用插件</p>
              <p className="text-xs text-muted-foreground">关闭后不会参与加载和合成</p>
            </div>
            <Switch checked={isEnabled} onCheckedChange={setIsEnabled} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>变量配置</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="space-y-2">
            <Label>默认变量 JSON</Label>
            <Textarea className="min-h-[220px] font-mono text-xs" value={defVars} onChange={(event) => setDefVars(event.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>用户变量 JSON</Label>
            <Textarea className="min-h-[220px] font-mono text-xs" value={userVars} onChange={(event) => setUserVars(event.target.value)} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>插件代码</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea className="min-h-[520px] font-mono text-xs" value={code} onChange={(event) => setCode(event.target.value)} />
        </CardContent>
      </Card>
    </div>
  )
}
