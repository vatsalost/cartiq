import React from 'react'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  variant?: 'default' | 'flat' | 'dark' | 'lime' | 'lavender'
  className?: string
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  className = '',
  ...props
}) => {
  const variantStyles = {
    default:
      'bg-white dark:bg-[#16181D] text-neutral-900 dark:text-neutral-100 border border-neutral-200 dark:border-neutral-800 shadow-xs',
    flat:
      'bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/80 dark:border-neutral-800 text-neutral-900 dark:text-neutral-100',
    dark:
      'bg-[#111215] text-white border border-neutral-800 shadow-xs',
    lime:
      'bg-[#98EC6A] dark:bg-[#143228] text-[#0A2810] dark:text-[#2CE5B5] border border-black/10 dark:border-[#1E574F]',
    lavender:
      'bg-[#AAB5F8] dark:bg-[#282538] text-[#13194B] dark:text-[#D5DCFF] border border-black/10 dark:border-[#403B5C]',
  }[variant]

  return (
    <div
      className={`rounded-2xl transition-colors p-5 md:p-6 ${variantStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
