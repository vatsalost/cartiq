import React from 'react'

export type BadgeVariant =
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral'
  | 'lime'
  | 'lavender'

interface BadgeProps {
  children: React.ReactNode
  variant?: BadgeVariant
  className?: string
  size?: 'sm' | 'md'
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  className = '',
  size = 'md',
}) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-0.5 text-xs'

  const variantClasses: Record<BadgeVariant, string> = {
    success:
      'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 font-medium',
    warning:
      'bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20 font-medium',
    danger:
      'bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/20 font-medium',
    info: 'bg-sky-500/10 text-sky-700 dark:text-sky-400 border border-sky-500/20 font-medium',
    neutral:
      'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 border border-neutral-200 dark:border-neutral-700 font-medium',
    lime: 'bg-[#98EC6A] dark:bg-[#153424] text-[#0A3010] dark:text-[#2CE5B5] border border-black/10 dark:border-[#225038] font-semibold',
    lavender:
      'bg-[#AAB5F8] dark:bg-[#232036] text-[#151B4D] dark:text-[#C5CEFF] border border-black/10 dark:border-[#3A3554] font-semibold',
  }

  return (
    <span
      className={`inline-flex items-center justify-center rounded-full transition-colors ${sizeClasses} ${variantClasses[variant]} ${className}`}
    >
      {children}
    </span>
  )
}
