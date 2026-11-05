import React, { useState } from 'react'
import {
  FileText,
  Scale,
  ShoppingBag,
  History as HistoryIcon,
  Search,
  ExternalLink,
  ShieldCheck,
  CheckCircle,
  XCircle,
} from 'lucide-react'
import { ShoppingRequest, CandidateProduct, Order, AuditEvent } from '../../api/types'
import { Badge } from '../common/Badge'

interface HistoryTabsProps {
  requests: ShoppingRequest[]
  candidates: CandidateProduct[]
  orders: Order[]
  auditEvents: AuditEvent[]
}

export const HistoryTabs: React.FC<HistoryTabsProps> = ({
  requests,
  candidates,
  orders,
  auditEvents,
}) => {
  const [activeTab, setActiveTab] = useState<'requests' | 'candidates' | 'orders' | 'timeline'>(
    'requests'
  )
  const [filterQuery, setFilterQuery] = useState('')

  return (
    <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-[#16181D] border border-neutral-200 dark:border-neutral-800 shadow-xs flex flex-col gap-5">
      {/* Tab Switcher & Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
          <button
            onClick={() => setActiveTab('requests')}
            className={`px-4 py-2 rounded-full text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'requests'
                ? 'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900 shadow-xs'
                : 'text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 bg-neutral-100 dark:bg-neutral-800'
            }`}
          >
            <FileText size={14} />
            <span>Requests ({requests.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('candidates')}
            className={`px-4 py-2 rounded-full text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'candidates'
                ? 'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900 shadow-xs'
                : 'text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 bg-neutral-100 dark:bg-neutral-800'
            }`}
          >
            <Scale size={14} />
            <span>Candidate Comparison ({candidates.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('orders')}
            className={`px-4 py-2 rounded-full text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'orders'
                ? 'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900 shadow-xs'
                : 'text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 bg-neutral-100 dark:bg-neutral-800'
            }`}
          >
            <ShoppingBag size={14} />
            <span>Orders ({orders.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-4 py-2 rounded-full text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'timeline'
                ? 'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900 shadow-xs'
                : 'text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 bg-neutral-100 dark:bg-neutral-800'
            }`}
          >
            <HistoryIcon size={14} />
            <span>Audit Timeline ({auditEvents.length})</span>
          </button>
        </div>

        {/* Search filter input */}
        <div className="relative min-w-[200px]">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400" />
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Filter records..."
            className="w-full text-xs rounded-full bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200 dark:border-neutral-700/80 pl-9 pr-3 py-2 outline-hidden text-neutral-900 dark:text-white"
          />
        </div>
      </div>

      {/* VIEW A: REQUESTS */}
      {activeTab === 'requests' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-800 text-neutral-400 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Original Prompt</th>
                <th className="py-2.5 px-3">Request ID</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Mandate Version</th>
                <th className="py-2.5 px-3">Created Date</th>
                <th className="py-2.5 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {requests
                .filter(
                  (r) =>
                    !filterQuery ||
                    r.prompt.toLowerCase().includes(filterQuery.toLowerCase()) ||
                    r.id.toLowerCase().includes(filterQuery.toLowerCase())
                )
                .map((req) => (
                  <tr key={req.id} className="hover:bg-neutral-50/50 dark:hover:bg-neutral-800/30">
                    <td className="py-3 px-3 font-bold text-neutral-900 dark:text-white max-w-xs truncate">
                      {req.prompt}
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-neutral-400">{req.id}</td>
                    <td className="py-3 px-3 text-neutral-600 dark:text-neutral-300">
                      {req.normalized_category || 'General'}
                    </td>
                    <td className="py-3 px-3 font-semibold">v{req.mandate_version}</td>
                    <td className="py-3 px-3 text-neutral-500">
                      {new Date(req.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Badge variant={req.status === 'completed' ? 'success' : 'info'}>
                        {req.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {/* VIEW B: CANDIDATE COMPARISON */}
      {activeTab === 'candidates' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-800 text-neutral-400 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Product Name</th>
                <th className="py-2.5 px-3">Retailer</th>
                <th className="py-2.5 px-3">Price</th>
                <th className="py-2.5 px-3">Stock</th>
                <th className="py-2.5 px-3">Guardrail Eligibility</th>
                <th className="py-2.5 px-3">Rejection / Match Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {candidates.flatMap((cand) =>
                cand.offers
                  .filter(
                    (off) =>
                      !filterQuery ||
                      cand.title.toLowerCase().includes(filterQuery.toLowerCase()) ||
                      off.domain.toLowerCase().includes(filterQuery.toLowerCase())
                  )
                  .map((off) => (
                    <tr
                      key={off.id}
                      className={`hover:bg-neutral-50/50 dark:hover:bg-neutral-800/30 ${
                        !off.is_eligible ? 'bg-rose-500/5' : ''
                      }`}
                    >
                      <td className="py-3 px-3 font-bold text-neutral-900 dark:text-white max-w-xs truncate">
                        {cand.title}
                      </td>
                      <td className="py-3 px-3 font-semibold text-neutral-800 dark:text-neutral-200">
                        {off.domain}
                      </td>
                      <td className="py-3 px-3 font-black text-sm">
                        ${off.price_amount} {off.currency}
                      </td>
                      <td className="py-3 px-3">
                        {off.availability === 'InStock' ? (
                          <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                            In Stock
                          </span>
                        ) : (
                          <span className="text-rose-500 font-medium">Out of Stock</span>
                        )}
                      </td>
                      <td className="py-3 px-3">
                        {off.is_eligible ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
                            Eligible
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/20">
                            Rejected
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-neutral-500 max-w-sm truncate">
                        {off.ineligibility_reason || cand.rank_reason}
                      </td>
                    </tr>
                  ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* VIEW C: ORDERS */}
      {activeTab === 'orders' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-800 text-neutral-400 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Order ID</th>
                <th className="py-2.5 px-3">Product Title</th>
                <th className="py-2.5 px-3">Captured Amount</th>
                <th className="py-2.5 px-3">PayPal Capture ID</th>
                <th className="py-2.5 px-3">Captured Date</th>
                <th className="py-2.5 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {orders
                .filter(
                  (o) =>
                    !filterQuery ||
                    o.id.toLowerCase().includes(filterQuery.toLowerCase()) ||
                    (o.product_title && o.product_title.toLowerCase().includes(filterQuery.toLowerCase()))
                )
                .map((o) => (
                  <tr key={o.id} className="hover:bg-neutral-50/50 dark:hover:bg-neutral-800/30">
                    <td className="py-3 px-3 font-mono text-[11px] font-semibold text-neutral-900 dark:text-white">
                      {o.id.slice(0, 13)}...
                    </td>
                    <td className="py-3 px-3 font-bold text-neutral-800 dark:text-neutral-200 max-w-xs truncate">
                      {o.product_title || 'Purchased Product'}
                    </td>
                    <td className="py-3 px-3 font-black text-sm text-neutral-900 dark:text-white">
                      ${o.amount} {o.currency}
                    </td>
                    <td className="py-3 px-3 font-mono text-emerald-600 dark:text-teal-400">
                      {o.paypal_capture_id || 'CAP-IN-FLIGHT'}
                    </td>
                    <td className="py-3 px-3 text-neutral-500">
                      {o.captured_at
                        ? new Date(o.captured_at).toLocaleString()
                        : new Date(o.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Badge variant={o.status === 'completed' ? 'success' : 'warning'}>
                        {o.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {/* VIEW D: AUDIT TIMELINE */}
      {activeTab === 'timeline' && (
        <div className="flex flex-col gap-3 py-2">
          {auditEvents
            .filter(
              (ev) =>
                !filterQuery ||
                ev.event_type.toLowerCase().includes(filterQuery.toLowerCase()) ||
                (ev.reason && ev.reason.toLowerCase().includes(filterQuery.toLowerCase()))
            )
            .map((ev) => (
              <div
                key={ev.id}
                className="p-4 rounded-2xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/80 dark:border-neutral-800 flex items-start gap-3.5 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-neutral-800 dark:text-neutral-200 shrink-0 font-bold text-xs mt-0.5">
                  <ShieldCheck size={16} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black uppercase tracking-wider text-neutral-900 dark:text-white">
                      {ev.event_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[11px] text-neutral-400">
                      {new Date(ev.created_at).toLocaleString()}
                    </span>
                  </div>
                  {ev.reason && (
                    <p className="text-xs text-neutral-600 dark:text-neutral-300 mt-1">
                      {ev.reason}
                    </p>
                  )}
                  {ev.details && (
                    <div className="mt-2 p-2.5 rounded-xl bg-white dark:bg-neutral-900 text-[11px] font-mono text-neutral-600 dark:text-neutral-400 border border-neutral-200/50 dark:border-neutral-800">
                      {JSON.stringify(ev.details)}
                    </div>
                  )}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}
