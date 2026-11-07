import React from 'react'
import {
  CheckCircle2,
  ExternalLink,
  RotateCcw,
  ShoppingBag,
  ShieldCheck,
} from 'lucide-react'
import { Order } from '../../api/types'
import { Modal } from '../common/Modal'
import { Button } from '../common/Button'
import { Badge } from '../common/Badge'

interface ReceiptDetailModalProps {
  order: Order | null
  isOpen: boolean
  onClose: () => void
  onRequestRefund: (order: Order) => void
}

export const ReceiptDetailModal: React.FC<ReceiptDetailModalProps> = ({
  order,
  isOpen,
  onClose,
  onRequestRefund,
}) => {
  if (!order) return null

  const isRefundable = order.status === 'completed' && Boolean(order.paypal_capture_id)
  const isRefunded = order.status === 'refunded'

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Official Transaction Receipt"
      description={`Authoritative PayPal capture record for Order #${order.id.slice(0, 16)}`}
      maxWidth="md"
    >
      <div className="flex flex-col gap-4">
        {/* Status Banner */}
        <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold ${
                isRefunded
                  ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/30 dark:text-amber-400'
                  : 'bg-[#ECFADF] text-[#1D4A18] dark:bg-[#142617] dark:text-[#95EB68]'
              }`}
            >
              <CheckCircle2 size={16} strokeWidth={1.8} />
            </div>
            <div>
              <div className="text-xs font-semibold text-neutral-900 dark:text-white flex items-center gap-1.5">
                <span>{isRefunded ? 'Payment Refunded' : 'Payment Settled & Captured'}</span>
                <Badge variant={isRefunded ? 'warning' : 'success'} size="xs" dot>
                  {isRefunded ? 'Refunded' : 'Completed'}
                </Badge>
              </div>
              <div className="text-[11px] text-neutral-400 font-mono mt-0.5 tabular-nums">
                {new Date(order.created_at).toLocaleString()}
              </div>
            </div>
          </div>

          <div className="text-right font-mono">
            <div className="text-[26px] font-bold text-neutral-900 dark:text-white tabular-nums">
              ${order.amount}
            </div>
            <div className="text-[10px] text-neutral-400 uppercase">{order.currency}</div>
          </div>
        </div>

        {/* Product & Retailer Details */}
        <div className="p-4 rounded-xl bg-white dark:bg-[#17191C] border border-neutral-200/80 dark:border-neutral-800 flex flex-col gap-3">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400">
            Purchased Item
          </span>
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-neutral-600 dark:text-neutral-300 shrink-0">
              <ShoppingBag size={18} strokeWidth={1.8} />
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-[15px] font-semibold text-neutral-900 dark:text-white leading-snug">
                {order.product_title || 'Purchased Item'}
              </h4>
              <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 flex items-center gap-2 flex-wrap">
                <span>Retailer: <strong className="text-neutral-800 dark:text-neutral-200">{order.retailer_domain || 'Retailer'}</strong></span>
                <span>•</span>
                <span className="tabular-nums">Quantity: {order.quantity || 1} unit</span>
                {order.retailer_buy_url && (
                  <>
                    <span>•</span>
                    <a
                      href={order.retailer_buy_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-neutral-600 dark:text-neutral-300 hover:underline flex items-center gap-1 font-medium"
                    >
                      <span>Retailer Page</span>
                      <ExternalLink size={12} strokeWidth={1.8} />
                    </a>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Payment Identifiers Ledger */}
        <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 flex flex-col gap-2.5 text-xs font-mono">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400 font-sans block mb-1">
            Authoritative Identifiers
          </span>
          <div className="flex items-center justify-between py-1 border-b border-neutral-200/50 dark:border-neutral-800/80">
            <span className="text-neutral-500 font-sans">Carti Order ID</span>
            <span className="text-neutral-900 dark:text-white font-semibold tabular-nums">{order.id}</span>
          </div>

          <div className="flex items-center justify-between py-1 border-b border-neutral-200/50 dark:border-neutral-800/80">
            <span className="text-neutral-500 font-sans">PayPal Capture ID</span>
            <span className="text-neutral-900 dark:text-white font-semibold tabular-nums">
              {order.paypal_capture_id || 'CAP-SIMULATED-DEV'}
            </span>
          </div>

          {order.proposal_id && (
            <div className="flex items-center justify-between py-1 border-b border-neutral-200/50 dark:border-neutral-800/80">
              <span className="text-neutral-500 font-sans">Verified Proposal ID</span>
              <span className="text-neutral-900 dark:text-white truncate max-w-[200px] tabular-nums">
                {order.proposal_id}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between py-1">
            <span className="text-neutral-500 font-sans">Verification Method</span>
            <span className="text-emerald-700 dark:text-emerald-400 font-semibold font-sans flex items-center gap-1">
              <ShieldCheck size={14} strokeWidth={1.8} /> B10 Server Verified
            </span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-neutral-100 dark:border-neutral-800">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close Receipt
          </Button>

          {isRefundable && (
            <Button
              variant="danger"
              size="sm"
              icon={<RotateCcw size={16} strokeWidth={1.8} />}
              onClick={() => {
                onClose()
                onRequestRefund(order)
              }}
            >
              Refund Order (${order.amount})
            </Button>
          )}
        </div>
      </div>
    </Modal>
  )
}
