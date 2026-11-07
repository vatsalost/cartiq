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
  size?: 'xs' | 'sm' | 'md'
  dot?: boolean
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  className = '',
  size = 'sm',
  dot = false,
}) => {
  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-[10px] gap-1',
    sm: 'px-2.5 py-0.5 text-xs gap-1.5',
    md: 'px-3 py-1 text-xs gap-1.5',
  }[size]

  const variantClasses: Record<BadgeVariant, { container: string; dot: string }> = {
    success: {
      container:
        'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20 font-medium',
      dot: 'bg-emerald-500',
    },
    warning: {
      container:
        'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20 font-medium',
      dot: 'bg-amber-500',
    },
    danger: {
      container:
        'bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400 border border-rose-200 dark:border-rose-500/20 font-medium',
      dot: 'bg-rose-500',
    },
    info: {
      container:
        'bg-sky-50 text-sky-700 dark:bg-sky-500/10 dark:text-sky-400 border border-sky-200 dark:border-sky-500/20 font-medium',
      dot: 'bg-sky-500',
    },
    neutral: {
      container:
        'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400 border border-neutral-200 dark:border-neutral-700/80 font-medium',
      dot: 'bg-neutral-400',
    },
    lime: {
      container:
        'bg-[#ECFADF] text-[#1D4A18] dark:bg-[#153424] dark:text-[#95EB68] border border-[#95EB68]/40 dark:border-[#95EB68]/30 font-semibold',
      dot: 'bg-[#95EB68]',
    },
    lavender: {
      container:
        'bg-[#EEF0FD] text-[#343C78] dark:bg-[#202236] dark:text-[#C5CEFF] border border-[#AAB5F8]/40 dark:border-[#AAB5F8]/30 font-semibold',
      dot: 'bg-[#AAB5F8]',
    },
  }

  const { container, dot: dotColor } = variantClasses[variant]

  return (
    <span
      className={`inline-flex items-center justify-center rounded-md transition-colors ${sizeClasses} ${container} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`} />}
      {children}
    </span>
  )
}
