/**
 * 插件详情抽屉组件
 * 展示插件详细信息和代码预览
 */
'use client'

import { useEffect, useMemo, useState } from 'react'

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { Icons } from '@/components/ui/icons'
import { usePlugin, useUpdatePluginUserVars, type Plugin } from '@/hooks/use-plugins'
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
  const { data: detailPlugin } = usePlugin(plugin?.id)
  const updateUserVars = useUpdatePluginUserVars()
  const currentPlugin = detailPlugin ?? plugin
  const [formValues, setFormValues] = useState<Record<string, string>>({})

  const uiFields = useMemo(() => {
    const sections = Array.isArray(currentPlugin?.ui_schema?.sections)
      ? (currentPlugin?.ui_schema?.sections as Array<{ fields?: Array<Record<string, unknown>> }> )
      : []
    return sections.flatMap((section) => section.fields || [])
  }, [currentPlugin])

  useEffect(() => {
    if (!currentPlugin) return
    const nextValues: Record<string, string> = {}
    uiFields.forEach((field) => {
      const key = String(field.key || '')
      if (!key) return
      const rawValue = currentPlugin.user_vars?.[key] ?? currentPlugin.def_vars?.[key] ?? field.default ?? ''
      nextValues[key] = typeof rawValue === 'string' ? rawValue : JSON.stringify(rawValue)
    })
    setFormValues(nextValues)
  }, [currentPlugin, uiFields])

  if (!currentPlugin) return null

  const handleSaveUserVars = async () => {
    const payload: Record<string, unknown> = { ...currentPlugin.user_vars }
    uiFields.forEach((field) => {
      const key = String(field.key || '')
      if (!key) return
      const fieldType = String(field.type || 'text')
      const rawValue = formValues[key] ?? ''
      if (fieldType === 'number') {
        const numberValue = Number(rawValue)
        payload[key] = Number.isNaN(numberValue) ? rawValue : numberValue
      } else {
        payload[key] = rawValue
      }
    })
    await updateUserVars.mutateAsync({ id: currentPlugin.id, user_vars: payload })
  }

  const basicInfoItems = [
    { label: '插件 ID', value: currentPlugin.plugin_id || '-' },
    { label: '版本', value: String(currentPlugin.version ?? '-') },
    { label: '运行引擎', value: currentPlugin.engine_type || 'native' },
    { label: '编译状态', value: currentPlugin.compile_status || '-' },
    { label: '排序', value: String(currentPlugin.order ?? '-') },
    { label: '创建时间', value: currentPlugin.created_at ? formatDateTime(currentPlugin.created_at) : '-' },
    { label: '更新时间', value: currentPlugin.updated_at ? formatDateTime(currentPlugin.updated_at) : '-' },
  ]

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-xl">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            {currentPlugin.name}
            <Badge variant={currentPlugin.is_enabled ? 'default' : 'secondary'}>
              {currentPlugin.is_enabled ? '启用' : '禁用'}
            </Badge>
          </SheetTitle><SheetDescription>
            {currentPlugin.author || '未知作者'} · v{currentPlugin.version}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 h-[calc(100vh-12rem)] overflow-y-auto pr-2">
          <div className="space-y-6 pb-2">
            {/* 基本信息 */}
            <div>
              <h4 className="text-sm font-medium mb-3">基本信息</h4>
              <div className="space-y-3 text-sm">
                {basicInfoItems.map((item) => (
                  <div key={item.label} className="rounded-lg border bg-muted/30 px-3 py-2">
                    <div className="text-xs text-muted-foreground">{item.label}</div>
                    <div className="mt-1 break-all font-medium text-foreground">{item.value}</div>
                  </div>
                ))}
              </div>
            </div><Separator />

            {currentPlugin.compile_error ? (
              <>
                <div>
                  <h4 className="text-sm font-medium mb-3">编译错误</h4>
                  <pre className="rounded-lg bg-destructive/10 p-4 text-xs overflow-x-auto text-destructive">
                    {currentPlugin.compile_error}
                  </pre>
                </div>
                <Separator />
              </>
            ) : null}

            {currentPlugin.capabilities && Object.keys(currentPlugin.capabilities).length > 0 ? (
              <>
                <div>
                  <h4 className="text-sm font-medium mb-3">能力描述</h4>
                  <pre className="rounded-lg bg-muted p-4 text-xs overflow-x-auto">
                    {JSON.stringify(currentPlugin.capabilities, null, 2)}
                  </pre>
                </div>
                <Separator />
              </>
            ) : null}

            {currentPlugin.ui_schema && Object.keys(currentPlugin.ui_schema).length > 0 ? (
              <>
                <div>
                  <h4 className="text-sm font-medium mb-3">界面描述</h4>
                  <pre className="rounded-lg bg-muted p-4 text-xs overflow-x-auto">
                    {JSON.stringify(currentPlugin.ui_schema, null, 2)}
                  </pre>
                </div>
                <Separator />
              </>
            ) : null}

            {uiFields.length > 0 ? (
              <>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium">插件参数</h4>
                    <Button size="sm" onClick={handleSaveUserVars} disabled={updateUserVars.isPending}>
                      {updateUserVars.isPending ? <Icons.spinner className="mr-2 h-4 w-4 animate-spin" /> : null}
                      保存参数
                    </Button>
                  </div>
                  {uiFields.map((field) => {
                    const key = String(field.key || '')
                    const label = String(field.label || key)
                    const hint = String(field.hint || '')
                    const required = Boolean(field.required)
                    const fieldType = String(field.type || 'text')
                    const value = formValues[key] ?? ''
                    return (
                      <div key={key} className="space-y-2">
                        <div className="flex items-center gap-2">
                          <label className="text-sm font-medium">{label}</label>
                          {required ? <Badge variant="secondary">必填</Badge> : null}
                        </div>
                        {fieldType === 'textarea' ? (
                          <Textarea
                            value={value}
                            onChange={(event) => setFormValues((prev) => ({ ...prev, [key]: event.target.value }))}
                            placeholder={hint || label}
                            className="min-h-[120px]"
                          />
                        ) : (
                          <Input
                            type={fieldType === 'number' ? 'number' : 'text'}
                            value={value}
                            onChange={(event) => setFormValues((prev) => ({ ...prev, [key]: event.target.value }))}
                            placeholder={hint || label}
                          />
                        )}
                        {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
                      </div>
                    )
                  })}
                </div>
                <Separator />
              </>
            ) : null}

            {/* 用户变量 */}
            {currentPlugin.user_vars && Object.keys(currentPlugin.user_vars).length > 0 && (
              <>
                <div>
                  <h4 className="text-sm font-medium mb-3">用户变量</h4>
                  <pre className="rounded-lg bg-muted p-4 text-xs overflow-x-auto">
                    {JSON.stringify(currentPlugin.user_vars, null, 2)}
                  </pre>
                </div>
                <Separator />
              </>
            )}

            {/* 代码预览 */}
            <div>
              <h4 className="text-sm font-medium mb-3">代码预览</h4>
              <pre className="rounded-lg bg-muted p-4 text-xs overflow-x-auto max-h-[300px]">
                <code>{currentPlugin.code.substring(0, 2000)}</code>
                {currentPlugin.code.length > 2000 && (
                  <span className="text-muted-foreground">
                    {'\n'}...代码过长，请点击编辑查看完整内容
                  </span>
                )}
              </pre>
            </div></div>
        </div><div className="mt-6">
          <Button className="w-full" onClick={onEdit}><Icons.edit className="mr-2 h-4 w-4" />
            编辑插件
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
