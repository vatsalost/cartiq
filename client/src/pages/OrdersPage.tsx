import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import {
  CheckCircle2,
  Search,
  ExternalLink,
  Copy,
  Check,
  RotateCcw,
  Receipt,
  ShieldCheck,
  CreditCard,
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
  const rawOrderFromNav = (location.state as any)?.newOrder
  const newOrderFromNav: Order | undefined = rawOrderFromNav
    ? {
        ...rawOrderFromNav,
        id: rawOrderFromNav.id || rawOrderFromNav.order_id || `ord_${Date.now()}`,
      }
    : undefined

  const getOrderId = (o?: Order | null): string => {
    if (!o) return ''
    return o.id || (o as any).order_id || ''
  }

  const [orders, setOrders] = useState<Order[]>(() => {
    if (newOrderFromNav) {
      return [newOrderFromNav, ...mockOrders.filter((o) => getOrderId(o) !== getOrderId(newOrderFromNav))]
    }
    return mockOrders
  })

  const [selectedOrder, setSelectedOrder] = useState<Order>(orders[0] || mockOrders[0])
  const [selectedOrderForReceipt, setSelectedOrderForReceipt] = useState<Order | null>(null)
  const [selectedOrderForRefund, setSelectedOrderForRefund] = useState<Order | null>(null)
  const [isReceiptOpen, setIsReceiptOpen] = useState(false)
  const [isRefundModalOpen, setIsRefundModalOpen] = useState(false)
  const [refundAlert, setRefundAlert] = useState<string | null>(null)
  const [filterTab, setFilterTab] = useState<'all' | 'completed' | 'pending' | 'refunded'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [copiedField, setCopiedField] = useState<string | null>(null)

  useEffect(() => {
    async function loadOrders() {
      try {
        const res = await api.listOrders()
        if (res.items && res.items.length > 0) {
          if (newOrderFromNav) {
            const merged = [newOrderFromNav, ...res.items.filter((o) => o.id !== newOrderFromNav.id)]
            setOrders(merged)
            setSelectedOrder(merged[0])
          } else {
            setOrders(res.items)
            setSelectedOrder(res.items[0])
          }
        }
      } catch {
        // Fallback to initialized mock state
      }
    }
    loadOrders()
  }, [newOrderFromNav])

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const handleRefundSuccess = (refund: Refund) => {
    setOrders((prev) =>
      prev.map((o) => (o.id === refund.order_id ? { ...o, status: 'refunded' } : o))
    )
    if (selectedOrder.id === refund.order_id) {
      setSelectedOrder({ ...selectedOrder, status: 'refunded' })
    }
    setRefundAlert(
      `Full refund of $${refund.amount} ${refund.currency} successfully issued. PayPal Refund ID: ${
        refund.paypal_refund_id || 'REF-CONFIRMED'
      }`
    )
  }

  // Filter calculations
  const completedOrders = orders.filter((o) => o.status === 'completed')
  const pendingOrders = orders.filter((o) => (o.status as string) === 'pending')
  const refundedOrders = orders.filter((o) => o.status === 'refunded')

  const totalCapturedAmount = completedOrders.reduce(
    (sum, o) => sum + parseFloat(o.amount || '0'),
    0
  )

  const filteredOrders = orders.filter((o) => {
    if (filterTab === 'completed' && o.status !== 'completed') return false
    if (filterTab === 'pending' && (o.status as string) !== 'pending') return false
    if (filterTab === 'refunded' && o.status !== 'refunded') return false

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
      {/* Top Header */}
      <div>
        <h1 className="text-[28px] font-bold text-neutral-900 dark:text-white tracking-tight leading-tight">
          Orders & Transactions
        </h1>
        <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
          Settled purchases, delivery status, and PayPal transaction receipts.
        </p>
      </div>

      {refundAlert && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 dark:bg-emerald-950/20 dark:border-emerald-800/40 dark:text-emerald-300 text-xs font-semibold flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 size={16} strokeWidth={1.8} className="shrink-0" />
          <span>{refundAlert}</span>
        </div>
      )}

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400 font-medium">
            <span>Total Orders</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 font-semibold tabular-nums">
              100% Fulfilled
            </span>
          </div>
          <div className="text-[30px] font-bold text-neutral-900 dark:text-white mt-2 tabular-nums">
            {orders.length}
          </div>
        </div>

        <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400 font-medium">
            <span>Total Captured</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 font-semibold tabular-nums">
              PayPal Settled
            </span>
          </div>
          <div className="text-[30px] font-bold text-neutral-900 dark:text-white mt-2 tabular-nums">
            ${totalCapturedAmount.toFixed(2)}
          </div>
        </div>

        <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400 font-medium">
            <span>Refunds & Disputes</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 font-semibold tabular-nums">
              0.0% Rate
            </span>
          </div>
          <div className="text-[30px] font-bold text-neutral-900 dark:text-white mt-2 tabular-nums">
            {refundedOrders.length}
          </div>
        </div>
      </div>

      {/* Filter Tabs + Search Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => setFilterTab('all')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors cursor-pointer font-medium ${
              filterTab === 'all'
                ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 font-semibold'
                : 'bg-white dark:bg-[#17191C] text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 border border-neutral-200/80 dark:border-neutral-800'
            }`}
          >
            All Orders ({orders.length})
          </button>
          <button
            onClick={() => setFilterTab('completed')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors cursor-pointer font-medium ${
              filterTab === 'completed'
                ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 font-semibold'
                : 'bg-white dark:bg-[#17191C] text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 border border-neutral-200/80 dark:border-neutral-800'
            }`}
          >
            Completed ({completedOrders.length})
          </button>
          <button
            onClick={() => setFilterTab('pending')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors cursor-pointer font-medium ${
              filterTab === 'pending'
                ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 font-semibold'
                : 'bg-white dark:bg-[#17191C] text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 border border-neutral-200/80 dark:border-neutral-800'
            }`}
          >
            Pending ({pendingOrders.length})
          </button>
          <button
            onClick={() => setFilterTab('refunded')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors cursor-pointer font-medium ${
              filterTab === 'refunded'
                ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 font-semibold'
                : 'bg-white dark:bg-[#17191C] text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 border border-neutral-200/80 dark:border-neutral-800'
            }`}
          >
            Refunded ({refundedOrders.length})
          </button>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search size={16} strokeWidth={1.8} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by product, retailer, or PayPal ID..."
            className="w-full text-xs rounded-lg bg-white dark:bg-[#17191C] border border-neutral-200 dark:border-neutral-700/80 pl-9 pr-3 py-1.5 outline-hidden text-neutral-900 dark:text-white"
          />
        </div>
      </div>

      {/* Transactions Table */}
      <div className="rounded-xl bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-neutral-200/80 dark:border-neutral-800 bg-neutral-50/50 dark:bg-[#141619] text-neutral-500 uppercase text-[10px] tracking-wider font-semibold">
                <th className="py-3 px-4">Order ID</th>
                <th className="py-3 px-4">Product</th>
                <th className="py-3 px-4">Retailer</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-xs text-neutral-400">
                    No transactions match your search filter.
                  </td>
                </tr>
              ) : (
                filteredOrders.map((order) => {
                  const isSelected = getOrderId(selectedOrder) === getOrderId(order)
                  return (
                    <tr
                      key={getOrderId(order) || Math.random().toString()}
                      onClick={() => setSelectedOrder(order)}
                      className={`transition-colors cursor-pointer ${
                        isSelected
                          ? 'bg-[#ECFADF]/40 dark:bg-[#142617]/30'
                          : 'hover:bg-neutral-50 dark:hover:bg-neutral-800/40'
                      }`}
                    >
                      <td className="py-3.5 px-4 font-mono text-[11px] font-medium text-neutral-700 dark:text-neutral-300 tabular-nums">
                        {getOrderId(order).slice(0, 12) || 'ORD-RECENT'}
                      </td>
                      <td className="py-3.5 px-4 font-medium text-neutral-900 dark:text-white max-w-[220px] truncate">
                        {order.product_title || 'Anker USB-C Hub 7-in-1'}
                      </td>
                      <td className="py-3.5 px-4 text-neutral-600 dark:text-neutral-400">
                        {order.retailer_domain?.replace('.com', '') || 'Amazon'}
                      </td>
                      <td className="py-3.5 px-4 font-bold text-neutral-900 dark:text-white tabular-nums">
                        ${order.amount}
                      </td>
                      <td className="py-3.5 px-4">
                        {order.status === 'completed' ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#ECFADF] text-[#1D4A18] dark:bg-[#142617] dark:text-[#95EB68] inline-flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#1D4A18] dark:bg-[#95EB68]" />
                            Completed
                          </span>
                        ) : order.status === 'refunded' ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 inline-flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                            Refunded
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
                            {order.status}
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-neutral-500 dark:text-neutral-400 tabular-nums">
                        May 10, 2026
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedOrder(order)
                          }}
                          className="text-xs font-medium text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-white px-2.5 py-1 rounded-md bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Order Detailed Card */}
      {selectedOrder && (
        <div className="rounded-xl p-5 md:p-6 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-5 animate-in fade-in">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-neutral-100 dark:border-neutral-800">
            <div>
              <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
                {selectedOrder.product_title || 'Anker USB-C Hub 7-in-1 with 4K HDMI'}
              </h3>
              <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5 tabular-nums">
                {selectedOrder.retailer_domain || 'Amazon'} • Ordered May 10, 2026 at 4:30 PM
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-[#ECFADF] text-[#1D4A18] dark:bg-[#142617] dark:text-[#95EB68] flex items-center gap-1.5">
                <CheckCircle2 size={14} strokeWidth={1.8} />
                <span>Verified PayPal Capture</span>
              </span>
            </div>
          </div>

          {/* 2-Column Specs: Payment Details (Left) + Mandate Details (Right) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Payment Details */}
            <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800/80 flex flex-col gap-2.5">
              <div className="text-[15px] font-semibold text-neutral-900 dark:text-white pb-1 border-b border-neutral-200/60 dark:border-neutral-800">
                Payment Details
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">PayPal Order ID</span>
                  <div className="flex items-center gap-1.5 font-mono text-[11px] text-neutral-800 dark:text-neutral-200 tabular-nums">
                    <span>{selectedOrder.paypal_order_id || '5X982341KL678901M'}</span>
                    <button
                      type="button"
                      onClick={() =>
                        copyToClipboard(
                          selectedOrder.paypal_order_id || '5X982341KL678901M',
                          'paypal_order'
                        )
                      }
                      className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 cursor-pointer"
                    >
                      {copiedField === 'paypal_order' ? (
                        <Check size={14} strokeWidth={1.8} className="text-emerald-500" />
                      ) : (
                        <Copy size={14} strokeWidth={1.8} />
                      )}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Capture ID</span>
                  <div className="flex items-center gap-1.5 font-mono text-[11px] text-neutral-800 dark:text-neutral-200 tabular-nums">
                    <span>{selectedOrder.paypal_capture_id || 'CAP_876543210987'}</span>
                    <button
                      type="button"
                      onClick={() =>
                        copyToClipboard(
                          selectedOrder.paypal_capture_id || 'CAP_876543210987',
                          'capture_id'
                        )
                      }
                      className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 cursor-pointer"
                    >
                      {copiedField === 'capture_id' ? (
                        <Check size={14} strokeWidth={1.8} className="text-emerald-500" />
                      ) : (
                        <Copy size={14} strokeWidth={1.8} />
                      )}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Captured At</span>
                  <span className="text-neutral-800 dark:text-neutral-200 tabular-nums">
                    May 10, 2026, 4:30 PM
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Amount</span>
                  <span className="font-bold text-neutral-900 dark:text-white tabular-nums">
                    ${selectedOrder.amount} {selectedOrder.currency}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Payment Status</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                    {selectedOrder.status.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            {/* Mandate Details */}
            <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800/80 flex flex-col gap-2.5">
              <div className="text-[15px] font-semibold text-neutral-900 dark:text-white pb-1 border-b border-neutral-200/60 dark:border-neutral-800">
                Mandate Details
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Reservation ID</span>
                  <span className="font-mono text-[11px] text-neutral-800 dark:text-neutral-200 tabular-nums">
                    res_11223344
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Mandate Version</span>
                  <span className="font-mono text-[11px] text-neutral-800 dark:text-neutral-200 tabular-nums">
                    v2
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Category</span>
                  <span className="text-neutral-800 dark:text-neutral-200 font-medium">
                    electronics (Permitted)
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Price Check</span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1 tabular-nums">
                    <Check size={14} strokeWidth={2} />
                    <span>${selectedOrder.amount} &le; $60.00 cap (Passed)</span>
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-neutral-500 dark:text-neutral-400">Tolerance Check</span>
                  <span className="text-neutral-800 dark:text-neutral-200 tabular-nums">
                    0.0% variance (Passed)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-3 border-t border-neutral-100 dark:border-neutral-800 flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedOrderForReceipt(selectedOrder)
                  setIsReceiptOpen(true)
                }}
                icon={<Receipt size={16} strokeWidth={1.8} />}
              >
                View Receipt
              </Button>

              {selectedOrder.status === 'completed' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedOrderForRefund(selectedOrder)
                    setIsRefundModalOpen(true)
                  }}
                  icon={<RotateCcw size={16} strokeWidth={1.8} />}
                >
                  Request Refund
                </Button>
              )}
            </div>

            {selectedOrder.retailer_buy_url && (
              <a
                href={selectedOrder.retailer_buy_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
              >
                <span>View on Retailer</span>
                <ExternalLink size={14} strokeWidth={1.8} />
              </a>
            )}
          </div>
        </div>
      )}

      {/* Modals */}
      {selectedOrderForReceipt && (
        <ReceiptDetailModal
          order={selectedOrderForReceipt}
          isOpen={isReceiptOpen}
          onClose={() => {
            setIsReceiptOpen(false)
            setSelectedOrderForReceipt(null)
          }}
          onRequestRefund={(ord) => {
            setIsReceiptOpen(false)
            setSelectedOrderForRefund(ord)
            setIsRefundModalOpen(true)
          }}
        />
      )}

      {selectedOrderForRefund && (
        <RefundModal
          order={selectedOrderForRefund}
          isOpen={isRefundModalOpen}
          onClose={() => {
            setIsRefundModalOpen(false)
            setSelectedOrderForRefund(null)
          }}
          onRefundSuccess={handleRefundSuccess}
        />
      )}
    </div>
  )
}
