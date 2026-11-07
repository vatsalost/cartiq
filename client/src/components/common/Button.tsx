import React from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'lavender'
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  icon?: React.ReactNode
  loading?: boolean
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  loading = false,
  className = '',
  disabled,
  ...props
}) => {
  const sizeClasses: Record<ButtonSize, string> = {
    xs: 'px-2.5 py-1 text-xs gap-1 rounded-md font-medium',
    sm: 'px-3 py-1.5 text-xs gap-1.5 rounded-lg font-medium',
    md: 'px-3.5 py-2 text-sm gap-2 rounded-lg font-medium',
    lg: 'px-5 py-2.5 text-base gap-2 rounded-xl font-semibold',
  }

  const variantClasses: Record<ButtonVariant, string> = {
    primary:
      'bg-[#95EB68] text-[#17191C] hover:bg-[#86E455] active:bg-[#78D845] border border-[#85E257] shadow-xs font-semibold',
    secondary:
      'bg-[#17191C] text-white hover:bg-[#25282F] active:bg-[#2F333B] dark:bg-white dark:text-[#17191C] dark:hover:bg-neutral-100 border border-transparent shadow-xs',
    lavender:
      'bg-[#EEF0FD] text-[#434D91] hover:bg-[#E2E6FB] border border-[#D5DCFA] dark:bg-[#222438] dark:text-[#AAB5F8] dark:border-[#343754]',
    outline:
      'bg-white dark:bg-[#1C1F24] text-neutral-800 dark:text-neutral-200 border border-neutral-200 dark:border-neutral-700/80 hover:bg-neutral-50 dark:hover:bg-neutral-800 active:bg-neutral-100 shadow-xs',
    ghost:
      'bg-transparent text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800/60',
    danger:
      'bg-rose-50 text-rose-600 hover:bg-rose-100 dark:bg-rose-500/10 dark:text-rose-400 dark:hover:bg-rose-500/20 border border-rose-200 dark:border-rose-500/30',
  }

  return (
    <button
      className={`inline-flex items-center justify-center transition-all duration-150 cursor-pointer select-none disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98] ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin shrink-0" />
      ) : (
        icon && <span className="shrink-0">{icon}</span>
      )}
      {children}
    </button>
  )
}
