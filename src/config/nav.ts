import { 
  LucideIcon, 
  Home, Mic, 
  Package, 
  FileText, 
  Settings, 
  Sliders
} from 'lucide-react'

/**
 * 导航项接口
 */
export interface NavItem {
  /** 导航标题 */
  title: string
  /** 导航链接 */
  href: string
  /** 图标组件 */
  icon: LucideIcon
  /** 徽章（可选） */
  badge?: string | number/** 子导航项（可选） */
  children?: NavItem[]
}

/**
 * 主导航配置
 *侧边栏显示的主要导航菜单
 */
export const mainNav: NavItem[] = [
  {
    title: '仪表盘',
    href: '/dashboard',
    icon: Home,},
  {
    title: '语音合成',
    href: '/synthesize',
    icon: Mic,
  },
  {
    title: 'TTS 配置',
    href: '/tts-configs',
    icon: Sliders,
  },
  {
    title: '插件管理',
    href: '/plugins',
    icon: Package,
  },
  {
    title: '规则管理',
    href: '/rules',
    icon: FileText,
  },
  {
    title: '系统设置',
    href: '/settings',
    icon: Settings,
  },
]

/**
 * 用户导航配置
 * 用户下拉菜单中的导航项
 */
export const userNav: NavItem[] = [
  {
    title: '个人设置',
    href: '/settings/profile',
    icon: Settings,
  },
]