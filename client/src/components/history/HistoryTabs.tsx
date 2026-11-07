import React, { useState } from 'react'
import {
  Search,
  ShieldCheck,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Code2,
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
  const [activeTab, setActiveTab] = useState<'all' | 'requests' | 'candidates' | 'orders' | 'timeline'>('all')
  const [filterQuery, setFilterQuery] = useState('')
  const [dateFilter, setDateFilter] = useState<'all' | '7days' | '30days'>('all')
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null)

  const toggleExpand = (id: string) => {
    setExpandedRowId(expandedRowId === id ? null : id)
  }

  // Combined activity items for "All" tab
  const allItems = [
    ...requests.map((r) => ({
      kind: 'request' as const,
      id: r.id,
      title: r.prompt,
      category: r.normalized_category || 'General',
      timestamp: new Date(r.created_at).getTime(),
      dateStr: new Date(r.created_at).toLocaleString(),
      status: r.status,
      amount: null,
      details: r,
    })),
    ...orders.map((o) => ({
      kind: 'order' as const,
      id: o.id,
      title: o.product_title || `Order ${o.id.slice(0, 8)}`,
      category: o.retailer_domain || 'Retailer',
      timestamp: new Date(o.created_at).getTime(),
      dateStr: new Date(o.created_at).toLocaleString(),
      status: o.status,
      amount: `$${o.amount} ${o.currency}`,
      details: o,
    })),
    ...auditEvents.map((ev) => ({
      kind: 'timeline' as const,
      id: ev.id,
      title: ev.event_type.replace(/_/g, ' '),
      category: ev.reason || 'System Audit',
      timestamp: new Date(ev.created_at).getTime(),
      dateStr: new Date(ev.created_at).toLocaleString(),
      status: 'verified',
      amount: null,
      details: ev.details,
    })),
  ].sort((a, b) => b.timestamp - a.timestamp)

  const isWithinDate = (timestamp: number) => {
    if (dateFilter === 'all') return true
    const now = Date.now()
    const diffDays = (now - timestamp) / (1000 * 3600 * 24)
    if (dateFilter === '7days') return diffDays <= 7
    if (dateFilter === '30days') return diffDays <= 30
    return true
  }

  return (
    <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-4">
      {/* Tab Switcher & Search / Date Filter */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-3 border-b border-neutral-100 dark:border-neutral-800">
        {/* Compact Tab Buttons */}
        <div className="flex items-center gap-1 overflow-x-auto p-0.5 rounded-lg bg-neutral-100 dark:bg-neutral-800/80 text-xs font-medium">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1.5 rounded-md transition-colors cursor-pointer shrink-0 ${
              activeTab === 'all'
                ? 'bg-white dark:bg-[#17191C] text-neutral-900 dark:text-white shadow-xs font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
            }`}
          >
            All Activity ({allItems.length})
          </button>

          <button
            onClick={() => setActiveTab('requests')}
            className={`px-3 py-1.5 rounded-md transition-colors cursor-pointer shrink-0 ${
              activeTab === 'requests'
                ? 'bg-white dark:bg-[#17191C] text-neutral-900 dark:text-white shadow-xs font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
            }`}
          >
            Requests ({requests.length})
          </button>

          <button
            onClick={() => setActiveTab('candidates')}
            className={`px-3 py-1.5 rounded-md transition-colors cursor-pointer shrink-0 ${
              activeTab === 'candidates'
                ? 'bg-white dark:bg-[#17191C] text-neutral-900 dark:text-white shadow-xs font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
            }`}
          >
            Comparisons ({candidates.length})
          </button>

          <button
            onClick={() => setActiveTab('orders')}
            className={`px-3 py-1.5 rounded-md transition-colors cursor-pointer shrink-0 ${
              activeTab === 'orders'
                ? 'bg-white dark:bg-[#17191C] text-neutral-900 dark:text-white shadow-xs font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
            }`}
          >
            Orders ({orders.length})
          </button>

          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-3 py-1.5 rounded-md transition-colors cursor-pointer shrink-0 ${
              activeTab === 'timeline'
                ? 'bg-white dark:bg-[#17191C] text-neutral-900 dark:text-white shadow-xs font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
            }`}
          >
            Audit Timeline ({auditEvents.length})
          </button>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-2 self-start lg:self-auto">
          {/* Date Range Selector */}
          <select
            value={dateFilter}
            onChange={(e: any) => setDateFilter(e.target.value)}
            className="text-xs rounded-lg bg-neutral-50 dark:bg-[#141619] border border-neutral-200 dark:border-neutral-700/80 px-2.5 py-1.5 outline-hidden text-neutral-700 dark:text-neutral-300"
          >
            <option value="all">All Dates</option>
            <option value="7days">Last 7 Days</option>
            <option value="30days">Last 30 Days</option>
          </select>

          {/* Search Input */}
          <div className="relative w-48 sm:w-60">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-neutral-400" />
            <input
              type="text"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              placeholder="Search audit records..."
              className="w-full text-xs rounded-lg bg-neutral-50 dark:bg-[#141619] border border-neutral-200 dark:border-neutral-700/80 pl-8 pr-3 py-1.5 outline-hidden text-neutral-900 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* VIEW: ALL ACTIVITY (UNIFIED) */}
      {activeTab === 'all' && (
        <div className="flex flex-col divide-y divide-neutral-100 dark:divide-neutral-800">
          {allItems
            .filter(
              (item) =>
                isWithinDate(item.timestamp) &&
                (!filterQuery ||
                  item.title.toLowerCase().includes(filterQuery.toLowerCase()) ||
                  item.category.toLowerCase().includes(filterQuery.toLowerCase()) ||
                  item.id.toLowerCase().includes(filterQuery.toLowerCase()))
            )
            .map((item) => {
              const isExpanded = expandedRowId === item.id
              return (
                <div key={item.id} className="py-3 flex flex-col gap-2">
                  <div
                    onClick={() => toggleExpand(item.id)}
                    className="flex items-center justify-between gap-3 hover:bg-neutral-50/70 dark:hover:bg-neutral-800/40 p-2 rounded-lg cursor-pointer transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div
                        className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 text-xs font-semibold uppercase ${
                          item.kind === 'request'
                            ? 'bg-[#EEF0FD] text-[#434D91] dark:bg-[#202236] dark:text-[#AAB5F8]'
                            : item.kind === 'order'
                            ? 'bg-[#ECFADF] text-[#1D4A18] dark:bg-[#142617] dark:text-[#95EB68]'
                            : 'bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300'
                        }`}
                      >
                        {item.kind === 'request' ? 'R' : item.kind === 'order' ? 'O' : 'A'}
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-semibold text-neutral-900 dark:text-white truncate">
                          {item.title}
                        </div>
                        <div className="text-[11px] text-neutral-400 flex items-center gap-2 mt-0.5">
                          <span>{item.category}</span>
                          <span>•</span>
                          <span>{item.dateStr}</span>
                          <span className="font-mono text-[10px] hidden sm:inline">#{item.id.slice(0, 10)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5 shrink-0">
                      {item.amount && (
                        <span className="text-xs font-bold text-neutral-900 dark:text-white font-mono">
                          {item.amount}
                        </span>
                      )}
                      <Badge variant={item.status === 'completed' ? 'success' : 'neutral'} size="xs">
                        {item.status}
                      </Badge>
                      <button className="text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 p-1">
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                    </div>
                  </div>

                  {/* Expandable Technical Section */}
                  {isExpanded && (
                    <div className="p-3 mx-2 rounded-lg bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 text-[11px] font-mono text-neutral-600 dark:text-neutral-400 animate-in fade-in duration-150">
                      <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-neutral-200/60 dark:border-neutral-800">
                        <span className="font-sans font-semibold text-neutral-800 dark:text-neutral-200 flex items-center gap-1.5">
                          <Code2 size={13} /> Technical Verification & Payload
                        </span>
                        <span className="text-[10px] text-neutral-400">Record ID: {item.id}</span>
                      </div>
                      <pre className="overflow-x-auto whitespace-pre-wrap max-h-48 text-[10px]">
                        {JSON.stringify(item.details, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )
            })}
        </div>
      )}

      {/* VIEW: REQUESTS */}
      {activeTab === 'requests' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-neutral-200/80 dark:border-neutral-800 text-neutral-500 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Original Query</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Mandate Version</th>
                <th className="py-2.5 px-3">Date</th>
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
                  <tr key={req.id} className="hover:bg-neutral-50/60 dark:hover:bg-neutral-800/30">
                    <td className="py-3 px-3 font-semibold text-neutral-900 dark:text-white max-w-xs truncate">
                      {req.prompt}
                    </td>
                    <td className="py-3 px-3 text-neutral-600 dark:text-neutral-400">
                      {req.normalized_category || 'General'}
                    </td>
                    <td className="py-3 px-3 font-mono font-medium">v{req.mandate_version}</td>
                    <td className="py-3 px-3 text-neutral-400 text-[11px]">
                      {new Date(req.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Badge variant={req.status === 'completed' ? 'success' : 'info'} size="xs">
                        {req.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {/* VIEW: CANDIDATES */}
      {activeTab === 'candidates' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-neutral-200/80 dark:border-neutral-800 text-neutral-500 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Product Name</th>
                <th className="py-2.5 px-3">Retailer</th>
                <th className="py-2.5 px-3">Price</th>
                <th className="py-2.5 px-3">Stock</th>
                <th className="py-2.5 px-3">Policy Audit</th>
                <th className="py-2.5 px-3">Rationale</th>
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
                      className={`hover:bg-neutral-50/60 dark:hover:bg-neutral-800/30 ${
                        !off.is_eligible ? 'opacity-70 bg-rose-50/20 dark:bg-rose-950/10' : ''
                      }`}
                    >
                      <td className="py-3 px-3 font-semibold text-neutral-900 dark:text-white max-w-xs truncate">
                        {cand.title}
                      </td>
                      <td className="py-3 px-3 font-medium text-neutral-800 dark:text-neutral-200">
                        {off.domain}
                      </td>
                      <td className="py-3 px-3 font-bold text-neutral-900 dark:text-white font-mono">
                        ${off.price_amount}
                      </td>
                      <td className="py-3 px-3">
                        {off.availability === 'InStock' ? (
                          <span className="text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1">
                            <CheckCircle size={11} /> In Stock
                          </span>
                        ) : (
                          <span className="text-rose-500 font-medium">Out of Stock</span>
                        )}
                      </td>
                      <td className="py-3 px-3">
                        {off.is_eligible ? (
                          <Badge variant="success" size="xs" dot>
                            Eligible
                          </Badge>
                        ) : (
                          <Badge variant="danger" size="xs">
                            Rejected
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 px-3 text-neutral-500 max-w-xs truncate">
                        {off.ineligibility_reason || cand.rank_reason}
                      </td>
                    </tr>
                  ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* VIEW: ORDERS */}
      {activeTab === 'orders' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-neutral-200/80 dark:border-neutral-800 text-neutral-500 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Order ID</th>
                <th className="py-2.5 px-3">Product Title</th>
                <th className="py-2.5 px-3">Amount</th>
                <th className="py-2.5 px-3">PayPal Capture ID</th>
                <th className="py-2.5 px-3">Date</th>
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
                  <tr key={o.id} className="hover:bg-neutral-50/60 dark:hover:bg-neutral-800/30">
                    <td className="py-3 px-3 font-mono text-[11px] text-neutral-700 dark:text-neutral-300">
                      {o.id.slice(0, 14)}...
                    </td>
                    <td className="py-3 px-3 font-semibold text-neutral-900 dark:text-white max-w-xs truncate">
                      {o.product_title || 'Purchased Product'}
                    </td>
                    <td className="py-3 px-3 font-bold text-neutral-900 dark:text-white font-mono">
                      ${o.amount} {o.currency}
                    </td>
                    <td className="py-3 px-3 font-mono text-emerald-600 dark:text-emerald-400">
                      {o.paypal_capture_id || 'CAP-SIMULATED'}
                    </td>
                    <td className="py-3 px-3 text-neutral-400 text-[11px]">
                      {new Date(o.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Badge variant={o.status === 'completed' ? 'success' : 'warning'} size="xs" dot>
                        {o.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {/* VIEW: AUDIT TIMELINE */}
      {activeTab === 'timeline' && (
        <div className="flex flex-col gap-2.5 py-1">
          {auditEvents
            .filter(
              (ev) =>
                !filterQuery ||
                ev.event_type.toLowerCase().includes(filterQuery.toLowerCase()) ||
                (ev.reason && ev.reason.toLowerCase().includes(filterQuery.toLowerCase()))
            )
            .map((ev) => {
              const isExpanded = expandedRowId === ev.id
              return (
                <div
                  key={ev.id}
                  className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 flex flex-col gap-2 transition-colors"
                >
                  <div
                    onClick={() => toggleExpand(ev.id)}
                    className="flex items-start justify-between gap-3 cursor-pointer"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="w-6 h-6 rounded-md bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0">
                        <ShieldCheck size={14} />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-neutral-900 dark:text-white uppercase tracking-wider">
                          {ev.event_type.replace(/_/g, ' ')}
                        </div>
                        <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-0.5">
                          {ev.reason || 'Cryptographic audit assertion'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-neutral-400 shrink-0">
                      <span>{new Date(ev.created_at).toLocaleString()}</span>
                      <button className="text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 p-0.5">
                        {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                      </button>
                    </div>
                  </div>

                  {isExpanded && ev.details && (
                    <div className="mt-1 p-2.5 rounded-lg bg-white dark:bg-[#1C1F24] text-[11px] font-mono text-neutral-600 dark:text-neutral-400 border border-neutral-200/60 dark:border-neutral-800 overflow-x-auto">
                      <pre className="text-[10px]">{JSON.stringify(ev.details, null, 2)}</pre>
                    </div>
                  )}
                </div>
              )
            })}
        </div>
      )}
    </div>
  )
}
