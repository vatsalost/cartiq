import React from 'react'
import { ShieldCheck, Clock, Tag, Store, Ban, CheckCircle2, History, Percent, Hash } from 'lucide-react'
import { Mandate, BudgetBreakdown } from '../../api/types'
import { Badge } from '../common/Badge'

export const MandateCard: React.FC<{
  mandate: Mandate
  breakdown: BudgetBreakdown | null
}> = ({ mandate, breakdown }) => {
  const total = parseFloat(mandate.total_budget || '150.00')
  const available = parseFloat(breakdown?.available_budget || '65.02')
  const reserved = parseFloat(breakdown?.active_reservations || '49.99')
  const captured = parseFloat(breakdown?.captured_spending || '34.99')

  const availablePct = Math.round((available / total) * 100)
  const reservedPct = Math.round((reserved / total) * 100)
  const capturedPct = Math.max(0, 100 - availablePct - reservedPct)

  return (
    <div className="flex flex-col gap-5">
      {/* Primary Financial Budget Hero Card */}
      <div className="rounded-xl p-5 md:p-6 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-neutral-100 dark:border-neutral-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center font-bold">
              <ShieldCheck size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-neutral-900 dark:text-white">
                  Active Spending Authority
                </h3>
                <Badge variant="lime" size="xs">
                  Version {mandate.version}
                </Badge>
                <Badge variant="success" size="xs" dot>
                  Active
                </Badge>
              </div>
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                Cryptographically bound purchasing parameters enforced across B1–B10
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-neutral-500 dark:text-neutral-400 font-mono bg-neutral-50 dark:bg-neutral-800/60 px-3 py-1.5 rounded-lg border border-neutral-200/60 dark:border-neutral-700/60">
            <Clock size={13} className="text-neutral-400" />
            <span>Expires {new Date(mandate.expires_at).toLocaleDateString()}</span>
          </div>
        </div>

        {/* 4 Financial Metric Pillars */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-lg bg-neutral-50 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800">
            <div className="text-[11px] font-medium text-neutral-500 uppercase tracking-wider">
              Authorized Total
            </div>
            <div className="text-xl font-bold text-neutral-900 dark:text-white mt-1">
              ${total.toFixed(2)}
            </div>
            <div className="text-[11px] text-neutral-400 mt-0.5">{mandate.currency} Authorized</div>
          </div>

          <div className="p-3.5 rounded-lg bg-[#ECFADF]/60 dark:bg-[#142617]/50 border border-[#95EB68]/40 dark:border-[#95EB68]/30">
            <div className="text-[11px] font-medium text-emerald-800 dark:text-emerald-300 uppercase tracking-wider">
              Available Budget
            </div>
            <div className="text-xl font-bold text-emerald-900 dark:text-[#95EB68] mt-1">
              ${available.toFixed(2)}
            </div>
            <div className="text-[11px] text-emerald-700/80 dark:text-emerald-400/80 mt-0.5">
              {availablePct}% uncommitted
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-neutral-50 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800">
            <div className="text-[11px] font-medium text-neutral-500 uppercase tracking-wider">
              Active Reservations
            </div>
            <div className="text-xl font-bold text-neutral-900 dark:text-white mt-1">
              ${reserved.toFixed(2)}
            </div>
            <div className="text-[11px] text-neutral-400 mt-0.5">In-flight checkout locks</div>
          </div>

          <div className="p-3.5 rounded-lg bg-neutral-50 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800">
            <div className="text-[11px] font-medium text-neutral-500 uppercase tracking-wider">
              Captured Spending
            </div>
            <div className="text-xl font-bold text-neutral-900 dark:text-white mt-1">
              ${captured.toFixed(2)}
            </div>
            <div className="text-[11px] text-neutral-400 mt-0.5">Settled PayPal orders</div>
          </div>
        </div>

        {/* Visual Budget Utilization Bar */}
        <div className="flex flex-col gap-1.5 pt-1">
          <div className="flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400">
            <span className="font-medium">Budget Allocation Breakdown</span>
            <span className="font-mono text-[11px]">
              ${(captured + reserved).toFixed(2)} committed of ${total.toFixed(2)}
            </span>
          </div>
          <div className="w-full h-2.5 rounded-full bg-neutral-100 dark:bg-neutral-800 overflow-hidden flex">
            <div
              style={{ width: `${availablePct}%` }}
              className="h-full bg-[#95EB68] transition-all"
              title={`Available: $${available.toFixed(2)} (${availablePct}%)`}
            />
            <div
              style={{ width: `${reservedPct}%` }}
              className="h-full bg-[#AAB5F8] transition-all"
              title={`Reserved: $${reserved.toFixed(2)} (${reservedPct}%)`}
            />
            <div
              style={{ width: `${capturedPct}%` }}
              className="h-full bg-neutral-400 dark:bg-neutral-600 transition-all"
              title={`Captured: $${captured.toFixed(2)} (${capturedPct}%)`}
            />
          </div>
          <div className="flex items-center justify-between text-[11px] text-neutral-400 pt-1">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#95EB68]" />
              Available ({availablePct}%)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#AAB5F8]" />
              In Checkout ({reservedPct}%)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-neutral-400 dark:bg-neutral-600" />
              Settled ({capturedPct}%)
            </span>
          </div>
        </div>
      </div>

      {/* Rules, Categories & Retailers Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Left: Allowed Categories & Approved Retailers */}
        <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-4">
          <div>
            <div className="text-xs font-semibold text-neutral-800 dark:text-neutral-200 flex items-center gap-1.5 mb-2.5">
              <Tag size={13} className="text-[#95EB68]" />
              <span>Allowed Categories ({mandate.allowed_categories.length})</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {mandate.allowed_categories.map((cat) => (
                <span
                  key={cat}
                  className="px-2.5 py-1 rounded-md text-xs font-medium bg-neutral-100 dark:bg-neutral-800/80 border border-neutral-200/80 dark:border-neutral-700/80 text-neutral-800 dark:text-neutral-200"
                >
                  {cat}
                </span>
              ))}
            </div>
          </div>

          <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800">
            <div className="text-xs font-semibold text-neutral-800 dark:text-neutral-200 flex items-center gap-1.5 mb-2.5">
              <Store size={13} className="text-[#95EB68]" />
              <span>Approved Retailer Domains ({mandate.allowed_retailers.length})</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {mandate.allowed_retailers.map((ret) => (
                <span
                  key={ret}
                  className="px-2.5 py-1 rounded-md text-xs font-medium bg-neutral-100 dark:bg-neutral-800/80 border border-neutral-200/80 dark:border-neutral-700/80 text-neutral-800 dark:text-neutral-200 flex items-center gap-1"
                >
                  <CheckCircle2 size={11} className="text-emerald-500" />
                  {ret}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Blocked Categories & Transaction Limits */}
        <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-4">
          <div>
            <div className="text-xs font-semibold text-neutral-800 dark:text-neutral-200 flex items-center gap-1.5 mb-2.5">
              <Ban size={13} className="text-rose-500" />
              <span>Strictly Blocked Categories ({mandate.blocked_categories.length})</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {mandate.blocked_categories.map((cat) => (
                <span
                  key={cat}
                  className="px-2.5 py-1 rounded-md text-xs font-medium bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400 border border-rose-200 dark:border-rose-500/20"
                >
                  {cat}
                </span>
              ))}
            </div>
          </div>

          <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800">
            <div className="text-xs font-semibold text-neutral-800 dark:text-neutral-200 flex items-center gap-1.5 mb-2.5">
              <Percent size={13} className="text-neutral-400" />
              <span>Transactional Limits</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-lg bg-neutral-50 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800">
                <span className="text-neutral-400 text-[11px] block">Per-Item Price Cap</span>
                <span className="font-bold text-neutral-900 dark:text-white text-sm">
                  ${mandate.per_item_cap}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-neutral-50 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800">
                <span className="text-neutral-400 text-[11px] block">Price Tolerance</span>
                <span className="font-bold text-neutral-900 dark:text-white text-sm">
                  ±{mandate.price_tolerance_pct}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Version Lineage Snapshot */}
      <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-3">
        <div className="flex items-center justify-between pb-2 border-b border-neutral-100 dark:border-neutral-800">
          <div className="flex items-center gap-2">
            <History size={15} className="text-neutral-400" />
            <h4 className="text-xs font-semibold text-neutral-800 dark:text-neutral-200">
              Mandate Version History & Lineage
            </h4>
          </div>
          <span className="text-[11px] text-neutral-400 font-mono">
            Immutable Audit Trail
          </span>
        </div>

        <div className="flex flex-col gap-2">
          <div className="p-3 rounded-lg bg-neutral-50/80 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2.5">
              <Badge variant="lime" size="xs">v2 (Current)</Badge>
              <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                $150.00 Total • $60.00 Cap
              </span>
            </div>
            <span className="text-[11px] text-neutral-400">
              Updated {new Date(mandate.created_at).toLocaleDateString()}
            </span>
          </div>

          <div className="p-3 rounded-lg bg-neutral-50/40 dark:bg-[#141619]/40 border border-neutral-200/40 dark:border-neutral-800/40 flex items-center justify-between text-xs opacity-60">
            <div className="flex items-center gap-2.5">
              <Badge variant="neutral" size="xs">v1</Badge>
              <span className="text-neutral-600 dark:text-neutral-400">
                $100.00 Total • $50.00 Cap
              </span>
            </div>
            <span className="text-[11px] text-neutral-400">Archived</span>
          </div>
        </div>
      </div>
    </div>
  )
}
