import React, { useState } from 'react'
import { RotateCcw, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { Order, Refund } from '../../api/types'
import { Modal } from '../common/Modal'
import { Button } from '../common/Button'
import { api } from '../../api/client'
import { useAuth } from '../../context/AuthContext'

interface RefundModalProps {
  order: Order | null
  isOpen: boolean
  onClose: () => void
  onRefundSuccess: (refund: Refund) => void
}

export const RefundModal: React.FC<RefundModalProps> = ({
  order,
  isOpen,
  onClose,
  onRefundSuccess,
}) => {
  const { refreshMandate } = useAuth()
  const [reason, setReason] = useState('Customer return / unsatisfied with product')
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!order) return null

  const handleConfirmRefund = async () => {
    try {
      setIsProcessing(true)
      setError(null)

      const res = await api.refundOrder(order.id, reason)
      await refreshMandate()

      onRefundSuccess(res)
      onClose()
    } catch (err: any) {
      setError(err?.message || 'Failed to process refund with PayPal')
      setIsProcessing(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Confirm Full Order Refund" maxWidth="sm">
      <div className="flex flex-col gap-5">
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 text-xs flex items-start gap-2.5 leading-relaxed">
          <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          <span>
            You are requesting a full refund of <strong>${order.amount} {order.currency}</strong> for PayPal Capture ID{' '}
            <code className="font-mono">{order.paypal_capture_id}</code>. This action is non-reversible.
          </span>
        </div>

        {error && (
          <div className="p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold uppercase text-neutral-600 dark:text-neutral-400">
            Refund Reason (Sent to PayPal Payer note)
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={2}
            className="w-full rounded-xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200 dark:border-neutral-700 p-3 text-xs text-neutral-900 dark:text-white outline-hidden"
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-neutral-100 dark:border-neutral-800">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={isProcessing}>
            Cancel
          </Button>
          <Button
            variant="danger"
            size="md"
            icon={<RotateCcw size={16} />}
            loading={isProcessing}
            onClick={handleConfirmRefund}
          >
            Confirm & Execute Refund (${order.amount})
          </Button>
        </div>
      </div>
    </Modal>
  )
}
