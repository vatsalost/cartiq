import React from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { useAuth } from '../../context/AuthContext'

export const SpendingOverviewCard: React.FC = () => {
  const { mandate, breakdown } = useAuth()

  const total = parseFloat(mandate?.total_budget || '150.00') || 150.0
  const available = parseFloat(breakdown?.available_budget || '65.02') || 65.02
  const reserved = parseFloat(breakdown?.active_reservations || '49.99') || 49.99
  const captured = parseFloat(breakdown?.captured_spending || '34.99') || 34.99

  const utilized = captured + reserved
  const utilizedPct = Math.round((utilized / total) * 100)

  // Trajectory mock points leading to current month
  const trajectoryData = [
    { month: 'Jun', spending: 20 },
    { month: 'Jul', spending: 45 },
    { month: 'Aug', spending: 35 },
    { month: 'Sep', spending: 60 },
    { month: 'Oct', spending: 40 },
    { month: 'Nov', spending: 84.98 },
  ]

  // Donut chart segments
  const pieData = [
    { name: 'Captured', value: captured, color: '#17191C' },
    { name: 'Reserved', value: reserved, color: '#AAB5F8' },
    { name: 'Available', value: available, color: '#95EB68' },
  ]

  return (
    <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-4">
      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-neutral-100 dark:border-neutral-800 gap-2">
        <div>
          <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
            Spending Overview
          </h3>
          <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
            Trajectory & allocation against mandate limits
          </p>
        </div>

        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 self-start sm:self-auto">
          <span>Total Mandate:</span>
          <span className="font-semibold text-neutral-900 dark:text-white tabular-nums">${total.toFixed(2)}</span>
        </div>
      </div>

      {/* Main Grid: Area Chart (Left) + Donut & Ledger (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Left: Trajectory Area Chart */}
        <div className="lg:col-span-7 h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trajectoryData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
              <defs>
                <linearGradient id="spendingGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#95EB68" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#95EB68" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="month"
                stroke="#9CA3AF"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#9CA3AF"
                fontSize={10}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `$${v}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#17191C',
                  borderColor: '#262930',
                  borderRadius: '8px',
                  fontSize: '11px',
                  color: '#fff',
                }}
                formatter={(value: any) => [`$${value}`, 'Spending']}
              />
              <Area
                type="monotone"
                dataKey="spending"
                stroke="#95EB68"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#spendingGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Right: Donut Chart & Breakdown Ledger */}
        <div className="lg:col-span-5 flex flex-col sm:flex-row lg:flex-row items-center justify-center gap-6 p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-100 dark:border-neutral-800">
          {/* Circular Donut with Centered % */}
          <div className="relative w-32 h-32 flex items-center justify-center shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={42}
                  outerRadius={58}
                  paddingAngle={3}
                  dataKey="value"
                  startAngle={90}
                  endAngle={-270}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>

            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-[26px] font-bold text-neutral-900 dark:text-white leading-none tabular-nums">
                {utilizedPct}%
              </span>
              <span className="text-[10px] text-neutral-500 dark:text-neutral-400 mt-0.5 font-medium">
                Utilized
              </span>
            </div>
          </div>

          {/* Ledger List */}
          <div className="flex flex-col gap-2 w-full text-xs">
            <div className="flex items-center justify-between text-neutral-600 dark:text-neutral-400">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#17191C] dark:bg-neutral-400" />
                <span>Captured</span>
              </span>
              <span className="font-semibold text-neutral-900 dark:text-white tabular-nums">${captured.toFixed(2)}</span>
            </div>

            <div className="flex items-center justify-between text-neutral-600 dark:text-neutral-400">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#AAB5F8]" />
                <span>Reserved</span>
              </span>
              <span className="font-semibold text-neutral-900 dark:text-white tabular-nums">${reserved.toFixed(2)}</span>
            </div>

            <div className="flex items-center justify-between text-neutral-600 dark:text-neutral-400">
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#95EB68]" />
                <span>Available</span>
              </span>
              <span className="font-semibold text-[#1D4A18] dark:text-[#95EB68] tabular-nums">${available.toFixed(2)}</span>
            </div>

            <div className="pt-2 border-t border-neutral-200 dark:border-neutral-700/60 flex items-center justify-between font-medium">
              <span className="text-neutral-500 dark:text-neutral-400">Total Budget</span>
              <span className="font-bold text-neutral-900 dark:text-white tabular-nums">${total.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
