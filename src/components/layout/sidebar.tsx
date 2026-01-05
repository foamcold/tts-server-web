'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { mainNav, NavItem } from '@/config/nav'
import { useLayoutStore } from '@/stores/layout-store'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from '@/components/ui/tooltip'
import { Icons } from '@/components/ui/icons'

/**
 * 侧边栏组件属性
 */
interface SidebarProps {
  className?: string
}

/**
 * 侧边栏组件
 *桌面端显示的固定侧边导航栏
 */
export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname()
  const { sidebarCollapsed, setSidebarCollapsed } = useLayoutStore()

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          'fixed left-0 top-14 z-30 hidden h-[calc(100vh-3.5rem)] border-r bg-background transition-all duration-300 md:block',
          sidebarCollapsed ? 'w-16' : 'w-60',
          className
        )}
      >
        <div className="flex h-full flex-col">
          {/* 导航列表 */}
          <ScrollArea className="flex-1 py-4">
            <nav className="space-y-1 px-2">
              {mainNav.map((item) => (
                <NavLink
                  key={item.href}
                  item={item}
                  isActive={pathname === item.href || pathname.startsWith(item.href + '/')}
                  collapsed={sidebarCollapsed}
                />
              ))}
            </nav>
          </ScrollArea>

          {/* 折叠按钮 */}
          <div className="border-t p-2">
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-center"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            >
              {sidebarCollapsed ? (
                <Icons.chevronRight className="h-4 w-4" />
              ) : (
                <>
                  <Icons.chevronLeft className="h-4 w-4 mr-2" />
                  <span>收起</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </aside>
    </TooltipProvider>
  )
}

/**
 * 导航链接组件属性
 */
interface NavLinkProps {
  item: NavItem
  isActive: boolean
  collapsed: boolean
}

/**
 * 导航链接组件
 * 单个导航项，支持折叠状态下的工具提示
 */
function NavLink({ item, isActive, collapsed }: NavLinkProps) {
  const Icon = item.icon

  const link = (
    <Link
      href={item.href}
      className={cn(
        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
        'hover:bg-accent hover:text-accent-foreground',
        isActive
          ? 'bg-accent text-accent-foreground'
          : 'text-muted-foreground',
        collapsed && 'justify-center px-2'
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && <span>{item.title}</span>}{!collapsed && item.badge && (
        <span className="ml-auto rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
          {item.badge}
        </span>
      )}
    </Link>
  )

  // 折叠状态下显示工具提示
  if (collapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{link}</TooltipTrigger>
        <TooltipContent side="right">{item.title}</TooltipContent>
      </Tooltip>
    )
  }

  return link
}