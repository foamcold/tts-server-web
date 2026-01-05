import { z } from 'zod'

/**
 * 登录表单验证规则
 */
export const loginSchema = z.object({
  username: z
    .string()
    .min(3, '用户名至少 3 个字符')
    .max(20, '用户名最多 20 个字符'),
  password: z
    .string()
    .min(6, '密码至少 6 个字符')
    .max(50, '密码最多 50 个字符'),
})

/**
 * 注册表单验证规则
 */
export const registerSchema = z
  .object({
    username: z
      .string()
      .min(3, '用户名至少 3 个字符')
      .max(20, '用户名最多 20 个字符')
      .regex(/^[a-zA-Z0-9_]+$/, '用户名只能包含字母、数字和下划线'),
    password: z
      .string()
      .min(6, '密码至少 6 个字符')
      .max(50, '密码最多 50 个字符'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: '两次输入的密码不一致',
    path: ['confirmPassword'],
  })

/**
 * 修改密码表单验证规则
 */
export const changePasswordSchema = z
  .object({
    old_password: z.string().min(1, '请输入当前密码'),
    new_password: z
      .string()
      .min(6, '新密码至少 6 个字符')
      .max(50, '新密码最多 50 个字符'),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: '两次输入的密码不一致',
    path: ['confirm_password'],
  })

// 类型导出
export type LoginFormData = z.infer<typeof loginSchema>
export type RegisterFormData = z.infer<typeof registerSchema>
export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>
