'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

import { ImportDialog } from '@/components/plugins/import-dialog'
import { PluginCard } from '@/components/plugins/plugin-card'
import { PluginDrawer } from '@/components/plugins/plugin-drawer'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { Empty } from '@/components/ui/empty'
import { Icons } from '@/components/ui/icons'
import { PageLoading } from '@/components/ui/loading'
import { PageHeader } from '@/components/ui/page-header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  type Plugin,
  useDeletePlugin,
  useExportPlugin,
  useImportPlugin,
  usePlugins,
  useTogglePlugin,
} from '@/hooks/use-plugins'

export default function PluginsPage() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')
  const [importOpen, setImportOpen] = useState(false)
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const { data: plugins, isLoading } = usePlugins()
  const deletePlugin = useDeletePlugin()
  const importPlugin = useImportPlugin()
  const exportPlugin = useExportPlugin()
  const togglePlugin = useTogglePlugin()

  const filteredPlugins = plugins?.filter((plugin: Plugin) => {
    const keyword = searchQuery.toLowerCase()
    return (
      plugin.name.toLowerCase().includes(keyword) ||
      plugin.plugin_id.toLowerCase().includes(keyword) ||
      plugin.author?.toLowerCase().includes(keyword)
    )
  })

  const handleView = (plugin: Plugin) => {
    setSelectedPlugin(plugin)
    setDrawerOpen(true)
  }

  const handleEdit = (plugin: Plugin) => {
    router.push(`/plugins/edit?id=${plugin.id}`)
  }

  const handleExport = async (plugin: Plugin) => {
    try {
      const result = await exportPlugin.mutateAsync(plugin.id)
      const blob = new Blob([result.json_data], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `${plugin.plugin_id}.json`
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('导出失败:', error)
    }
  }

  const handleImport = async (jsonData: string) => {
    try {
      await importPlugin.mutateAsync(jsonData)
      setImportOpen(false)
    } catch (error) {
      console.error('导入失败:', error)
    }
  }

  const handleDelete = async () => {
    if (!deleteId) return
    await deletePlugin.mutateAsync(deleteId)
    setDeleteId(null)
  }

  if (isLoading) {
    return <PageLoading />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="插件管理"
        description="管理 TTS 插件，支持导入、查看、编辑和删除。"
        actions={
          <Button onClick={() => setImportOpen(true)}>
            <Icons.import className="mr-2 h-4 w-4" />
            导入插件
          </Button>
        }
      />

      <div className="flex items-center gap-4">
        <div className="relative max-w-sm flex-1">
          <Icons.search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索插件..."
            className="pl-10"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
          />
        </div>
      </div>

      {filteredPlugins?.length === 0 ? (
        <Empty
          title="暂无插件"
          description="点击上方按钮导入新的插件。"
          action={{
            label: '导入插件',
            onClick: () => setImportOpen(true),
          }}
        />
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredPlugins?.map((plugin: Plugin) => (
            <PluginCard
              key={plugin.id}
              plugin={plugin}
              onView={() => handleView(plugin)}
              onEdit={() => handleEdit(plugin)}
              onDelete={() => setDeleteId(plugin.id)}
              onExport={() => handleExport(plugin)}
              onToggle={(enabled) => togglePlugin.mutate({ id: plugin.id, is_enabled: enabled })}
              loading={togglePlugin.isPending}
            />
          ))}
        </div>
      )}

      <ImportDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        onImport={handleImport}
        loading={importPlugin.isPending}
      />

      <PluginDrawer
        plugin={selectedPlugin}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        onEdit={() => {
          setDrawerOpen(false)
          if (selectedPlugin) handleEdit(selectedPlugin)
        }}
      />

      <ConfirmDialog
        open={!!deleteId}
        onOpenChange={(open) => {
          if (!open) setDeleteId(null)
        }}
        title="删除插件"
        description="确定要删除这个插件吗？此操作不可撤销。"
        confirmText="删除"
        variant="destructive"
        onConfirm={handleDelete}
        loading={deletePlugin.isPending}
      />
    </div>
  )
}
