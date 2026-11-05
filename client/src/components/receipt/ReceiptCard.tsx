import React from 'react'
import {
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  Receipt as ReceiptIcon,
  RotateCcw,
  Clock,
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
    <div className="rounded-[28px] p-6 md:p-8 bg-white dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800 shadow-[0_4px_24px_rgba(0,0,0,0.03)] flex flex-col gap-6">
      {/* Receipt Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-[#98EC6A] dark:bg-[#2CE5B5] flex items-center justify-center text-[#0A2610] dark:text-[#05261F] font-black shadow-xs">
            <CheckCircle2 size={24} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-black text-neutral-900 dark:text-white">
                Payment Captured Successfully
              </h3>
              {isRefunded ? (
                <Badge variant="warning">Refunded</Badge>
              ) : (
                <Badge variant="success">Completed</Badge>
              )}
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5 font-mono">
              Order #{order.id}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isRefundable && (
            <Button
              variant="outline"
              size="sm"
              icon={<RotateCcw size={14} />}
              onClick={() => onRequestRefund(order)}
            >
              Request Full Refund
            </Button>
          )}
        </div>
      </div>

      {/* Transaction Details Ledger */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="flex flex-col gap-4">
          <div className="p-4 rounded-2xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800 flex flex-col gap-3">
            <span className="text-[11px] font-bold uppercase tracking-wider text-neutral-400">
              Purchased Product
            </span>
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-neutral-700 dark:text-neutral-300 shrink-0">
                <ShoppingBag size={18} />
              </div>
              <div>
                <h4 className="text-sm font-bold text-neutral-900 dark:text-white leading-snug">
                  {order.product_title || 'Nordic Adjustable LED Desk Lamp with 3000K Warm Light'}
                </h4>
                <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                  Quantity: {order.quantity || 1} unit • Retailer: {order.retailer_domain || 'target.com'}
                </div>
              </div>
            </div>

            {order.retailer_buy_url && (
              <a
                href={order.retailer_buy_url}
                target="_blank"
                rel="noreferrer"
                className="mt-1 text-xs text-emerald-600 dark:text-teal-400 hover:underline flex items-center gap-1 font-semibold"
              >
                <span>Visit external retailer product page</span>
                <ExternalLink size={12} />
              </a>
            )}
          </div>

          {/* Fulfillment separation notice */}
          <div className="p-4 rounded-2xl bg-neutral-50/80 dark:bg-neutral-900/40 border border-neutral-200/60 dark:border-neutral-800 text-xs text-neutral-500 leading-relaxed">
            <strong className="text-neutral-700 dark:text-neutral-300">Hackathon Simulation:</strong>{' '}
            {order.fulfillment_note ||
              'Your payment has been captured in PayPal Sandbox. In a live production environment, Carti triggers autonomous merchant checkout or virtual card issuance.'}
          </div>
        </div>

        {/* Financial & PayPal Identifiers Ledger */}
        <div className="p-5 rounded-2xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800 flex flex-col justify-between gap-4">
          <div className="flex flex-col gap-3">
            <span className="text-[11px] font-bold uppercase tracking-wider text-neutral-400">
              PayPal Capture Receipt
            </span>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-neutral-200/60 dark:border-neutral-800">
                <span className="text-neutral-500">PayPal Order ID</span>
                <span className="font-mono font-semibold text-neutral-800 dark:text-neutral-200">
                  {order.paypal_order_id || 'PP-SANDBOX-ORDER'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-200/60 dark:border-neutral-800">
                <span className="text-neutral-500">PayPal Capture ID</span>
                <span className="font-mono font-bold text-emerald-600 dark:text-teal-400">
                  {order.paypal_capture_id || 'CAP-UNCONFIRMED'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-200/60 dark:border-neutral-800">
                <span className="text-neutral-500">Captured Timestamp</span>
                <span className="font-medium text-neutral-700 dark:text-neutral-300">
                  {order.captured_at ? new Date(order.captured_at).toLocaleString() : 'Just now'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-200/60 dark:border-neutral-800">
                <span className="text-neutral-500">Mandate Reservation</span>
                <span className="font-medium text-neutral-700 dark:text-neutral-300">
                  Converted to Captured Spend ($0.00 in-flight)
                </span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
            <span className="text-sm font-bold text-neutral-900 dark:text-white">
              Total Captured
            </span>
            <span className="text-2xl font-black text-neutral-900 dark:text-white">
              ${order.amount} {order.currency}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
