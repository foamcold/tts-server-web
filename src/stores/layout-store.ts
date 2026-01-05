import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * 布局状态接口
 */
interface LayoutState {
  /**侧边栏是否打开（移动端用） */
  sidebarOpen: boolean
  /** 侧边栏是否折叠（桌面端用） */
  sidebarCollapsed: boolean
  /** 切换侧边栏状态 */
  toggleSidebar: () => void
  /** 设置侧边栏打开状态 */
  setSidebarOpen: (open: boolean) => void
  /** 设置侧边栏折叠状态 */
  setSidebarCollapsed: (collapsed: boolean) => void
}

/**
 * 布局状态管理
 *使用 zustand 进行状态管理，并持久化到localStorage
 */
export const useLayoutStore = create<LayoutState>()(
  persist(
    (set) => ({
      sidebarOpen: false,
      sidebarCollapsed: false,
      toggleSidebar: () =>
        set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
    }),
    {
      name: 'layout-storage',
    }
  )
)