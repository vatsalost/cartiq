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
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-xs'

  const variantClasses: Record<BadgeVariant, string> = {
    success:
      'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30 font-medium',
    warning:
      'bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30 font-medium',
    danger:
      'bg-rose-500/15 text-rose-700 dark:text-rose-400 border border-rose-500/30 font-medium',
    info: 'bg-sky-500/15 text-sky-700 dark:text-sky-400 border border-sky-500/30 font-medium',
    neutral:
      'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700 font-medium',
    lime: 'bg-[#98EC6A] text-[#0A3010] border border-[#7edb4d] font-semibold shadow-xs',
    lavender:
      'bg-[#AAB5F8] text-[#151B4D] border border-[#8f9df0] font-semibold shadow-xs',
  }

  return (
    <span
      className={`inline-flex items-center justify-center rounded-full transition-colors ${sizeClasses} ${variantClasses[variant]} ${className}`}
    >
      {children}
    </span>
  )
}
