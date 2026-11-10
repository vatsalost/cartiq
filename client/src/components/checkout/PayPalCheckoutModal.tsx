import React, { useState } from 'react'
import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js'
import { ShieldCheck, AlertCircle, ShoppingBag, CheckCircle, Info } from 'lucide-react'
import { Proposal, Order } from '../../api/types'
import { Modal } from '../common/Modal'
import { Button } from '../common/Button'
import { api } from '../../api/client'

interface PayPalCheckoutModalProps {
  proposal: Proposal
  isOpen: boolean
  onClose: () => void
  onSuccess: (order: Order) => void
}

export const PayPalCheckoutModal: React.FC<PayPalCheckoutModalProps> = ({
  proposal,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [internalOrderId, setInternalOrderId] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isApproved, setIsApproved] = useState(false)

  const paypalClientId = import.meta.env.VITE_PAYPAL_CLIENT_ID || 'test'

  const handleCreateOrder = async (): Promise<string> => {
    try {
      setIsProcessing(true)
      setErrorMessage(null)
      const attemptId = `attempt_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`

      const res = await api.createOrderFromProposal(proposal.id, attemptId)
      if (res.paypal_order_id.startsWith('PP-SANDBOX-')) {
        throw new Error('Server returned synthetic order ID. Real PayPal SDK requires a live PayPal order. Please use Direct Sandbox Capture.')
      }
      setInternalOrderId(res.order_id)
      return res.paypal_order_id
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to create PayPal order')
      setIsProcessing(false)
      throw err
    }
  }

  const handleApprove = async (data: any) => {
    try {
      setIsProcessing(true)
      setIsApproved(true)

      const targetOrderId = internalOrderId || `ord_${Date.now()}`
      const capturedOrder = await api.captureOrder(targetOrderId, data.orderID)

      onSuccess(capturedOrder)
      onClose()
    } catch (err: any) {
      setErrorMessage(err.message || 'Payment capture failed server-side')
      setIsProcessing(false)
    }
  }

  const handleSimulateSandboxCheckout = async () => {
    try {
      setIsProcessing(true)
      setErrorMessage(null)

      const attemptId = `attempt_sim_${Date.now()}`
      const created = await api.createOrderFromProposal(proposal.id, attemptId)
      const captured = await api.captureOrder(created.order_id, created.paypal_order_id)

      onSuccess(captured)
      onClose()
    } catch (err: any) {
      setErrorMessage(err.message || 'Sandbox simulation failed')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="PayPal Sandbox Checkout"
      description="Authorize purchase under active mandate version lock"
      maxWidth="md"
    >
      <div className="flex flex-col gap-4">
        {/* Order Summary Pill */}
        <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-neutral-700 dark:text-neutral-300">
              <ShoppingBag size={16} strokeWidth={1.8} />
            </div>
            <div>
              <div className="text-xs font-semibold text-neutral-900 dark:text-white line-clamp-1">
                {proposal.product?.title || 'Proposed Product'}
              </div>
              <div className="text-[11px] text-neutral-400">
                Verified retailer: {proposal.offer?.domain || 'target.com'}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-base font-bold text-neutral-900 dark:text-white font-mono tabular-nums">
              ${proposal.total_amount}
            </div>
            <div className="text-[10px] text-neutral-400 uppercase">{proposal.currency}</div>
          </div>
        </div>

        {errorMessage && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 dark:bg-rose-500/10 dark:border-rose-500/20 dark:text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle size={16} strokeWidth={1.8} className="shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* PayPal SDK Buttons Section */}
        <div className="flex flex-col gap-2 pt-1">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Authorize Payment Method
          </div>

          <div className="min-h-[140px] flex flex-col justify-center rounded-xl p-3 bg-neutral-50/50 dark:bg-[#141619]/50 border border-neutral-200/60 dark:border-neutral-800">
            <PayPalScriptProvider
              options={{
                clientId: paypalClientId,
                currency: proposal.currency || 'USD',
                intent: 'capture',
              }}
            >
              <PayPalButtons
                style={{ layout: 'vertical', shape: 'rect', height: 40 }}
                createOrder={handleCreateOrder}
                onApprove={handleApprove}
                disabled={isProcessing}
              />
            </PayPalScriptProvider>
          </div>
        </div>

        {/* Sandbox Fallback Simulator Action */}
        <div className="p-3 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 flex items-center justify-between gap-3 text-xs">
          <div>
            <div className="font-semibold text-neutral-800 dark:text-neutral-200">
              Direct Sandbox Capture
            </div>
            <div className="text-[11px] text-neutral-400">
              Executes B10 server-side capture without entering sandbox credentials
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            size="xs"
            onClick={handleSimulateSandboxCheckout}
            loading={isProcessing}
          >
            Execute Capture
          </Button>
        </div>

        {/* Compliance Footer Note */}
        <div className="p-2.5 rounded-lg bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/30 text-[11px] text-amber-800 dark:text-amber-300 flex items-start gap-2 leading-relaxed">
          <Info size={13} className="shrink-0 mt-0.5" />
          <span>
            <strong>Sandbox Notice:</strong> This authorization is processed within the PayPal developer sandbox. It does not initiate real banking transfers or external retailer fulfillments.
          </span>
        </div>
      </div>
    </Modal>
  )
}
