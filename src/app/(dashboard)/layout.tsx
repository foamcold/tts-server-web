import { MainLayout } from '@/components/layout/main-layout'

/**
 * 仪表盘布局
 *使用主布局组件包裹所有需要登录后访问的页面
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <MainLayout>{children}</MainLayout>
}