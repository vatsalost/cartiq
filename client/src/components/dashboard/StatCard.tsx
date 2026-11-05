import React from 'react'
import { ArrowUpRight, ArrowDownRight, ArrowRightLeft } from 'lucide-react'

export interface StatCardProps {
  title: string
  amount: string
  subtitle?: string
  trend?: string
  variant: 'lime' | 'lavender' | 'dark'
  iconType?: 'up' | 'down' | 'neutral'
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  amount,
  subtitle,
  variant,
  iconType = 'up',
}) => {
  const variantStyles = {
    lime: {
      card: 'bg-[#98EC6A] dark:bg-[#143228] text-[#0A2610] dark:text-[#2CE5B5] border border-black/10 dark:border-[#1E574F]',
      iconBox: 'text-[#0A2610] dark:text-[#2CE5B5] bg-black/5 dark:bg-white/5',
      label: 'text-[#0A2610]/70 dark:text-[#2CE5B5]/70',
    },
    lavender: {
      card: 'bg-[#AAB5F8] dark:bg-[#201D30] text-[#13194B] dark:text-[#D5DCFF] border border-black/10 dark:border-[#383354]',
      iconBox: 'text-[#13194B] dark:text-[#D5DCFF] bg-black/5 dark:bg-white/5',
      label: 'text-[#13194B]/70 dark:text-[#D5DCFF]/70',
    },
    dark: {
      card: 'bg-[#121316] text-white border border-neutral-800',
      iconBox: 'text-neutral-400 bg-white/5',
      label: 'text-neutral-400',
    },
  }[variant]

  const Icon = {
    up: ArrowUpRight,
    down: ArrowDownRight,
    neutral: ArrowRightLeft,
  }[iconType]

  return (
    <div
      className={`rounded-2xl p-4 sm:p-5 flex flex-col justify-between transition-colors shadow-xs ${variantStyles.card}`}
    >
      <div className="flex items-center justify-between">
        <span className={`text-[11px] font-bold uppercase tracking-wider ${variantStyles.label}`}>
          {title}
        </span>
        <div className={`p-1 rounded-full ${variantStyles.iconBox}`}>
          <Icon size={16} />
        </div>
      </div>

      <div className="mt-3">
        <div className="text-2xl sm:text-3xl font-extrabold tracking-tight">
          {amount}
        </div>
        {subtitle && (
          <p className={`text-xs mt-0.5 font-medium ${variantStyles.label}`}>
            {subtitle}
          </p>
        )}
      </div>
    </div>
  )
}
