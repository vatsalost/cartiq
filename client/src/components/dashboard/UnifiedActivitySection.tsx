import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Sparkles, Receipt, ArrowUpRight, CheckCircle, Clock } from 'lucide-react'
import { ShoppingRequest, Order } from '../../api/types'
import { Badge } from '../common/Badge'

interface UnifiedActivitySectionProps {
  requests: ShoppingRequest[]
  orders: Order[]
}

export const UnifiedActivitySection: React.FC<UnifiedActivitySectionProps> = ({
  requests,
  orders,
}) => {
  const [activeTab, setActiveTab] = useState<'all' | 'requests' | 'orders'>('all')

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success" size="xs" dot>Completed</Badge>
      case 'proposal_ready':
        return <Badge variant="lime" size="xs" dot>Proposal Ready</Badge>
      case 'running':
      case 'searching':
      case 'planning':
      case 'evaluating_mandate':
        return <Badge variant="info" size="xs" dot>Processing</Badge>
      case 'refunded':
        return <Badge variant="warning" size="xs" dot>Refunded</Badge>
      case 'cancelled':
        return <Badge variant="neutral" size="xs">Cancelled</Badge>
      default:
        return <Badge variant="neutral" size="xs">{status}</Badge>
    }
  }

  // Combined timeline items
  const combinedItems = [
    ...requests.map((r) => ({
      type: 'request' as const,
      id: r.id,
      title: r.prompt,
      subtitle: `${r.normalized_category || 'General'} • Request ${r.id.slice(0, 8)}`,
      time: new Date(r.created_at).toLocaleDateString(),
      status: r.status,
      amount: null,
      link: r.active_proposal_id ? '/proposals' : '/shopping',
      actionLabel: r.active_proposal_id ? 'View Proposal' : 'Track',
    })),
    ...orders.map((o) => ({
      type: 'order' as const,
      id: o.id,
      title: o.product_title || `Order ${o.id.slice(0, 8)}`,
      subtitle: `${o.retailer_domain || 'Retailer'} • PayPal ${o.paypal_capture_id || o.id.slice(0, 8)}`,
      time: new Date(o.created_at).toLocaleDateString(),
      status: o.status,
      amount: `$${o.amount}`,
      link: '/orders',
      actionLabel: 'Receipt',
    })),
  ].sort((a, b) => (a.id < b.id ? 1 : -1))

  const filteredItems = combinedItems.filter((item) => {
    if (activeTab === 'requests') return item.type === 'request'
    if (activeTab === 'orders') return item.type === 'order'
    return true
  })

  return (
    <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-4">
      {/* Header & Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-neutral-100 dark:border-neutral-800">
        <div>
          <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
            Recent Activity
          </h3>
          <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
            Real-time feed of shopping queries, proposals and settled captures
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-1 p-0.5 rounded-lg bg-neutral-100 dark:bg-neutral-800/80 self-start sm:self-auto text-xs font-medium">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1 rounded-md transition-colors cursor-pointer ${
              activeTab === 'all'
                ? 'bg-white dark:bg-[#17191C] text-neutral-900 dark:text-white shadow-xs font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
            }`}
          >
            All (<span className="tabular-nums">{combinedItems.length}</span>)
          </button>
          <button
            onClick={() => setActiveTab('requests')}
            className={`px-3 py-1 rounded-md transition-colors cursor-pointer ${
              activeTab === 'requests'
                ? 'bg-white dark:bg-[#17191C] text-neutral-900 dark:text-white shadow-xs font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
            }`}
          >
            Requests (<span className="tabular-nums">{requests.length}</span>)
          </button>
          <button
            onClick={() => setActiveTab('orders')}
            className={`px-3 py-1 rounded-md transition-colors cursor-pointer ${
              activeTab === 'orders'
                ? 'bg-white dark:bg-[#17191C] text-neutral-900 dark:text-white shadow-xs font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
            }`}
          >
            Orders (<span className="tabular-nums">{orders.length}</span>)
          </button>
        </div>
      </div>

      {/* Items List */}
      <div className="flex flex-col divide-y divide-neutral-100 dark:divide-neutral-800/60">
        {filteredItems.length === 0 ? (
          <div className="py-8 text-center text-xs text-neutral-400">
            No activity found for this filter.
          </div>
        ) : (
          filteredItems.slice(0, 6).map((item) => (
            <div
              key={item.id}
              className="py-3 flex items-center justify-between gap-3 hover:bg-neutral-50/60 dark:hover:bg-neutral-800/40 px-2 rounded-lg transition-colors group"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-xs ${
                    item.type === 'request'
                      ? 'bg-[#EEF0FD] text-[#434D91] dark:bg-[#202236] dark:text-[#AAB5F8]'
                      : 'bg-[#ECFADF] text-[#1D4A18] dark:bg-[#142617] dark:text-[#95EB68]'
                  }`}
                >
                  {item.type === 'request' ? (
                    <Sparkles size={16} strokeWidth={1.8} />
                  ) : (
                    <Receipt size={16} strokeWidth={1.8} />
                  )}
                </div>

                <div className="min-w-0">
                  <div className="text-xs font-semibold text-neutral-900 dark:text-white truncate">
                    {item.title}
                  </div>
                  <div className="text-[11px] text-neutral-500 dark:text-neutral-400 flex items-center gap-1.5 mt-0.5">
                    <span>{item.subtitle}</span>
                    <span>•</span>
                    <span className="tabular-nums">{item.time}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                {item.amount && (
                  <div className="text-xs font-bold text-neutral-900 dark:text-white tabular-nums">
                    {item.amount}
                  </div>
                )}
                {getStatusBadge(item.status)}
                <Link
                  to={item.link}
                  className="hidden sm:flex items-center gap-1 text-[11px] font-medium text-neutral-500 hover:text-neutral-900 dark:hover:text-white group-hover:underline transition-colors"
                >
                  <span>{item.actionLabel}</span>
                  <ArrowRight size={14} strokeWidth={1.8} />
                </Link>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
