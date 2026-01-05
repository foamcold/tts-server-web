'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Icons } from '@/components/ui/icons'
import { useChangePassword } from '@/hooks/use-settings'

// 密码表单验证 schema
const passwordSchema = z
  .object({
    old_password: z.string().min(1, '请输入当前密码'),
    new_password: z.string().min(6, '新密码至少6个字符').max(100, '密码过长'),
    confirm_password: z.string().min(1, '请确认新密码'),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: '两次输入的密码不一致',
    path: ['confirm_password'],
  })
  .refine((data) => data.old_password !== data.new_password, {
    message: '新密码不能与当前密码相同',
    path: ['new_password'],
  })

type PasswordFormData = z.infer<typeof passwordSchema>

/**
 * 密码修改表单组件
 *允许用户修改账户密码
 */
export function PasswordForm() {
  const changePassword = useChangePassword()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      old_password: '',
      new_password: '',
      confirm_password: '',
    },
  })

  // 提交表单
  const onSubmit = (data: PasswordFormData) => {
    changePassword.mutate(
      {
        old_password: data.old_password,
        new_password: data.new_password,
      },
      {
        onSuccess: () => {
          // 成功后清空表单
          reset()
        },
      }
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>修改密码</CardTitle>
        <CardDescription>
          定期修改密码有助于保护您的账户安全
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* 当前密码 */}
          <div className="space-y-2">
            <Label htmlFor="old_password">当前密码</Label>
            <Input
              id="old_password"
              type="password"
              placeholder="请输入当前密码"
              autoComplete="current-password"
              {...register('old_password')}
            />
            {errors.old_password && (
              <p className="text-sm text-destructive">
                {errors.old_password.message}
              </p>
            )}
          </div>

          {/* 新密码 */}
          <div className="space-y-2">
            <Label htmlFor="new_password">新密码</Label>
            <Input
              id="new_password"
              type="password"
              placeholder="请输入新密码(至少6个字符)"
              autoComplete="new-password"
              {...register('new_password')}
            />
            {errors.new_password && (
              <p className="text-sm text-destructive">
                {errors.new_password.message}
              </p>
            )}
          </div>

          {/* 确认新密码 */}
          <div className="space-y-2">
            <Label htmlFor="confirm_password">确认新密码</Label>
            <Input
              id="confirm_password"
              type="password"
              placeholder="请再次输入新密码"
              autoComplete="new-password"
              {...register('confirm_password')}
            />
            {errors.confirm_password && (
              <p className="text-sm text-destructive">
                {errors.confirm_password.message}
              </p>
            )}
          </div>

          {/* 密码要求提示 */}
          <div className="rounded-md bg-muted p-3">
            <p className="text-sm text-muted-foreground">
              <Icons.info className="inline-block mr-1 h-4 w-4" />
              密码要求：
            </p>
            <ul className="text-sm text-muted-foreground list-disc list-inside mt-1 space-y-0.5">
              <li>至少6个字符</li>
              <li>不能与当前密码相同</li>
              <li>建议使用字母、数字和特殊字符的组合</li>
            </ul>
          </div>

          {/* 提交按钮 */}
          <Button type="submit" disabled={changePassword.isPending}>
            {changePassword.isPending && (
              <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
            )}
            修改密码
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}