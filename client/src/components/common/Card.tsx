import React from 'react'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  variant?: 'default' | 'flat' | 'dark' | 'lime' | 'lavender' | 'subtle'
  className?: string
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  padding = 'md',
  className = '',
  ...props
}) => {
  const paddingStyles = {
    none: 'p-0',
    sm: 'p-3.5',
    md: 'p-5',
    lg: 'p-6 md:p-7',
  }[padding]

  const variantStyles = {
    default:
      'bg-white dark:bg-[#17191C] text-neutral-900 dark:text-neutral-100 border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.04)]',
    flat:
      'bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 text-neutral-900 dark:text-neutral-100',
    subtle:
      'bg-[#F9FAF8] dark:bg-[#15171A] border border-neutral-200/60 dark:border-neutral-800/80 text-neutral-900 dark:text-neutral-100',
    dark:
      'bg-[#17191C] text-white border border-neutral-800 shadow-sm',
    lime:
      'bg-[#F3FCED] dark:bg-[#142316] text-[#133816] dark:text-[#95EB68] border border-[#95EB68]/40 dark:border-[#95EB68]/30',
    lavender:
      'bg-[#F4F5FD] dark:bg-[#1E1F30] text-[#2D3360] dark:text-[#C5CEFF] border border-[#AAB5F8]/40 dark:border-[#AAB5F8]/30',
  }[variant]

  return (
    <div
      className={`rounded-xl md:rounded-2xl transition-colors ${paddingStyles} ${variantStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
