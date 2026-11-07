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
        <label className="text-xs font-medium text-neutral-700 dark:text-neutral-300">
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {icon && (
          <div className="absolute left-3.5 text-neutral-400 dark:text-neutral-500 pointer-events-none flex items-center">
            {icon}
          </div>
        )}
        <input
          className={`w-full rounded-lg bg-white dark:bg-[#1C1F24] text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 dark:placeholder-neutral-500 border text-sm transition-all py-2 px-3.5 outline-hidden ${
            icon ? 'pl-9' : ''
          } ${
            error
              ? 'border-rose-400 focus:ring-2 focus:ring-rose-500/20'
              : 'border-neutral-200 dark:border-neutral-700/80 focus:border-[#95EB68] dark:focus:border-[#95EB68] focus:ring-2 focus:ring-[#95EB68]/20'
          } ${className}`}
          {...props}
        />
      </div>
      {error ? (
        <span className="text-xs text-rose-500 font-medium">{error}</span>
      ) : helperText ? (
        <span className="text-xs text-neutral-500 dark:text-neutral-400">{helperText}</span>
      ) : null}
    </div>
  )
}
