import React from 'react'
import {
  ShieldCheck,
  Check,
  X,
  Lock,
  Layers,
  Sparkles,
  Info,
} from 'lucide-react'
import { Mandate, BudgetBreakdown } from '../../api/types'

export const MandateCard: React.FC<{
  mandate: Mandate
  breakdown: BudgetBreakdown | null
  onReset?: () => void
}> = ({ mandate, breakdown, onReset }) => {
  const total = parseFloat(mandate.total_budget || '0.00')
  const available = parseFloat(breakdown?.available_budget || mandate.total_budget || '0.00')
  const reserved = parseFloat(breakdown?.active_reservations || '0.00')
  const captured = parseFloat(breakdown?.captured_spending || '0.00')

  const utilized = captured + reserved
  const utilizedPct = total > 0 ? Math.round((utilized / total) * 100) : 0

  const allowedCategories = mandate.allowed_categories || []
  const approvedRetailers = mandate.allowed_retailers || []
  const blockedCategories = mandate.blocked_categories || []

  return (
    <div className="flex flex-col gap-6">
      {/* Top Row: Large Dark Authorized Budget Card (Left) + Stacked Cap & Tolerance (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* Left (7 cols): Large Dark Hero Card */}
        <div className="lg:col-span-7 rounded-2xl p-6 bg-[#17191C] text-white border border-neutral-800 shadow-sm flex flex-col justify-between min-h-[220px]">
          <div>
            <div className="text-[12px] font-medium text-neutral-400">
              Total Authorized Budget
            </div>
            <div className="text-[32px] sm:text-[36px] font-bold tracking-tight text-white mt-1 tabular-nums">
              ${total.toFixed(2)}
            </div>
            <div className="text-[12px] text-neutral-400 mt-1 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#95EB68]" />
              <span>Active Mandate v{mandate.version || 2} • Created May 1, 2026</span>
            </div>
          </div>

          <div className="mt-6">
            {/* Utilization Bar */}
            <div className="flex items-center justify-between text-xs text-neutral-400 mb-1.5 font-medium">
              <span className="tabular-nums">{utilizedPct}% utilized</span>
              <span className="tabular-nums">${utilized.toFixed(2)} / ${total.toFixed(2)}</span>
            </div>
            <div className="w-full h-2 rounded-full bg-neutral-800 overflow-hidden flex">
              <div
                style={{ width: `${(captured / total) * 100}%` }}
                className="h-full bg-neutral-400"
                title={`Captured: $${captured.toFixed(2)}`}
              />
              <div
                style={{ width: `${(reserved / total) * 100}%` }}
                className="h-full bg-[#AAB5F8]"
                title={`Reserved: $${reserved.toFixed(2)}`}
              />
              <div
                style={{ width: `${(available / total) * 100}%` }}
                className="h-full bg-[#95EB68]"
                title={`Available: $${available.toFixed(2)}`}
              />
            </div>

            {/* 3 Metrics Row */}
            <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-neutral-800/80 text-xs">
              <div>
                <div className="text-neutral-400 text-[11px]">Available</div>
                <div className="font-bold text-[#95EB68] text-sm mt-0.5 tabular-nums">
                  ${available.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-neutral-400 text-[11px]">Captured</div>
                <div className="font-bold text-white text-sm mt-0.5 tabular-nums">
                  ${captured.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-neutral-400 text-[11px]">Reserved</div>
                <div className="font-bold text-[#AAB5F8] text-sm mt-0.5 tabular-nums">
                  ${reserved.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right (5 cols): Stacked Cards (Per-Item Cap & Price Tolerance) */}
        <div className="lg:col-span-5 flex flex-col gap-4 justify-between">
          {/* Card 1: Per-Item Cap */}
          <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
                Per-Item Cap
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 font-mono">
                Hard Boundary
              </span>
            </div>
            <div className="my-2">
              <div className="text-[30px] font-bold text-neutral-900 dark:text-white tabular-nums leading-none">
                ${mandate.per_item_cap || '60.00'}
              </div>
            </div>
            <div className="text-[12px] text-neutral-500 dark:text-neutral-400">
              Maximum single item price Carti can purchase without additional approval
            </div>
          </div>

          {/* Card 2: Price Tolerance */}
          <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
                Price Tolerance
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 font-mono">
                Checkout Lock
              </span>
            </div>
            <div className="my-2">
              <div className="text-[30px] font-bold text-neutral-900 dark:text-white tabular-nums leading-none">
                ±{Number(mandate.price_tolerance_pct) <= 0.5 ? Math.round(Number(mandate.price_tolerance_pct) * 100) : Math.round(Number(mandate.price_tolerance_pct) || 10)}%
              </div>
            </div>
            <div className="text-[12px] text-neutral-500 dark:text-neutral-400">
              Allowed price variance between proposal and final checkout
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: Purchasing Permissions (Left) + Purchasing Restrictions (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* Left (6 cols): Purchasing Permissions */}
        <div className="lg:col-span-6 rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-4">
          <div className="pb-3 border-b border-neutral-100 dark:border-neutral-800">
            <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
              Purchasing Permissions
            </h3>
            <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
              Allowed categories & retailers Carti is authorized to search and buy from
            </p>
          </div>

          {/* Allowed Categories */}
          <div>
            <div className="text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Allowed Categories
            </div>
            <div className="flex flex-wrap gap-2">
              {allowedCategories.length > 0 ? (
                allowedCategories.map((cat) => (
                  <span
                    key={cat}
                    className="px-2.5 py-1 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 text-xs font-medium flex items-center gap-1.5"
                  >
                    <Check size={14} strokeWidth={2} className="text-[#1D4A18] dark:text-[#95EB68]" />
                    <span>{cat}</span>
                  </span>
                ))
              ) : (
                <span className="text-xs text-neutral-400 italic">All product categories permitted</span>
              )}
            </div>
          </div>

          {/* Approved Retailers */}
          <div className="pt-2">
            <div className="text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Approved Retailers
            </div>
            <div className="flex flex-wrap gap-2">
              {approvedRetailers.length > 0 ? (
                approvedRetailers.map((ret) => (
                  <span
                    key={ret}
                    className="px-2.5 py-1 rounded-lg bg-neutral-50 dark:bg-neutral-800/60 border border-neutral-200/70 dark:border-neutral-700/60 text-neutral-700 dark:text-neutral-300 text-xs font-medium"
                  >
                    {ret}
                  </span>
                ))
              ) : (
                <span className="text-xs text-neutral-400 italic">All authorized merchants permitted</span>
              )}
            </div>
          </div>
        </div>

        {/* Right (6 cols): Purchasing Restrictions */}
        <div className="lg:col-span-6 rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-4">
          <div className="pb-3 border-b border-neutral-100 dark:border-neutral-800">
            <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
              Purchasing Restrictions
            </h3>
            <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
              Hard boundaries enforced by deterministic guardrails (B8)
            </p>
          </div>

          {/* Blocked Categories */}
          <div>
            <div className="text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Blocked Categories
            </div>
            <div className="flex flex-wrap gap-2">
              {blockedCategories.length > 0 ? (
                blockedCategories.map((cat) => (
                  <span
                    key={cat}
                    className="px-2.5 py-1 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/40 text-rose-700 dark:text-rose-400 text-xs font-medium flex items-center gap-1.5"
                  >
                    <X size={14} strokeWidth={2} className="text-rose-600 dark:text-rose-400" />
                    <span>{cat}</span>
                  </span>
                ))
              ) : (
                <span className="text-xs text-neutral-400 italic">No categories blocked</span>
              )}
            </div>
          </div>

          {/* Guardrail Rules List */}
          <div className="pt-2">
            <div className="text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Guardrail Rules
            </div>
            <div className="space-y-1.5 text-xs text-neutral-600 dark:text-neutral-400">
              <div className="flex items-center justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span>Max Quantity</span>
                <span className="font-semibold text-neutral-900 dark:text-white">
                  {mandate.max_quantity_per_product || 1} per item
                </span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span>Requires Stock Verification</span>
                <span className="font-semibold text-neutral-900 dark:text-white">Yes (real-time)</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span>Auto-Refund on Delivery Failure</span>
                <span className="font-semibold text-neutral-900 dark:text-white">Enabled</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span>Cryptographic Audit Trail</span>
                <span className="font-mono text-[11px] text-neutral-900 dark:text-white">SHA-256 chained</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span>Mandate Version</span>
                <span className="font-mono text-[11px] text-neutral-900 dark:text-white">
                  v{mandate.version || 2} (active)
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
