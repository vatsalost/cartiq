import React from 'react'
import { Shield, Clock, Tag, Store, Ban, CheckCircle } from 'lucide-react'
import { Mandate, BudgetBreakdown } from '../../api/types'
import { Badge } from '../common/Badge'

export const MandateCard: React.FC<{
  mandate: Mandate
  breakdown: BudgetBreakdown | null
}> = ({ mandate, breakdown }) => {
  return (
    <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-[#16181D] border border-neutral-200 dark:border-neutral-800 shadow-xs flex flex-col gap-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#98EC6A] dark:bg-[#2CE5B5] flex items-center justify-center text-[#0A2610] dark:text-[#05261F] font-bold">
            <Shield size={18} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-neutral-900 dark:text-white">
                Active Mandate (Version {mandate.version})
              </h3>
              <Badge variant="success" size="sm">
                Active
              </Badge>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
              Approved spending rules and boundaries
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-neutral-500 dark:text-neutral-400">
          <Clock size={13} />
          <span>Expires {new Date(mandate.expires_at).toLocaleDateString()}</span>
        </div>
      </div>

      {/* Spending Limits Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800">
          <div className="text-[11px] font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
            Total Budget
          </div>
          <div className="text-xl font-bold text-neutral-900 dark:text-white mt-1">
            ${mandate.total_budget}
          </div>
          <div className="text-[11px] text-neutral-400 mt-0.5">{mandate.currency} authorized</div>
        </div>

        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-900 dark:text-emerald-300">
          <div className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">
            Available Budget
          </div>
          <div className="text-xl font-bold text-emerald-800 dark:text-emerald-300 mt-1">
            ${breakdown?.available_budget || '0.00'}
          </div>
          <div className="text-[11px] text-emerald-600/80 dark:text-emerald-400/80 mt-0.5">
            Remaining unspent
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800">
          <div className="text-[11px] font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
            Per-Item Cap
          </div>
          <div className="text-xl font-bold text-neutral-900 dark:text-white mt-1">
            ${mandate.per_item_cap}
          </div>
          <div className="text-[11px] text-neutral-400 mt-0.5">Max single item price</div>
        </div>

        <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800">
          <div className="text-[11px] font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
            Price Tolerance
          </div>
          <div className="text-xl font-bold text-neutral-900 dark:text-white mt-1">
            ±{mandate.price_tolerance_pct}%
          </div>
          <div className="text-[11px] text-neutral-400 mt-0.5">Allowed variance at checkout</div>
        </div>
      </div>

      {/* Rules & Permissions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Allowed Categories & Retailers */}
        <div className="flex flex-col gap-3 p-4 rounded-xl bg-neutral-50/70 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800">
          <div>
            <div className="text-xs font-bold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5 mb-2">
              <Tag size={13} className="text-[#98EC6A] dark:text-[#2CE5B5]" />
              <span>Allowed Categories</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {mandate.allowed_categories.map((cat) => (
                <span
                  key={cat}
                  className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-800 dark:text-neutral-200"
                >
                  {cat}
                </span>
              ))}
            </div>
          </div>

          <div className="pt-2 border-t border-neutral-200/50 dark:border-neutral-800">
            <div className="text-xs font-bold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5 mb-2">
              <Store size={13} className="text-[#98EC6A] dark:text-[#2CE5B5]" />
              <span>Approved Retailers</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {mandate.allowed_retailers.map((ret) => (
                <span
                  key={ret}
                  className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-800 dark:text-neutral-200"
                >
                  {ret}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Blocked Categories & Constraints */}
        <div className="flex flex-col gap-3 p-4 rounded-xl bg-neutral-50/70 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800">
          <div>
            <div className="text-xs font-bold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5 mb-2">
              <Ban size={13} className="text-rose-500" />
              <span>Blocked Categories</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {mandate.blocked_categories.map((cat) => (
                <span
                  key={cat}
                  className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400"
                >
                  {cat}
                </span>
              ))}
            </div>
          </div>

          <div className="pt-2 border-t border-neutral-200/50 dark:border-neutral-800">
            <div className="text-xs font-bold text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5 mb-2">
              <CheckCircle size={13} className="text-neutral-400" />
              <span>Purchase Rules</span>
            </div>
            <ul className="text-xs text-neutral-600 dark:text-neutral-400 space-y-1">
              <li>• Max {mandate.max_quantity_per_product} item(s) per order</li>
              <li>• Proposals are locked to active version {mandate.version}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
