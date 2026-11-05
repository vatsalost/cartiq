import React from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'dark' | 'outline' | 'danger' | 'ghost'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: 'sm' | 'md' | 'lg'
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
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-2.5 text-base',
  }[size]

  const variantClasses: Record<ButtonVariant, string> = {
    primary:
      'bg-[#98EC6A] dark:bg-[#2CE5B5] text-[#0A2610] dark:text-[#05261F] font-semibold hover:brightness-105 active:scale-[0.98] border border-black/10 dark:border-transparent shadow-xs',
    secondary:
      'bg-[#AAB5F8] dark:bg-neutral-800 text-[#151B4D] dark:text-neutral-200 font-medium hover:brightness-105 active:scale-[0.98] border border-black/5 dark:border-neutral-700',
    dark:
      'bg-[#121316] text-white hover:bg-neutral-800 active:scale-[0.98] font-medium border border-neutral-800 shadow-xs',
    outline:
      'bg-white dark:bg-[#1C1E22] text-neutral-800 dark:text-neutral-200 border border-neutral-300 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-800 active:scale-[0.98] font-medium shadow-xs',
    danger:
      'bg-rose-500 text-white hover:bg-rose-600 active:scale-[0.98] font-medium border border-rose-600 shadow-xs',
    ghost:
      'bg-transparent text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 font-medium',
  }

  return (
    <button
      className={`inline-flex items-center justify-center gap-1.5 rounded-full cursor-pointer transition-all duration-150 disabled:opacity-50 disabled:pointer-events-none select-none ${sizeClasses} ${variantClasses[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        icon
      )}
      {children}
    </button>
  )
}
