import React from 'react'
import { Shield, CheckCircle2, Clock, DollarSign, Tag, Store } from 'lucide-react'
import { Mandate, BudgetBreakdown } from '../../api/types'
import { Badge } from '../common/Badge'

export const MandateCard: React.FC<{
  mandate: Mandate
  breakdown: BudgetBreakdown | null
}> = ({ mandate, breakdown }) => {
  return (
    <div className="rounded-[28px] p-6 bg-white dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800 shadow-[0_4px_24px_rgba(0,0,0,0.03)] flex flex-col gap-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[#98EC6A] dark:bg-[#2CE5B5] flex items-center justify-center text-[#0A2610] dark:text-[#05261F] font-bold">
            <Shield size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-black text-neutral-900 dark:text-white">
                Spending Mandate
              </h2>
              <Badge variant="lime" size="sm">
                v{mandate.version}
              </Badge>
              <Badge variant="success" size="sm">
                Active
              </Badge>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
              Defines authoritative autonomous spending boundaries
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400">
          <Clock size={14} />
          <span>
            Expires {new Date(mandate.expires_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* Numerical Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/60 dark:border-neutral-800">
          <div className="text-[11px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            Total Budget
          </div>
          <div className="text-2xl font-black text-neutral-900 dark:text-white mt-1">
            ${mandate.total_budget}
          </div>
          <div className="text-[11px] text-neutral-400 mt-0.5">{mandate.currency} Authorized</div>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-900 dark:text-emerald-300">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
            Available Budget
          </div>
          <div className="text-2xl font-black text-emerald-800 dark:text-emerald-300 mt-1">
            ${breakdown?.available_budget || '0.00'}
          </div>
          <div className="text-[11px] text-emerald-600/80 dark:text-emerald-400/80 mt-0.5">
            Remaining spendable
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/60 dark:border-neutral-800">
          <div className="text-[11px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            Per-Item Cap
          </div>
          <div className="text-2xl font-black text-neutral-900 dark:text-white mt-1">
            ${mandate.per_item_cap}
          </div>
          <div className="text-[11px] text-neutral-400 mt-0.5">Max single product price</div>
        </div>

        <div className="p-4 rounded-2xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/60 dark:border-neutral-800">
          <div className="text-[11px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            Price Tolerance
          </div>
          <div className="text-2xl font-black text-neutral-900 dark:text-white mt-1">
            ±{mandate.price_tolerance_pct}%
          </div>
          <div className="text-[11px] text-neutral-400 mt-0.5">Retailer price change limit</div>
        </div>
      </div>

      {/* Allowed and Blocked Rules Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        {/* Allowed Categories & Retailers */}
        <div className="flex flex-col gap-2 p-4 rounded-2xl bg-neutral-50/70 dark:bg-[#1A1D23] border border-neutral-200/60 dark:border-neutral-800">
          <div className="text-xs font-bold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5">
            <Tag size={14} className="text-[#98EC6A] dark:text-[#2CE5B5]" />
            <span>Allowed Categories</span>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {mandate.allowed_categories.map((cat) => (
              <span
                key={cat}
                className="px-2.5 py-1 rounded-full text-xs font-semibold bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-800 dark:text-neutral-200 shadow-2xs"
              >
                {cat}
              </span>
            ))}
          </div>

          <div className="text-xs font-bold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5 mt-3">
            <Store size={14} className="text-[#98EC6A] dark:text-[#2CE5B5]" />
            <span>Approved Retailers</span>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {mandate.allowed_retailers.map((ret) => (
              <span
                key={ret}
                className="px-2.5 py-1 rounded-full text-xs font-semibold bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-800 dark:text-neutral-200 shadow-2xs"
              >
                {ret}
              </span>
            ))}
          </div>
        </div>

        {/* Blocked Guardrails & Safety Restrictions */}
        <div className="flex flex-col gap-2 p-4 rounded-2xl bg-neutral-50/70 dark:bg-[#1A1D23] border border-neutral-200/60 dark:border-neutral-800">
          <div className="text-xs font-bold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5">
            <CheckCircle2 size={14} className="text-rose-500" />
            <span>Blocked Categories (Strict Guardrails)</span>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {mandate.blocked_categories.map((cat) => (
              <span
                key={cat}
                className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400"
              >
                ✕ {cat}
              </span>
            ))}
          </div>

          <div className="text-xs font-bold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5 mt-3">
            <DollarSign size={14} className="text-neutral-400" />
            <span>Quantity & Lineage Constraints</span>
          </div>
          <ul className="text-xs text-neutral-600 dark:text-neutral-400 space-y-1 mt-0.5">
            <li>• Maximum {mandate.max_quantity_per_product} unit(s) per product offer</li>
            <li>• Revalidations lock previous proposals to exact mandate version {mandate.version}</li>
            <li>• Server-side Decimal math guarantees zero floating point rounding errors</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
