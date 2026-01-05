'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from 'next-themes'
import { useEffect, useState } from 'react'
import { AuthGuard } from './auth/auth-guard'

/**
 * 全局 Providers 组件
 * 提供React Query、主题、认证等上下文
 */
export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1分钟
            retry: 1,
          },
        },
      })
  )

  // 将 queryClient 暴露到全局，以便在非组件代码（如 auth-store）中调用
  useEffect(() => {
    if (typeof window !== 'undefined') {
      ;(window as any).queryClient = queryClient
    }
  }, [queryClient])

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <AuthGuard>{children}</AuthGuard>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
