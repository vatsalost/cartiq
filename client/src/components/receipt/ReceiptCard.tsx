import React from 'react'
import {
  CheckCircle2,
  ExternalLink,
  RotateCcw,
  ShoppingBag,
} from 'lucide-react'
import { Order } from '../../api/types'
import { Button } from '../common/Button'
import { Badge } from '../common/Badge'

interface ReceiptCardProps {
  order: Order
  onRequestRefund: (order: Order) => void
}

export const ReceiptCard: React.FC<ReceiptCardProps> = ({ order, onRequestRefund }) => {
  const isRefundable = order.status === 'completed' && Boolean(order.paypal_capture_id)
  const isRefunded = order.status === 'refunded'

  return (
    <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-[#16181D] border border-neutral-200 dark:border-neutral-800 shadow-xs flex flex-col gap-5">
      {/* Receipt Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#98EC6A] dark:bg-[#2CE5B5] flex items-center justify-center text-[#0A2610] dark:text-[#05261F] font-bold">
            <CheckCircle2 size={20} strokeWidth={1.8} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
                {isRefunded ? 'Order Refunded' : 'Payment Confirmed'}
              </h3>
              {isRefunded ? (
                <Badge variant="warning" size="sm">Refunded</Badge>
              ) : (
                <Badge variant="success" size="sm">Captured</Badge>
              )}
            </div>
            <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5 tabular-nums">
              Order #{order.id.slice(0, 16)}
            </p>
          </div>
        </div>

        {isRefundable && (
          <Button
            variant="outline"
            size="sm"
            icon={<RotateCcw size={16} strokeWidth={1.8} />}
            onClick={() => onRequestRefund(order)}
          >
            Refund Order
          </Button>
        )}
      </div>

      {/* Transaction Details Ledger */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Product Information */}
        <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800 flex flex-col justify-between gap-3">
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400">
              Product Details
            </span>
            <div className="flex items-start gap-3 mt-2">
              <div className="w-9 h-9 rounded-lg bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-neutral-600 dark:text-neutral-300 shrink-0">
                <ShoppingBag size={16} strokeWidth={1.8} />
              </div>
              <div>
                <h4 className="text-[14px] font-semibold text-neutral-900 dark:text-white leading-snug">
                  {order.product_title || 'Purchased Item'}
                </h4>
                <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                  Retailer: <strong className="text-neutral-700 dark:text-neutral-300">{order.retailer_domain || 'Retailer'}</strong> • Quantity: <span className="tabular-nums">{order.quantity || 1}</span>
                </div>
              </div>
            </div>
          </div>

          {order.retailer_buy_url && (
            <a
              href={order.retailer_buy_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-neutral-600 dark:text-neutral-300 hover:underline flex items-center gap-1 font-medium pt-2 border-t border-neutral-200/50 dark:border-neutral-800"
            >
              <span>View Product on {order.retailer_domain || 'Merchant'}</span>
              <ExternalLink size={12} strokeWidth={1.8} />
            </a>
          )}
        </div>

        {/* Payment & Capture Details */}
        <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800 flex flex-col justify-between gap-3">
          <div className="space-y-2 text-xs">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400 block mb-1">
              Payment Summary
            </span>

            <div className="flex justify-between py-1 border-b border-neutral-200/50 dark:border-neutral-800">
              <span className="text-neutral-500">PayPal Order ID</span>
              <span className="font-mono text-[11px] text-neutral-800 dark:text-neutral-200 tabular-nums">
                {order.paypal_order_id || 'PP-SANDBOX'}
              </span>
            </div>

            <div className="flex justify-between py-1 border-b border-neutral-200/50 dark:border-neutral-800">
              <span className="text-neutral-500">Capture ID</span>
              <span className="font-mono text-[11px] text-neutral-800 dark:text-neutral-200 tabular-nums">
                {order.paypal_capture_id || 'CAP-PENDING'}
              </span>
            </div>

            <div className="flex justify-between py-1 border-b border-neutral-200/50 dark:border-neutral-800">
              <span className="text-neutral-500">Date</span>
              <span className="text-neutral-700 dark:text-neutral-300 tabular-nums">
                {order.captured_at ? new Date(order.captured_at).toLocaleDateString() : 'Recent'}
              </span>
            </div>
          </div>

          <div className="pt-2 border-t border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
            <span className="text-xs font-semibold text-neutral-600 dark:text-neutral-400">
              Total Captured
            </span>
            <span className="text-xl font-bold text-neutral-900 dark:text-white tabular-nums">
              ${order.amount} {order.currency}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
