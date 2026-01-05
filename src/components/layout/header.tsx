'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'
import { Button } from '@/components/ui/button'
import {DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { MobileSidebar } from './mobile-sidebar'
import { Icons } from '@/components/ui/icons'

/**
 * 顶部栏组件属性
 */
interface HeaderProps {
  className?: string
}

/**
 * 顶部栏组件
 * 包含 Logo、移动端菜单按钮、主题切换和用户菜单
 */
export function Header({ className }: HeaderProps) {
  const router = useRouter()
  const { user, logout } = useAuthStore()

  /**
   * 处理退出登录
   */
  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  return (
    <header
      className={cn(
        'sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60',
        className
      )}
    ><div className="flex h-14 items-center gap-4 px-4 md:px-6">
        {/*移动端菜单 */}
        <MobileSidebar />

        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2">
          <Icons.volume className="h-6 w-6 text-primary" />
          <span className="font-bold hidden sm:inline-block">TTS Server</span>
        </Link>

        {/* 右侧操作区*/}
        <div className="ml-auto flex items-center gap-2">
          {/* 主题切换 */}
          <ThemeToggle />

          {/* 用户菜单 */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="relative">
                <Icons.user className="h-5 w-5" />
                <span className="sr-only">用户菜单</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium">{user?.username || '用户'}</p>
                  <p className="text-xs text-muted-foreground">
                    {user?.is_admin ? '管理员' : '普通用户'}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
              <Link href="/settings">
                <Icons.settings className="mr-2 h-4 w-4" />
              个人设置
              </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <Icons.logOut className="mr-2 h-4 w-4" />
                退出登录
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}