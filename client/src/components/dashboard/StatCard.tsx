import React from 'react'
import { Badge } from '../common/Badge'

export interface StatCardProps {
  title: string
  amount: string
  subtitle?: string
  badge?: {
    text: string
    variant?: 'success' | 'warning' | 'lime' | 'lavender' | 'neutral'
  }
  icon?: React.ReactNode
  variant?: 'default' | 'accent'
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  amount,
  subtitle,
  badge,
  icon,
  variant = 'default',
}) => {
  return (
    <div
      className={`rounded-xl p-4 sm:p-5 flex flex-col justify-between transition-all border ${
        variant === 'accent'
          ? 'bg-gradient-to-b from-[#ECFADF]/60 to-white dark:from-[#132817]/40 dark:to-[#17191C] border-[#95EB68]/50 dark:border-[#95EB68]/30 shadow-xs'
          : 'bg-white dark:bg-[#17191C] border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)]'
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
          {title}
        </span>
        {icon && (
          <div className="text-neutral-400 dark:text-neutral-500">
            {icon}
          </div>
        )}
      </div>

      <div className="my-2.5">
        <div className="text-2xl sm:text-[26px] font-bold tracking-tight text-neutral-900 dark:text-white">
          {amount}
        </div>
      </div>

      <div className="flex items-center justify-between gap-2 pt-1 border-t border-neutral-100 dark:border-neutral-800/60 text-xs">
        {subtitle && (
          <span className="text-[11px] text-neutral-500 dark:text-neutral-400 truncate">
            {subtitle}
          </span>
        )}
        {badge && (
          <Badge variant={badge.variant || 'neutral'} size="xs">
            {badge.text}
          </Badge>
        )}
      </div>
    </div>
  )
}
