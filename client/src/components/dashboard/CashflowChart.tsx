import React from 'react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  Tooltip,
} from 'recharts'
import { TrendingUp, BarChart3 } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'

const chartData = [
  { period: 'Nov', spend: 20, budget: 150 },
  { period: 'Dec', spend: 45, budget: 150 },
  { period: 'Jan', spend: 35, budget: 150 },
  { period: 'Feb', spend: 60, budget: 150 },
  { period: 'Mar', spend: 40, budget: 150 },
  { period: 'Apr', spend: 50, budget: 150 },
  { period: 'Current', spend: 84.98, budget: 150 },
]

export const CashflowChart: React.FC = () => {
  const { theme } = useTheme()
  const strokeColor = theme === 'dark' ? '#2CE5B5' : '#98EC6A'

  return (
    <div className="rounded-[26px] bg-[#111215] text-white p-5 md:p-6 border border-neutral-800 shadow-[0_8px_30px_rgba(0,0,0,0.3)] flex flex-col justify-between min-h-[220px]">
      {/* Top Header & Stat Counter */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-3xl md:text-4xl font-black tracking-tight text-[#98EC6A] dark:text-[#2CE5B5]">
              $84.98
            </span>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#98EC6A]/20 text-[#98EC6A] dark:text-[#2CE5B5] flex items-center gap-0.5">
              <TrendingUp size={12} />
              +100%
            </span>
          </div>
          <p className="text-xs text-neutral-400 font-medium mt-0.5">
            Total Committed (Captured + Active Reservations)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs px-3 py-1 rounded-full bg-neutral-800/80 border border-neutral-700 text-neutral-300 font-medium">
            Mandate: $150.00
          </span>
        </div>
      </div>

      {/* Center Recharts Line Graph with Glow */}
      <div className="h-28 w-full mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="spendGlow" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={strokeColor} stopOpacity={0.35} />
                <stop offset="95%" stopColor={strokeColor} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="period"
              stroke="#525252"
              fontSize={10}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1E2024',
                borderColor: '#333',
                borderRadius: '12px',
                color: '#fff',
                fontSize: '12px',
              }}
              formatter={(val) => [`$${val}`, 'Committed Spend']}
            />
            <Area
              type="monotone"
              dataKey="spend"
              stroke={strokeColor}
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#spendGlow)"
              dot={{ r: 3, fill: strokeColor, strokeWidth: 1 }}
              activeDot={{ r: 6, fill: strokeColor }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Bottom Mini Metrics Bar matching reference screenshot */}
      <div className="grid grid-cols-2 gap-4 pt-3 border-t border-neutral-800/80 mt-1">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-neutral-800 flex items-center justify-center text-[#98EC6A] dark:text-[#2CE5B5]">
            <BarChart3 size={14} />
          </div>
          <div>
            <div className="text-xs font-bold text-white">$34.99</div>
            <div className="text-[10px] text-neutral-400">Captured Spending</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-neutral-800 flex items-center justify-center text-[#AAB5F8]">
            <BarChart3 size={14} />
          </div>
          <div>
            <div className="text-xs font-bold text-white">$49.99</div>
            <div className="text-[10px] text-neutral-400">Reserved in Pipeline</div>
          </div>
        </div>
      </div>
    </div>
  )
}
