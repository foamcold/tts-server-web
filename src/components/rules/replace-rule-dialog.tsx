/**
 * 替换规则编辑对话框
 * 支持创建、编辑和测试替换规则
 */
'use client'

import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Icons } from '@/components/ui/icons'
import type { ReplaceRule, ReplaceRuleCreate } from '@/hooks/use-rules'
import { useTestReplaceRule } from '@/hooks/use-rules'

// 表单验证模式
const ruleSchema = z.object({
  name: z.string().min(1, '请输入规则名称'),
  group: z.string().optional(),
  pattern: z.string().min(1, '请输入匹配模式'),
  replacement: z.string(),
  is_regex: z.boolean().default(false),
  is_enabled: z.boolean().default(true),
})

type RuleFormData = z.infer<typeof ruleSchema>

interface ReplaceRuleDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  rule?: ReplaceRule | null
  onSave: (data: ReplaceRuleCreate) => void
  loading?: boolean
}

export function ReplaceRuleDialog({
  open,
  onOpenChange,
  rule,
  onSave,
  loading = false,
}: ReplaceRuleDialogProps) {
  const [testText, setTestText] = useState('')
  const [testResult, setTestResult] = useState<string | null>(null)

  const testRule = useTestReplaceRule()

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<RuleFormData>({
    resolver: zodResolver(ruleSchema),
    defaultValues: {
      name: '',
      group: '',
      pattern: '',
      replacement: '',
      is_regex: false,
      is_enabled: true,
    },
  })

  // 当规则变化时重置表单
  useEffect(() => {
    if (rule) {
      reset({
        name: rule.name,
        group: rule.group || '',
        pattern: rule.pattern,
        replacement: rule.replacement,
        is_regex: rule.is_regex,
        is_enabled: rule.is_enabled,
      })
    } else {
      reset({
        name: '',
        group: '',
        pattern: '',
        replacement: '',
        is_regex: false,
        is_enabled: true,
      })
    }
    setTestText('')
    setTestResult(null)
  }, [rule, reset, open])

  const onSubmit = (data: RuleFormData) => {
    onSave({
      ...data,
      group: data.group || undefined,
    })
  }

  // 测试规则
  const handleTest = async () => {
    if (!testText) return

    try {
      const result = await testRule.mutateAsync({
        pattern: watch('pattern'),
        replacement: watch('replacement'),
        is_regex: watch('is_regex'),
        text: testText,
      })
      setTestResult(result.result)
    } catch (error) {
      // 错误处理已在hook 中完成
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {rule ? '编辑替换规则' : '新建替换规则'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* 名称 */}
          <div className="space-y-2">
            <Label htmlFor="name">规则名称</Label>
            <Input
              id="name"
              placeholder="请输入规则名称"
              {...register('name')}
            />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>

          {/* 分组 */}
          <div className="space-y-2">
            <Label htmlFor="group">分组 (可选)</Label>
            <Input
              id="group"
              placeholder="请输入分组名称"
              {...register('group')}
            /></div>

          {/* 匹配模式 */}
          <div className="space-y-2">
            <Label htmlFor="pattern">匹配模式</Label>
            <Input
              id="pattern"
              placeholder="请输入匹配文本或正则表达式"
              className="font-mono"
              {...register('pattern')}
            />
            {errors.pattern && (
              <p className="text-sm text-destructive">
                {errors.pattern.message}
              </p>
            )}
          </div>

          {/* 替换内容 */}
          <div className="space-y-2">
            <Label htmlFor="replacement">替换为</Label>
            <Input
              id="replacement"
              placeholder="替换后的内容 (留空则删除)"
              className="font-mono"
              {...register('replacement')}
            />
          </div>

          {/* 选项 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Switch
                id="is_regex"
                checked={watch('is_regex')}
                onCheckedChange={(checked) => setValue('is_regex', checked)}
              />
              <Label htmlFor="is_regex">使用正则表达式</Label>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                id="is_enabled"
                checked={watch('is_enabled')}
                onCheckedChange={(checked) => setValue('is_enabled', checked)}
              />
              <Label htmlFor="is_enabled">启用</Label>
            </div>
          </div>

          {/* 测试区域 */}
          <div className="space-y-2 p-3 bg-muted rounded-lg">
            <Label>测试规则</Label>
            <Textarea
              placeholder="输入测试文本..."
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              rows={2}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleTest}
              disabled={testRule.isPending || !testText}
            >
              {testRule.isPending && (
                <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
              )}
              测试
            </Button>
            {testResult !== null && (
              <div className="mt-2 p-2 bg-background rounded border">
                <Label className="text-xs text-muted-foreground">结果:</Label>
                <p className="font-mono text-sm">{testResult}</p>
              </div>
            )}
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
              {loading && (
                <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
              )}
              保存
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}