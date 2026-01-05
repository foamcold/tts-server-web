/**
 * 插件导入对话框
 * 支持JSON粘贴和文件上传两种导入方式
 */
'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Icons } from '@/components/ui/icons'
import { toast } from 'sonner'

interface ImportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onImport: (jsonData: string) => void
  loading?: boolean
}

export function ImportDialog({
  open,
  onOpenChange,
  onImport,
  loading = false,
}: ImportDialogProps) {
  const [jsonData, setJsonData] = useState('')

  // 处理导入
  const handleImport = () => {
    if (!jsonData.trim()) {
      toast.error('请输入插件 JSON 数据')
      return
    }

    try {
      // 验证 JSON 格式
      JSON.parse(jsonData)
      onImport(jsonData)
    } catch {
      toast.error('无效的 JSON 格式')
    }
  }

  // 处理文件上传
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const content = event.target?.result as string
      setJsonData(content)
    }
    reader.readAsText(file)
  }

  // 对话框关闭时重置状态
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setJsonData('')
    }
    onOpenChange(newOpen)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>导入插件</DialogTitle>
          <DialogDescription>
            粘贴插件 JSON 数据或上传插件文件
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/*文件上传 */}
          <div>
            <Label htmlFor="file-upload">上传文件</Label>
            <div className="mt-2">
              <input
                id="file-upload"
                type="file"
                accept=".json"
                onChange={handleFileUpload}
                className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
              />
            </div>
          </div>

          {/* JSON 文本框 */}
          <div>
            <Label htmlFor="json-data">JSON 数据</Label>
            <Textarea
              id="json-data"
              placeholder='粘贴插件 JSON 数据，例如: {"name": "...", "code": "..."}'
              className="mt-2 min-h-[200px] font-mono text-sm"
              value={jsonData}
              onChange={(e) => setJsonData(e.target.value)}
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={loading}
          >
            取消
          </Button>
          <Button onClick={handleImport} disabled={loading || !jsonData.trim()}>
            {loading &&<Icons.spinner className="mr-2 h-4 w-4 animate-spin" />}
            导入
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}