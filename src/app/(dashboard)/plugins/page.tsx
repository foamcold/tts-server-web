/**
 * 插件管理页面
 * 支持插件的查看、添加、编辑、删除和导入导出
 */
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { PageHeader } from '@/components/ui/page-header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Empty } from '@/components/ui/empty'
import { PageLoading } from '@/components/ui/loading'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { Icons } from '@/components/ui/icons'
import { PluginCard } from '@/components/plugins/plugin-card'
import { ImportDialog } from '@/components/plugins/import-dialog'
import { PluginDrawer } from '@/components/plugins/plugin-drawer'
import {
  usePlugins,
  useDeletePlugin,
  useImportPlugin,
  useExportPlugin,
  useTogglePlugin,
  type Plugin,
} from '@/hooks/use-plugins'

export default function PluginsPage() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')
  const [importOpen, setImportOpen] = useState(false)
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  // 获取插件列表
  const { data: plugins, isLoading } = usePlugins()
  const deletePlugin = useDeletePlugin()
  const importPlugin = useImportPlugin()
  const exportPlugin = useExportPlugin()
  const togglePlugin = useTogglePlugin()

  // 过滤插件
  const filteredPlugins = plugins?.filter(
    (p: Plugin) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.plugin_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.author?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // 查看插件详情
  const handleView = (plugin: Plugin) => {
    setSelectedPlugin(plugin)
    setDrawerOpen(true)
  }

  // 编辑插件
  const handleEdit = (plugin: Plugin) => {
    router.push(`/plugins/${plugin.id}/edit`)
  }

  // 导出插件
  const handleExport = async (plugin: Plugin) => {
    try {
      const result = await exportPlugin.mutateAsync(plugin.id)
      // 下载 JSON 文件
      const blob = new Blob([result.json_data], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${plugin.plugin_id}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('导出失败:', error)
    }
  }

  // 导入插件
  const handleImport = async (jsonData: string) => {
    try {
      await importPlugin.mutateAsync(jsonData)
      setImportOpen(false)} catch (error) {
      console.error('导入失败:', error)
    }
  }

  // 删除插件
  const handleDelete = async () => {
    if (deleteId) {
      await deletePlugin.mutateAsync(deleteId)
      setDeleteId(null)
    }
  }

  // 加载中
  if (isLoading) {
    return <PageLoading />
  }

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <PageHeader
        title="插件管理"
        description="管理 TTS 插件，导入新插件或编辑现有插件"
        actions={
          <Button onClick={() => setImportOpen(true)}>
            <Icons.import className="mr-2 h-4 w-4" />
            导入插件
          </Button>
        }
      />

      {/* 搜索栏 */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Icons.search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索插件..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* 插件列表 */}
      {filteredPlugins?.length === 0 ? (
        <Empty
          title="暂无插件"
          description="点击上方按钮导入新插件"action={{
            label: '导入插件',
            onClick: () => setImportOpen(true),
          }}
        />
      ) : (
        <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                    {filteredPlugins?.map((plugin: Plugin) => (
            <PluginCard
              key={plugin.id}
              plugin={plugin}
              onView={() => handleView(plugin)}
              onEdit={() => handleEdit(plugin)}
              onDelete={() => setDeleteId(plugin.id)}
              onExport={() => handleExport(plugin)}
              onToggle={(enabled) =>
                togglePlugin.mutate({ id: plugin.id, is_enabled: enabled })
              }
              loading={togglePlugin.isPending}
            />
          ))}
        </div>
      )}

      {/* 导入对话框 */}
      <ImportDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        onImport={handleImport}
        loading={importPlugin.isPending}
      />

      {/* 详情抽屉 */}
      <PluginDrawer
        plugin={selectedPlugin}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        onEdit={() => {
          setDrawerOpen(false)
          if (selectedPlugin) {
            handleEdit(selectedPlugin)
          }
        }}/>

      {/* 删除确认*/}
      <ConfirmDialog
        open={!!deleteId}
        onOpenChange={(open) => !open && setDeleteId(null)}
        title="删除插件"
        description="确定要删除这个插件吗？此操作不可撤销。"
        confirmText="删除"
        variant="destructive"
        onConfirm={handleDelete}loading={deletePlugin.isPending}
      />
    </div>
  )
}