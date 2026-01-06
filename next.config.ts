import type { NextConfig } from 'next'

const isProd = process.env.NODE_ENV === 'production'

const nextConfig: NextConfig = {
  // 仅在生产环境启用静态文件导出
  ...(isProd && { output: 'export' }),
  // 静态文件输出目录
  distDir: 'dist',
  // 配置后端API代理（仅开发环境生效，生产环境由后端处理）
  ...(!isProd && {
    async rewrites() {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ]
    },
  }),
  // 禁用 x-powered-by 头
  poweredByHeader: false,
  // 启用严格模式
  reactStrictMode: true,
}

export default nextConfig