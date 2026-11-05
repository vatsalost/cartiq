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
      'bg-white dark:bg-[#16181D] text-neutral-900 dark:text-neutral-100 border border-neutral-200/80 dark:border-neutral-800/90 shadow-[0_4px_20px_rgba(0,0,0,0.03)] dark:shadow-none',
    flat:
      'bg-neutral-50/70 dark:bg-[#1A1D23] border border-neutral-200/60 dark:border-neutral-800/80 text-neutral-900 dark:text-neutral-100',
    dark:
      'bg-[#111215] text-white border border-neutral-800 shadow-[0_8px_24px_rgba(0,0,0,0.25)]',
    lime:
      'bg-[#98EC6A] dark:bg-gradient-to-br dark:from-[#133F39] dark:to-[#0A2624] text-[#0A2810] dark:text-[#2CE5B5] border border-black/15 dark:border-[#1E574F] shadow-[2px_3px_0px_rgba(0,0,0,0.18)] dark:shadow-none',
    lavender:
      'bg-[#AAB5F8] dark:bg-[#2B2320] text-[#13194B] dark:text-[#EAD7D1] border border-black/15 dark:border-[#4A3B37] shadow-[2px_3px_0px_rgba(0,0,0,0.18)] dark:shadow-none',
  }[variant]

  return (
    <div
      className={`rounded-[22px] transition-colors p-5 md:p-6 ${variantStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
