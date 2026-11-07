import React from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { ShieldCheck, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export const CashflowChart: React.FC = () => {
  const { mandate, breakdown } = useAuth()

  const total = parseFloat(mandate?.total_budget || '150.00') || 150.0
  const available = parseFloat(breakdown?.available_budget || '65.02') || 65.02
  const reserved = parseFloat(breakdown?.active_reservations || '49.99') || 49.99
  const captured = parseFloat(breakdown?.captured_spending || '34.99') || 34.99

  const availablePct = Math.round((available / total) * 100)
  const reservedPct = Math.round((reserved / total) * 100)
  const capturedPct = Math.max(0, 100 - availablePct - reservedPct)

  // Monthly spending trajectory data
  const data = [
    { month: 'Jun', spending: 20, budget: 150 },
    { month: 'Jul', spending: 45, budget: 150 },
    { month: 'Aug', spending: 35, budget: 150 },
    { month: 'Sep', spending: 60, budget: 150 },
    { month: 'Oct', spending: 40, budget: 150 },
    { month: 'Nov', spending: 84.98, budget: 150 }, // captured + reserved
  ]

  return (
    <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between h-full min-h-[260px]">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-neutral-100 dark:border-neutral-800">
        <div>
          <div className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
            Spending Trajectory & Utilization
          </div>
          <div className="text-lg font-bold text-neutral-900 dark:text-white mt-0.5">
            ${(captured + reserved).toFixed(2)}{' '}
            <span className="text-xs font-normal text-neutral-400">committed of ${total.toFixed(2)}</span>
          </div>
        </div>

        <Link
          to="/mandate"
          className="text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white flex items-center gap-1 group"
        >
          <span>Mandate v{mandate?.version || 2}</span>
          <ArrowRight size={12} className="group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>

      {/* Chart */}
      <div className="h-36 w-full my-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#95EB68" stopOpacity={0.35} />
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
            <ReferenceLine
              y={total}
              stroke="#AAB5F8"
              strokeDasharray="3 3"
              label={{ value: 'Cap $150', position: 'top', fill: '#8892D6', fontSize: 10 }}
            />
            <Area
              type="monotone"
              dataKey="spending"
              stroke="#95EB68"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#spendGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Segmented bar & legend */}
      <div className="pt-2 border-t border-neutral-100 dark:border-neutral-800">
        <div className="w-full h-1.5 rounded-full bg-neutral-100 dark:bg-neutral-800 overflow-hidden flex mb-2">
          <div
            style={{ width: `${availablePct}%` }}
            className="h-full bg-[#95EB68]"
            title={`Available: $${available.toFixed(2)}`}
          />
          <div
            style={{ width: `${reservedPct}%` }}
            className="h-full bg-[#AAB5F8]"
            title={`Reserved: $${reserved.toFixed(2)}`}
          />
          <div
            style={{ width: `${capturedPct}%` }}
            className="h-full bg-neutral-400 dark:bg-neutral-600"
            title={`Captured: $${captured.toFixed(2)}`}
          />
        </div>

        <div className="flex items-center justify-between text-[11px] text-neutral-500 dark:text-neutral-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#95EB68]" />
            Available: <strong>${available.toFixed(2)}</strong>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#AAB5F8]" />
            Reserved: <strong>${reserved.toFixed(2)}</strong>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-neutral-400 dark:bg-neutral-600" />
            Captured: <strong>${captured.toFixed(2)}</strong>
          </span>
        </div>
      </div>
    </div>
  )
}
