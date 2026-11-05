import React from 'react'
import { Shield, ArrowRight } from 'lucide-react'
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

  return (
    <div className="rounded-2xl bg-[#111215] text-white p-5 md:p-6 border border-neutral-800 shadow-xs flex flex-col justify-between h-full min-h-[180px]">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-neutral-800">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-neutral-400">
            Mandate Budget Utilization
          </span>
          <div className="text-xl sm:text-2xl font-extrabold text-white mt-0.5">
            ${total.toFixed(2)}{' '}
            <span className="text-xs font-normal text-neutral-400">{mandate?.currency || 'USD'} Total</span>
          </div>
        </div>

        <Link
          to="/mandate"
          className="text-xs font-medium text-[#98EC6A] dark:text-[#2CE5B5] hover:underline flex items-center gap-1"
        >
          <span>Mandate v{mandate?.version || 2}</span>
          <ArrowRight size={12} />
        </Link>
      </div>

      {/* Segmented Distribution Bar */}
      <div className="my-4">
        <div className="w-full h-3 rounded-full bg-neutral-800 overflow-hidden flex">
          <div
            style={{ width: `${availablePct}%` }}
            className="h-full bg-[#98EC6A] dark:bg-[#2CE5B5] transition-all duration-300"
            title={`Available: $${available.toFixed(2)} (${availablePct}%)`}
          />
          <div
            style={{ width: `${reservedPct}%` }}
            className="h-full bg-[#AAB5F8] dark:bg-[#7987FF] transition-all duration-300"
            title={`Reserved: $${reserved.toFixed(2)} (${reservedPct}%)`}
          />
          <div
            style={{ width: `${capturedPct}%` }}
            className="h-full bg-neutral-500 transition-all duration-300"
            title={`Captured: $${captured.toFixed(2)} (${capturedPct}%)`}
          />
        </div>
      </div>

      {/* Breakdown Legend */}
      <div className="grid grid-cols-3 gap-2 pt-2 text-xs">
        <div>
          <div className="flex items-center gap-1.5 text-neutral-400 text-[11px]">
            <span className="w-2 h-2 rounded-full bg-[#98EC6A] dark:bg-[#2CE5B5]" />
            <span>Available</span>
          </div>
          <div className="font-bold text-white mt-0.5">${available.toFixed(2)}</div>
        </div>

        <div>
          <div className="flex items-center gap-1.5 text-neutral-400 text-[11px]">
            <span className="w-2 h-2 rounded-full bg-[#AAB5F8] dark:bg-[#7987FF]" />
            <span>In Checkout</span>
          </div>
          <div className="font-bold text-white mt-0.5">${reserved.toFixed(2)}</div>
        </div>

        <div>
          <div className="flex items-center gap-1.5 text-neutral-400 text-[11px]">
            <span className="w-2 h-2 rounded-full bg-neutral-500" />
            <span>Settled</span>
          </div>
          <div className="font-bold text-white mt-0.5">${captured.toFixed(2)}</div>
        </div>
      </div>
    </div>
  )
}
