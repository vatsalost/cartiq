import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import {
  ShoppingBag,
  RotateCcw,
  CheckCircle2,
  Search,
  ExternalLink,
  CreditCard,
  ArrowUpRight,
} from 'lucide-react'
import { ReceiptDetailModal } from '../components/receipt/ReceiptDetailModal'
import { RefundModal } from '../components/receipt/RefundModal'
import { api } from '../api/client'
import { Order, Refund } from '../api/types'
import { mockOrders } from '../api/mockData'
import { Badge } from '../components/common/Badge'
import { Button } from '../components/common/Button'

export const OrdersPage: React.FC = () => {
  const location = useLocation()
  const newOrderFromNav = (location.state as any)?.newOrder as Order | undefined

  const [orders, setOrders] = useState<Order[]>(() => {
    if (newOrderFromNav) {
      return [newOrderFromNav, ...mockOrders.filter((o) => o.id !== newOrderFromNav.id)]
    }
    return mockOrders
  })
  const [selectedOrderForReceipt, setSelectedOrderForReceipt] = useState<Order | null>(null)
  const [selectedOrderForRefund, setSelectedOrderForRefund] = useState<Order | null>(null)
  const [isReceiptOpen, setIsReceiptOpen] = useState(false)
  const [isRefundModalOpen, setIsRefundModalOpen] = useState(false)
  const [refundAlert, setRefundAlert] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    async function loadOrders() {
      try {
        const res = await api.listOrders()
        if (res.items && res.items.length > 0) {
          if (newOrderFromNav) {
            setOrders([newOrderFromNav, ...res.items.filter((o) => o.id !== newOrderFromNav.id)])
          } else {
            setOrders(res.items)
          }
        }
      } catch {
        // Fallback to state initialized with mock
      }
    }
    loadOrders()
  }, [newOrderFromNav])

  const handleRefundSuccess = (refund: Refund) => {
    setOrders((prev) =>
      prev.map((o) => (o.id === refund.order_id ? { ...o, status: 'refunded' } : o))
    )
    setRefundAlert(
      `Full refund of $${refund.amount} ${refund.currency} successfully issued. PayPal Refund ID: ${refund.paypal_refund_id || 'REF-CONFIRMED'}`
    )
  }

  // Calculate metrics
  const totalOrdersCount = orders.length
  const totalCapturedAmount = orders
    .filter((o) => o.status === 'completed')
    .reduce((sum, o) => sum + parseFloat(o.amount || '0'), 0)
  const totalRefundedAmount = orders
    .filter((o) => o.status === 'refunded')
    .reduce((sum, o) => sum + parseFloat(o.amount || '0'), 0)

  const filteredOrders = orders.filter((o) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      o.id.toLowerCase().includes(q) ||
      (o.product_title && o.product_title.toLowerCase().includes(q)) ||
      (o.retailer_domain && o.retailer_domain.toLowerCase().includes(q)) ||
      (o.paypal_capture_id && o.paypal_capture_id.toLowerCase().includes(q))
    )
  })

  return (
    <div className="flex flex-col gap-6">
      {/* Top Heading */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-neutral-900 dark:text-white tracking-tight">
            Orders & Transactions
          </h2>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
            Confirmed PayPal captures, receipts, and non-reversible refunds
          </p>
        </div>
      </div>

      {refundAlert && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 dark:bg-emerald-950/20 dark:border-emerald-800/40 dark:text-emerald-300 text-xs font-semibold flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 size={16} className="shrink-0" />
          <span>{refundAlert}</span>
        </div>
      )}

      {/* 3 Metric Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl p-4 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
            Total Orders
          </span>
          <div className="text-2xl font-bold text-neutral-900 dark:text-white mt-1">
            {totalOrdersCount}
          </div>
          <div className="text-[11px] text-neutral-400 mt-0.5">
            All captured transactions
          </div>
        </div>

        <div className="rounded-xl p-4 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
            Captured Spending
          </span>
          <div className="text-2xl font-bold text-neutral-900 dark:text-white mt-1">
            ${totalCapturedAmount.toFixed(2)}
          </div>
          <div className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-0.5 font-medium">
            Active settled capital
          </div>
        </div>

        <div className="rounded-xl p-4 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
            Total Refunds
          </span>
          <div className="text-2xl font-bold text-neutral-900 dark:text-white mt-1">
            ${totalRefundedAmount.toFixed(2)}
          </div>
          <div className="text-[11px] text-neutral-400 mt-0.5">
            Restored to budget balance
          </div>
        </div>
      </div>

      {/* Clean Transactions Table */}
      <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-neutral-100 dark:border-neutral-800">
          <div>
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-white">
              Transactions History
            </h3>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
              Click any order row to inspect full receipt and refund actions
            </p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search orders, retailers..."
              className="w-full text-xs rounded-lg bg-neutral-50 dark:bg-[#141619] border border-neutral-200 dark:border-neutral-700/80 pl-8.5 pr-3 py-1.5 outline-hidden text-neutral-900 dark:text-white"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-neutral-200/80 dark:border-neutral-800 text-neutral-500 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Order ID</th>
                <th className="py-2.5 px-3">Product & Retailer</th>
                <th className="py-2.5 px-3">Date</th>
                <th className="py-2.5 px-3">Amount</th>
                <th className="py-2.5 px-3">PayPal Capture ID</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-xs text-neutral-400">
                    No matching transactions found.
                  </td>
                </tr>
              ) : (
                filteredOrders.map((order) => (
                  <tr
                    key={order.id}
                    onClick={() => {
                      setSelectedOrderForReceipt(order)
                      setIsReceiptOpen(true)
                    }}
                    className="hover:bg-neutral-50/80 dark:hover:bg-neutral-800/40 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-3 font-mono text-[11px] text-neutral-700 dark:text-neutral-300">
                      {order.id.slice(0, 12)}...
                    </td>

                    <td className="py-3 px-3">
                      <div className="font-semibold text-neutral-900 dark:text-white max-w-[220px] truncate">
                        {order.product_title || 'Purchased Item'}
                      </div>
                      <div className="text-[11px] text-neutral-400 mt-0.5">
                        {order.retailer_domain || 'Retailer'}
                      </div>
                    </td>

                    <td className="py-3 px-3 text-neutral-500 dark:text-neutral-400 text-[11px]">
                      {new Date(order.created_at).toLocaleDateString()}
                    </td>

                    <td className="py-3 px-3 font-bold text-neutral-900 dark:text-white font-mono">
                      ${order.amount} <span className="text-[10px] font-normal text-neutral-400">{order.currency}</span>
                    </td>

                    <td className="py-3 px-3 font-mono text-[11px] text-neutral-500 dark:text-neutral-400">
                      {order.paypal_capture_id || 'CAP-SIMULATED'}
                    </td>

                    <td className="py-3 px-3">
                      {order.status === 'completed' ? (
                        <Badge variant="success" size="xs" dot>
                          Captured
                        </Badge>
                      ) : order.status === 'refunded' ? (
                        <Badge variant="warning" size="xs" dot>
                          Refunded
                        </Badge>
                      ) : (
                        <Badge variant="neutral" size="xs">
                          {order.status}
                        </Badge>
                      )}
                    </td>

                    <td className="py-3 px-3 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="outline"
                          size="xs"
                          onClick={() => {
                            setSelectedOrderForReceipt(order)
                            setIsReceiptOpen(true)
                          }}
                        >
                          Receipt
                        </Button>

                        {order.status === 'completed' && order.paypal_capture_id && (
                          <Button
                            variant="ghost"
                            size="xs"
                            className="text-neutral-400 hover:text-rose-600 dark:hover:text-rose-400"
                            onClick={() => {
                              setSelectedOrderForRefund(order)
                              setIsRefundModalOpen(true)
                            }}
                          >
                            Refund
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Official Receipt Modal */}
      <ReceiptDetailModal
        order={selectedOrderForReceipt}
        isOpen={isReceiptOpen}
        onClose={() => setIsReceiptOpen(false)}
        onRequestRefund={(ord) => {
          setSelectedOrderForRefund(ord)
          setIsRefundModalOpen(true)
        }}
      />

      {/* Full Refund Modal */}
      <RefundModal
        order={selectedOrderForRefund}
        isOpen={isRefundModalOpen}
        onClose={() => setIsRefundModalOpen(false)}
        onRefundSuccess={handleRefundSuccess}
      />
    </div>
  )
}
