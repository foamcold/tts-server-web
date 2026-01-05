'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Icons } from '@/components/ui/icons'
import { useProfile, useUpdateProfile } from '@/hooks/use-settings'
import { formatDateTime } from '@/lib/utils'

// 表单验证 schema
const profileSchema = z.object({
  username: z.string().min(2, '用户名至少2个字符').max(50, '用户名最多50个字符'),
})

type ProfileFormData = z.infer<typeof profileSchema>

/**
 * 个人资料表单组件
 * 显示和编辑用户基本信息
 */
export function ProfileForm() {
  const { data: profile, isLoading } = useProfile()
  const updateProfile = useUpdateProfile()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),})

  // 当profile数据加载完成后，重置表单值
  useEffect(() => {
    if (profile) {
      reset({
        username: profile.username,
      })
    }
  }, [profile, reset])

  // 提交表单
  const onSubmit = (data: ProfileFormData) => {
    updateProfile.mutate(data)
  }

  // 加载状态
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>个人资料</CardTitle>
          <CardDescription>管理您的账户信息</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="animate-pulse space-y-4">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-muted" />
              <div className="h-8 w-24 bg-muted rounded" />
            </div>
            <div className="h-10 bg-muted rounded" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>个人资料</CardTitle>
        <CardDescription>管理您的账户信息</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* 头像区域 */}
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarImage src={undefined} alt={profile?.username} />
              <AvatarFallback className="text-lg bg-primary text-primary-foreground">
                {profile?.username?.charAt(0).toUpperCase() ||'U'}
              </AvatarFallback>
            </Avatar>
            <div className="space-y-1">
              <p className="text-sm font-medium">{profile?.username}</p>
              <p className="text-xs text-muted-foreground">
                {profile?.is_admin ? '管理员' : '普通用户'}
              </p>
            </div>
          </div>

          {/* 用户名输入 */}
          <div className="space-y-2">
            <Label htmlFor="username">用户名</Label>
            <Input
              id="username"
              placeholder="请输入用户名"
              {...register('username')}
            />
            {errors.username && (
              <p className="text-sm text-destructive">
                {errors.username.message}
              </p>
            )}
          </div>

          {/* 账户ID（只读） */}
          <div className="space-y-2">
            <Label>账户 ID</Label>
            <Input value={profile?.id?.toString() || '-'} disabled /><p className="text-xs text-muted-foreground">
              账户ID不可更改
            </p>
          </div>

          {/* 注册时间（只读） */}
          <div className="space-y-2">
            <Label>注册时间</Label>
            <Input
              value={
                profile?.created_at
                  ? formatDateTime(profile.created_at)
                  : '-'
              }
              disabled
            />
          </div>

          {/* 提交按钮 */}
          <Button
            type="submit"
            disabled={!isDirty || updateProfile.isPending}
          >
            {updateProfile.isPending && (
              <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
            )}
            保存更改
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}