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
      card: 'bg-[#98EC6A] dark:bg-gradient-to-br dark:from-[#114039] dark:to-[#0A2624] text-[#0A2610] dark:text-[#2CE5B5] border border-black/15 dark:border-[#1E574F] shadow-[2px_4px_0px_rgba(0,0,0,0.18)] dark:shadow-none',
      iconBox: 'text-[#0A2610] dark:text-[#2CE5B5]',
      label: 'text-[#0A2610]/80 dark:text-[#2CE5B5]/80',
    },
    lavender: {
      card: 'bg-[#AAB5F8] dark:bg-[#322824] text-[#13194B] dark:text-[#EAD7D1] border border-black/15 dark:border-[#4F3C36] shadow-[2px_4px_0px_rgba(0,0,0,0.18)] dark:shadow-none',
      iconBox: 'text-[#13194B] dark:text-[#EAD7D1]',
      label: 'text-[#13194B]/80 dark:text-[#EAD7D1]/80',
    },
    dark: {
      card: 'bg-[#121316] text-white border border-black dark:border-neutral-800 shadow-[2px_4px_0px_rgba(0,0,0,0.22)]',
      iconBox: 'text-white',
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
      className={`rounded-[26px] p-5 md:p-6 flex flex-col justify-between min-h-[160px] transition-transform hover:-translate-y-0.5 ${variantStyles.card}`}
    >
      <div className="flex items-center justify-between">
        <span className={`text-xs font-bold uppercase tracking-wider ${variantStyles.label}`}>
          {title}
        </span>
        <div className={`p-1.5 rounded-full ${variantStyles.iconBox}`}>
          <Icon size={20} strokeWidth={2.5} />
        </div>
      </div>

      <div className="mt-4">
        <div className="text-3xl md:text-4xl font-extrabold tracking-tight">
          {amount}
        </div>
        {subtitle && (
          <p className={`text-xs mt-1 font-medium ${variantStyles.label}`}>
            {subtitle}
          </p>
        )}
      </div>
    </div>
  )
}
