import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 解析 UTC 时间字符串为 Date 对象
 * 后端返回的时间是 UTC 时间，但没有时区后缀
 * 需要手动添加 'Z' 后缀以确保正确解析为 UTC 时间
 * @param dateString UTC 时间字符串
 * @returns Date 对象
 */
function parseUTCDate(dateString: string): Date {
  // 如果已经有时区信息（Z 或 +/-），直接解析
  if (/[Zz]$/.test(dateString) || /[+-]\d{2}:\d{2}$/.test(dateString)) {
    return new Date(dateString)
  }
  // 后端返回的是 UTC 时间，添加 Z 后缀
  return new Date(dateString + 'Z')
}

/**
 * 格式化日期时间（将 UTC 时间转换为本地时区显示）
 * @param date UTC 日期字符串或 Date 对象
 * @returns 格式化后的本地日期时间字符串
 */
export function formatDateTime(date: string | Date): string {
  const d = typeof date === 'string' ? parseUTCDate(date) : date
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * 格式化日期（仅显示日期部分）
 * @param date UTC 日期字符串或 Date 对象
 * @returns 格式化后的本地日期字符串
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? parseUTCDate(date) : date
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

/**
 * 格式化日期时间（完整版，包含秒）
 * @param date UTC 日期字符串或 Date 对象
 * @returns 格式化后的本地日期时间字符串
 */
export function formatDateTimeFull(date: string | Date): string {
  const d = typeof date === 'string' ? parseUTCDate(date) : date
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/**
 * 格式化相对时间（如：刚刚、5分钟前、2小时前等）
 * @param date UTC 日期字符串或 Date 对象
 * @returns 相对时间字符串
 */
export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? parseUTCDate(date) : date
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffSeconds < 60) {
    return '刚刚'
  } else if (diffMinutes < 60) {
    return `${diffMinutes} 分钟前`
  } else if (diffHours < 24) {
    return `${diffHours} 小时前`
  } else if (diffDays < 30) {
    return `${diffDays} 天前`
  } else {
    return formatDateTime(d)
  }
}
