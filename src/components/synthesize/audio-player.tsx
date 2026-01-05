'use client'

/**
 * 音频播放器组件
 * 提供音频播放、进度控制、音量调节和下载功能
 */
import { useRef, useState, useEffect, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Icons } from '@/components/ui/icons'

interface AudioPlayerProps {
  /** 音频源URL */
  src: string | null
  /** 下载回调 */
  onDownload?: () => void
  /** 自定义样式 */
  className?: string
}

/**
 * 音频播放器
 * 支持播放/暂停、进度拖拽、音量控制和下载
 */
export function AudioPlayer({ src, onDownload, className}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(100)
  const [isMuted, setIsMuted] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)

  // 当音频源变化时重置状态
  useEffect(() => {
    if (src && audioRef.current) {
      setIsPlaying(false)
      setCurrentTime(0)
      setDuration(0)
      setIsLoaded(false)
      audioRef.current.load()
    }
  }, [src])

  // 切换播放/暂停
  const togglePlay = useCallback(async () => {
    if (!audioRef.current) return

    try {
      if (isPlaying) {
        audioRef.current.pause()
        setIsPlaying(false)
      } else {
        await audioRef.current.play()
        setIsPlaying(true)
      }
    } catch (error) {
      console.error('播放失败:', error)
      setIsPlaying(false)
    }
  }, [isPlaying])

  // 切换静音
  const toggleMute = useCallback(() => {
    if (!audioRef.current) return
    
    const newMuted = !isMuted
    audioRef.current.muted = newMuted
    setIsMuted(newMuted)
  }, [isMuted])

  // 更新当前播放时间
  const handleTimeUpdate = useCallback(() => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime)
    }
  }, [])

  // 加载音频元数据（获取时长）
  const handleLoadedMetadata = useCallback(() => {
    if (audioRef.current) {
      const audioDuration = audioRef.current.duration
      if (!isNaN(audioDuration) && isFinite(audioDuration)) {
        setDuration(audioDuration)
      }
      setIsLoaded(true)
    }
  }, [])

  // 音频可以播放时再次检查时长（某些浏览器需要）
  const handleCanPlay = useCallback(() => {
    if (audioRef.current) {
      const audioDuration = audioRef.current.duration
      if (!isNaN(audioDuration) && isFinite(audioDuration) && audioDuration > 0) {
        setDuration(audioDuration)
      }
      setIsLoaded(true)
    }
  }, [])

  // 时长变化时更新（用于流媒体或动态加载的音频）
  const handleDurationChange = useCallback(() => {
    if (audioRef.current) {
      const audioDuration = audioRef.current.duration
      if (!isNaN(audioDuration) && isFinite(audioDuration) && audioDuration > 0) {
        setDuration(audioDuration)
      }
    }
  }, [])

  // 拖拽进度条
  const handleSeek = useCallback((value: number[]) => {
    if (audioRef.current && isLoaded) {
      const seekTime = value[0]
      audioRef.current.currentTime = seekTime
      setCurrentTime(seekTime)
    }
  }, [isLoaded])

  // 调整音量
  const handleVolumeChange = useCallback((value: number[]) => {
    const newVolume = value[0]
    setVolume(newVolume)
    if (audioRef.current) {
      audioRef.current.volume = newVolume / 100
    }
    // 取消静音状态
    if (newVolume > 0 && isMuted) {
      setIsMuted(false)
      if (audioRef.current) {
        audioRef.current.muted = false
      }
    }
  }, [isMuted])

  // 播放结束
  const handleEnded = useCallback(() => {
    setIsPlaying(false)
    setCurrentTime(0)
    if (audioRef.current) {
      audioRef.current.currentTime = 0
    }
  }, [])

  // 播放暂停事件（确保状态同步）
  const handlePlay = useCallback(() => {
    setIsPlaying(true)
  }, [])

  const handlePause = useCallback(() => {
    setIsPlaying(false)
  }, [])

  // 格式化时间为 m:ss 格式
  const formatTime = useCallback((time: number) => {
    if (isNaN(time) || !isFinite(time) || time < 0) return '0:00'
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }, [])

  // 无音频时显示等待状态
  if (!src) {
    return (
      <div
        className={cn(
          'flex items-center justify-center rounded-lg border bg-muted/50 p-6',
          className
        )}
      >
        <div className="flex flex-col items-center gap-2">
          <Icons.volume className="h-8 w-8 text-muted-foreground/50" />
          <p className="text-sm text-muted-foreground">等待合成...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn('rounded-lg border bg-card p-4', className)}>
      {/* 隐藏的音频元素 */}
      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onCanPlay={handleCanPlay}
        onDurationChange={handleDurationChange}
        onEnded={handleEnded}
        onPlay={handlePlay}
        onPause={handlePause}
      />

      {/* 播放器主体布局 */}
      <div className="flex items-center gap-3">
        {/* 播放/暂停按钮 */}
        <Button
          variant="outline"
          size="icon"
          className="h-10 w-10 rounded-full shrink-0"
          onClick={togglePlay}
          disabled={!isLoaded}
        >
          {isPlaying ? (
            <Icons.pause className="h-4 w-4" />
          ) : (
            <Icons.play className="h-4 w-4 ml-0.5" />
          )}
        </Button>

        {/* 当前时间 */}
        <span className="text-xs text-muted-foreground w-10 text-right shrink-0 tabular-nums">
          {formatTime(currentTime)}
        </span>

        {/* 进度条 */}
        <div className="flex-1 min-w-0">
          <Slider
            value={[currentTime]}
            max={duration || 1}
            step={0.1}
            onValueChange={handleSeek}
            disabled={!isLoaded || duration === 0}
            className="cursor-pointer"
          />
        </div>

        {/* 总时长 */}
        <span className="text-xs text-muted-foreground w-10 shrink-0 tabular-nums">
          {formatTime(duration)}
        </span>

        {/* 分隔线 */}
        <div className="h-4 w-px bg-border shrink-0" />

        {/* 音量控制 */}
        <div className="flex items-center gap-1 shrink-0">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={toggleMute}
          >
            {isMuted || volume === 0 ? (
              <Icons.volumeMute className="h-4 w-4 text-muted-foreground" />
            ) : (
              <Icons.volume className="h-4 w-4 text-muted-foreground" />
            )}
          </Button>
          <Slider
            value={[isMuted ? 0 : volume]}
            max={100}
            step={1}
            onValueChange={handleVolumeChange}
            className="w-20 cursor-pointer"
          />
        </div>

        {/* 下载按钮 */}
        {onDownload && (
          <>
            <div className="h-4 w-px bg-border shrink-0" />
            <Button
              variant="ghost"
              size="icon"
              onClick={onDownload}
              className="h-8 w-8 shrink-0"
              title="下载音频"
            >
              <Icons.download className="h-4 w-4" />
            </Button>
          </>
        )}
      </div>
    </div>
  )
}