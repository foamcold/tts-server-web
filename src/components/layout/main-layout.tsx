'use client'

import { cn } from '@/lib/utils'
import { useLayoutStore } from '@/stores/layout-store'
import { Header } from './header'
import { Sidebar } from './sidebar'

/**
 * 主布局组件属性
 */
interface MainLayoutProps {
  children: React.ReactNode
}

/**
 * 主布局组件
 * 包含顶部栏、侧边栏和主内容区域的整体布局
 */
export function MainLayout({ children }: MainLayoutProps) {
  const { sidebarCollapsed } = useLayoutStore()

  return (
    <div className="min-h-screen bg-background">
      {/* 顶部栏 */}
      <Header />
      
      {/* 侧边栏 */}
      <Sidebar />
      
      {/* 主内容区域 */}
      <main
        className={cn(
          'transition-all duration-300 pt-14',
          'md:pl-60',
          sidebarCollapsed && 'md:pl-16'
        )}
      >
        <div className="container mx-auto p-4 md:p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  )
}