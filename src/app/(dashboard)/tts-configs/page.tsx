'use client'

/**
 * TTS 配置管理页面
 * 支持分组管理和配置的增删改查、拖拽排序
 */
import { useState, useMemo, useEffect } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { PageHeader } from '@/components/ui/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Empty } from '@/components/ui/empty'
import { PageLoading } from '@/components/ui/loading'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { Icons } from '@/components/ui/icons'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import { ConfigCard } from '@/components/tts-configs/config-card'
import { ConfigDialog } from '@/components/tts-configs/config-dialog'
import {
  useTtsGroupsWithConfigs,
  useCreateTtsGroup,
  useUpdateTtsGroup,
  useDeleteTtsGroup,
  useCreateTtsConfig,
  useUpdateTtsConfig,
  useDeleteTtsConfig,useReorderTtsConfigs,
  useToggleTtsConfig,TtsConfig,
  TtsGroup,
  TtsConfigCreate,
  TtsGroupWithConfigs,
  ReorderItem,
} from '@/hooks/use-tts-configs'
import { toast } from 'sonner'

//==================== 可排序配置卡片 ====================

interface SortableConfigCardProps {
  config: TtsConfig
  onEdit: () => void
  onDelete: () => void
  onCopy: () => void
  onToggle: (enabled: boolean) => void
  onTest: () => void
}

function SortableConfigCard({
  config,
  onEdit,
  onDelete,
  onCopy,
  onToggle,
  onTest,
}: SortableConfigCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: config.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <div ref={setNodeRef} style={style}>
      <ConfigCard
        config={config}
        onEdit={onEdit}
        onDelete={onDelete}
        onCopy={onCopy}
        onToggle={onToggle}
        onTest={onTest}
        isDragging={isDragging}
        dragHandleProps={{ ...attributes, ...listeners }}
      />
    </div>
  )
}

// ==================== 分组对话框 ====================

interface GroupDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  group?: TtsGroup | null
  onSave: (name: string) => void
  loading?: boolean
}

function GroupDialog({
  open,
  onOpenChange,
  group,
  onSave,
  loading = false,
}: GroupDialogProps) {
  const [name, setName] = useState('')

  // 编辑时填充数据
  useEffect(() => {
    if (group) {
      setName(group.name)
    } else {
      setName('')
    }
  }, [group])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      toast.error('请输入分组名称')
      return
    }
    onSave(name.trim())
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>
            {group ? '编辑分组' : '新建分组'}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Input
              placeholder="请输入分组名称"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              取消
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && (<Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
              )}
              保存
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ==================== 主页面 ====================

export default function TtsConfigsPage() {
  // 状态
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null)
  const [configDialogOpen, setConfigDialogOpen] = useState(false)
  const [groupDialogOpen, setGroupDialogOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<TtsConfig | null>(null)
  const [editingGroup, setEditingGroup] = useState<TtsGroup | null>(null)
  const [deleteConfigId, setDeleteConfigId] = useState<number | null>(null)
  const [deleteGroupId, setDeleteGroupId] = useState<number | null>(null)

  // API hooks
  const { data: groups, isLoading } = useTtsGroupsWithConfigs()
  const createGroup = useCreateTtsGroup()
  const updateGroup = useUpdateTtsGroup()
  const deleteGroup = useDeleteTtsGroup()
  const createConfig = useCreateTtsConfig()
  const updateConfig = useUpdateTtsConfig()
  const deleteConfig = useDeleteTtsConfig()
  const reorderConfigs = useReorderTtsConfigs()
  const toggleConfig = useToggleTtsConfig()

  // 拖拽传感器
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  // 当前选中的分组
  const selectedGroup = useMemo(() => {
    if (!groups || groups.length === 0) return null
    if (selectedGroupId === null) {
      // 默认选中第一个分组
      return groups[0]
    }
    return groups.find((g: TtsGroupWithConfigs) => g.id === selectedGroupId) || groups[0]
  }, [groups, selectedGroupId])

  // 当前分组的配置列表
  const configs: TtsConfig[] = selectedGroup?.configs || []

  // 拖拽结束处理
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id || configs.length === 0) return

    const oldIndex = configs.findIndex((c) => c.id === active.id)
    const newIndex = configs.findIndex((c) => c.id === over.id)
    const newOrder = arrayMove(configs, oldIndex, newIndex)

    // 构建重新排序数据
    const reorderItems: ReorderItem[] = newOrder.map((c, index) => ({
      id: c.id,
      order: index,
    }))

    reorderConfigs.mutate(reorderItems)
  }

  // 保存配置
  const handleSaveConfig = (data: TtsConfigCreate) => {
    if (editingConfig) {
      updateConfig.mutate(
        { id: editingConfig.id, data },
        {
          onSuccess: () => {
            setConfigDialogOpen(false)
            setEditingConfig(null)},
        }
      )
    } else {
      createConfig.mutate(data, {
        onSuccess: () => {
          setConfigDialogOpen(false)},
      })
    }
  }

  // 复制配置
  const handleCopyConfig = (config: TtsConfig) => {
    if (!selectedGroup) return
    createConfig.mutate({
      name: `${config.name} (复制)`,
      group_id: selectedGroup.id,
      source_type: config.source_type,
      plugin_id: config.plugin_id,
      voice: config.voice,
      voice_name: config.voice_name,
      locale: config.locale,
      speed: config.speed,
      volume: config.volume,
      pitch: config.pitch,
      is_enabled: config.is_enabled,
    })
  }

  // 测试配置
  const handleTestConfig = (config: TtsConfig) => {
    toast.info(`测试配置: ${config.name}（功能开发中）`)
  }

  // 删除配置
  const handleDeleteConfig = async () => {
    if (deleteConfigId) {
      await deleteConfig.mutateAsync(deleteConfigId)
      setDeleteConfigId(null)
    }
  }

  // 保存分组
  const handleSaveGroup = (name: string) => {
    if (editingGroup) {
      updateGroup.mutate(
        { id: editingGroup.id, data: { name } },
        {
          onSuccess: () => {
            setGroupDialogOpen(false)
            setEditingGroup(null)
          },
        }
      )
    } else {
      createGroup.mutate(
        { name },
        {
          onSuccess: () => {
            setGroupDialogOpen(false)
          },
        }
      )
    }
  }

  // 删除分组
  const handleDeleteGroup = async () => {
    if (deleteGroupId) {
      await deleteGroup.mutateAsync(deleteGroupId)
      setDeleteGroupId(null)
      // 如果删除的是当前选中的分组，重置选择
      if (selectedGroupId === deleteGroupId) {
        setSelectedGroupId(null)
      }
    }
  }

  // 加载中
  if (isLoading) {
    return <PageLoading />
  }

  return (
    <div className="space-y-6"><PageHeader
        title="TTS 配置"
        description="管理语音合成配置，设置声音、语速等参数"
      /><div className="grid gap-6 grid-cols-1 lg:grid-cols-4">
        {/* 左侧：分组列表 */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">配置分组</CardTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    setEditingGroup(null)
                    setGroupDialogOpen(true)
                  }}title="新建分组"
                >
                  <Icons.plus className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {!groups || groups.length === 0 ? (
                <Empty
                  title="暂无分组"
                  description="创建第一个分组开始管理配置"
                  className="py-6"
                />
              ) : (
                <div className="space-y-1">
                  {groups.map((group: TtsGroupWithConfigs) => (
                    <div
                      key={group.id}
                      className={cn(
                        'flex items-center justify-between px-3 py-2 rounded-md cursor-pointer transition-colors',
                        selectedGroup?.id === group.id
                          ? 'bg-primary/10 text-primary'
                          : 'hover:bg-muted'
                      )}
                      onClick={() => setSelectedGroupId(group.id)}
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <Icons.folder className="h-4 w-4 shrink-0" />
                        <span className="truncate">{group.name}</span>
                        <span className="text-xs text-muted-foreground shrink-0">
                          ({group.configs.length})
                        </span>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={(e) => {
                            e.stopPropagation()
                            setEditingGroup(group)
                            setGroupDialogOpen(true)
                          }}
                          title="编辑分组"
                        >
                          <Icons.edit className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive hover:text-destructive"
                          onClick={(e) => {
                            e.stopPropagation()
                            setDeleteGroupId(group.id)
                          }}
                          title="删除分组"
                        >
                          <Icons.trash className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* 右侧：配置列表 */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  {selectedGroup ? selectedGroup.name : '选择分组'}
                </CardTitle>
                {selectedGroup && (
                  <Button
                    onClick={() => {
                      setEditingConfig(null)
                      setConfigDialogOpen(true)
                    }}
                  >
                    <Icons.plus className="mr-2 h-4 w-4" />
                    新建配置
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {!selectedGroup ? (
                <Empty
                  title="请选择分组"
                  description="从左侧选择一个分组查看配置"
                  className="py-12"
                />
              ) : configs.length === 0 ? (
                <Empty
                  title="暂无配置"
                  description="点击上方按钮创建新的TTS 配置"
                  action={{
                    label: '新建配置',
                    onClick: () => {
                      setEditingConfig(null)
                      setConfigDialogOpen(true)
                    },
                  }}className="py-12"
                />
              ) : (
                <DndContext
                  sensors={sensors}
                  collisionDetection={closestCenter}onDragEnd={handleDragEnd}
                >
                  <SortableContext
                    items={configs.map((c) => c.id)}
                    strategy={verticalListSortingStrategy}
                  >
                <div className="space-y-3">
                      {configs.map((config) => (
                        <SortableConfigCard
                          key={config.id}
                          config={config}
                          onEdit={() => {
                            setEditingConfig(config)
                            setConfigDialogOpen(true)
                          }}
                          onDelete={() => setDeleteConfigId(config.id)}
                          onCopy={() => handleCopyConfig(config)}
                          onToggle={(enabled) =>
                            toggleConfig.mutate({ id: config.id, is_enabled: enabled })
                          }
                          onTest={() => handleTestConfig(config)}
                        />
                      ))}
                    </div>
                  </SortableContext>
                </DndContext>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 配置编辑对话框 */}<ConfigDialog
        open={configDialogOpen}
        onOpenChange={(open) => {
          setConfigDialogOpen(open)
          if (!open) setEditingConfig(null)
        }}
        config={editingConfig}
        group={selectedGroup}
        onSave={handleSaveConfig}
        loading={createConfig.isPending || updateConfig.isPending}
      />

      {/* 分组编辑对话框 */}
      <GroupDialog
        open={groupDialogOpen}
        onOpenChange={(open) => {
          setGroupDialogOpen(open)
          if (!open) setEditingGroup(null)
        }}
        group={editingGroup}
        onSave={handleSaveGroup}
        loading={createGroup.isPending || updateGroup.isPending}
      />

      {/* 删除配置确认 */}
      <ConfirmDialog
        open={!!deleteConfigId}
        onOpenChange={(open) => !open && setDeleteConfigId(null)}
        title="删除配置"
        description="确定要删除这个配置吗？此操作不可撤销。"
        confirmText="删除"
        variant="destructive"
        onConfirm={handleDeleteConfig}loading={deleteConfig.isPending}
      />

      {/* 删除分组确认 */}
      <ConfirmDialog
        open={!!deleteGroupId}
        onOpenChange={(open) => !open && setDeleteGroupId(null)}
        title="删除分组"
        description="确定要删除这个分组吗？分组内的所有配置也会被删除，此操作不可撤销。"
        confirmText="删除"
        variant="destructive"
        onConfirm={handleDeleteGroup}
        loading={deleteGroup.isPending}
      />
    </div>
  )
}