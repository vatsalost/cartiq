import React from 'react'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  icon?: React.ReactNode
  helperText?: string
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  icon,
  helperText,
  className = '',
  ...props
}) => {
  return (
    <div className="w-full flex flex-col gap-1.5">
      {label && (
        <label className="text-xs font-semibold tracking-wide uppercase text-neutral-600 dark:text-neutral-400">
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {icon && (
          <div className="absolute left-4 text-neutral-400 dark:text-neutral-500 pointer-events-none">
            {icon}
          </div>
        )}
        <input
          className={`w-full rounded-full bg-white dark:bg-[#1C1E24] text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 dark:placeholder-neutral-500 border text-sm transition-all py-2.5 px-4 outline-hidden ${
            icon ? 'pl-11' : ''
          } ${
            error
              ? 'border-rose-500 focus:ring-2 focus:ring-rose-500/20'
              : 'border-neutral-200 dark:border-neutral-700/80 focus:border-neutral-400 dark:focus:border-neutral-500 focus:ring-2 focus:ring-neutral-200/50 dark:focus:ring-neutral-700/40'
          } ${className}`}
          {...props}
        />
      </div>
      {error ? (
        <span className="text-xs text-rose-500 font-medium pl-2">{error}</span>
      ) : helperText ? (
        <span className="text-xs text-neutral-500 dark:text-neutral-400 pl-2">{helperText}</span>
      ) : null}
    </div>
  )
}
