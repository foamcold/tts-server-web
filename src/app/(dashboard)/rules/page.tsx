/**
 * 规则管理页面
 * 包含替换规则和朗读规则的管理
 */
'use client'

import { useState } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PageHeader } from '@/components/ui/page-header'
import { Button } from '@/components/ui/button'
import { Empty } from '@/components/ui/empty'
import { PageLoading } from '@/components/ui/loading'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { Icons } from '@/components/ui/icons'
import { ReplaceRuleCard } from '@/components/rules/replace-rule-card'
import { ReplaceRuleDialog } from '@/components/rules/replace-rule-dialog'
import {
  useReplaceRules,
  useCreateReplaceRule,
  useUpdateReplaceRule,useDeleteReplaceRule,
  useReorderReplaceRules,useExportReplaceRules,
  useImportReplaceRules,
  type ReplaceRule,type ReplaceRuleCreate,
} from '@/hooks/use-rules'
import { toast } from 'sonner'

// 可排序规则卡片包装器
function SortableReplaceRuleCard({
  rule,
  onEdit,
  onDelete,
  onToggle,
  onTest,
}: {
  rule: ReplaceRule
  onEdit: () => void
  onDelete: () => void
  onToggle: (enabled: boolean) => void
  onTest: () => void
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: rule.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <div ref={setNodeRef} style={style}>
      <ReplaceRuleCard
        rule={rule}
        onEdit={onEdit}
        onDelete={onDelete}
        onToggle={onToggle}
        onTest={onTest}isDragging={isDragging}
        dragHandleProps={{ ...attributes, ...listeners }}
      />
    </div>
  )
}

export default function RulesPage() {
  // 状态
  const [activeTab, setActiveTab] = useState('replace')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<ReplaceRule | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  // 查询
  const { data: replaceRules, isLoading: replaceLoading } = useReplaceRules()

  // 变更
  const createRule = useCreateReplaceRule()
  const updateRule = useUpdateReplaceRule()
  const deleteRule = useDeleteReplaceRule()
  const reorderRules = useReorderReplaceRules()
  const exportRules = useExportReplaceRules()
  const importRules = useImportReplaceRules()

  // 拖拽传感器
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  // 拖拽结束处理
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id || !replaceRules) return

    const oldIndex = replaceRules.findIndex((r) => r.id === active.id)
    const newIndex = replaceRules.findIndex((r) => r.id === over.id)
    const newOrder = arrayMove([...replaceRules], oldIndex, newIndex) as ReplaceRule[]
    reorderRules.mutate(newOrder.map((r) => r.id))
  }

  // 保存规则
  const handleSave = (data: ReplaceRuleCreate) => {
    if (editingRule) {
      updateRule.mutate(
        { id: editingRule.id, data },
        {
          onSuccess: () => {
            setDialogOpen(false)
            setEditingRule(null)},
        }
      )
    } else {
      createRule.mutate(data, {
        onSuccess: () => {
          setDialogOpen(false)
        },
      })
    }
  }

  // 切换启用状态
  const handleToggle = (id: number, enabled: boolean) => {
    updateRule.mutate({ id, data: { is_enabled: enabled } })
  }

  // 测试规则(打开编辑对话框)
  const handleTest = (rule: ReplaceRule) => {
    setEditingRule(rule)
    setDialogOpen(true)
  }

  // 删除规则
  const handleDelete = async () => {
    if (deleteId) {
      await deleteRule.mutateAsync(deleteId)
      setDeleteId(null)
    }
  }

  // 导出规则
  const handleExport = async () => {
    try {
      const rules = await exportRules.mutateAsync()
      const blob = new Blob([JSON.stringify(rules, null, 2)], {
        type: 'application/json',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `replace-rules-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success('规则导出成功')
    } catch {
      // 错误处理已在hook中完成
    }
  }

  // 导入规则
  const handleImport = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.json'
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return

      try {
        const text = await file.text()
        const rules = JSON.parse(text)
        if (Array.isArray(rules)) {
          importRules.mutate(rules)
        } else {
          toast.error('无效的规则文件格式')
        }
      } catch {
        toast.error('解析文件失败')
      }
    }
    input.click()
  }

  if (replaceLoading) {
    return<PageLoading />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="规则管理"
        description="管理文本替换规则和朗读规则"actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={handleExport}>
              <Icons.download className="mr-2 h-4 w-4" />
              导出
            </Button>
            <Button variant="outline" onClick={handleImport}>
              <Icons.upload className="mr-2 h-4 w-4" />
              导入
            </Button><Button onClick={() => setDialogOpen(true)}>
              <Icons.plus className="mr-2 h-4 w-4" />
              新建规则
            </Button>
          </div>
        }
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="replace">
            替换规则
            {replaceRules && replaceRules.length > 0 && (
              <span className="ml-1.5 text-xs text-muted-foreground">
                ({replaceRules.length})
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="speech">朗读规则</TabsTrigger>
        </TabsList>

        <TabsContent value="replace" className="mt-4">
          {replaceRules?.length === 0 ? (
            <Empty
              title="暂无替换规则"
              description="替换规则用于在语音合成前替换文本内容"
              action={{
                label: '新建规则',
                onClick: () => setDialogOpen(true),
              }}
            />
          ) : (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={replaceRules?.map((r) => r.id) || []}
                strategy={verticalListSortingStrategy}
              >
                <div className="space-y-3">
                  {replaceRules?.map((rule) => (
                    <SortableReplaceRuleCard
                      key={rule.id}
                      rule={rule}
                      onEdit={() => {
                        setEditingRule(rule)
                        setDialogOpen(true)
                      }}
                      onDelete={() => setDeleteId(rule.id)}
                      onToggle={(enabled) => handleToggle(rule.id, enabled)}
                      onTest={() => handleTest(rule)}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          )}
        </TabsContent>

        <TabsContent value="speech" className="mt-4">
          <Empty
            title="朗读规则开发中"
            description="朗读规则功能即将上线"/>
        </TabsContent>
      </Tabs>

      {/* 编辑对话框 */}
      <ReplaceRuleDialog
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open)
          if (!open) setEditingRule(null)
        }}
        rule={editingRule}
        onSave={handleSave}
        loading={createRule.isPending || updateRule.isPending}
      />

      {/* 删除确认 */}
      <ConfirmDialog
        open={!!deleteId}
        onOpenChange={(open) => !open && setDeleteId(null)}
        title="删除规则"
        description="确定要删除这个规则吗？此操作不可撤销。"
        confirmText="删除"
        variant="destructive"
        onConfirm={handleDelete}loading={deleteRule.isPending}
      />
    </div>
  )
}