import React, { useState } from 'react'
import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js'
import { ShieldCheck, AlertCircle, ShoppingBag, CheckCircle } from 'lucide-react'
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

  // Demo client ID (standard public sandbox client ID from PayPal documentation)
  const paypalClientId = 'test'

  const handleCreateOrder = async (): Promise<string> => {
    try {
      setIsProcessing(true)
      setErrorMessage(null)
      const attemptId = `attempt_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`

      // 1. Authoritative server-side order initialization
      const res = await api.createOrderFromProposal(proposal.id, attemptId)
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
    <Modal isOpen={isOpen} onClose={onClose} title="PayPal Sandbox Checkout" maxWidth="md">
      <div className="flex flex-col gap-5">
        {/* Order Summary Pill */}
        <div className="p-4 rounded-2xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/80 dark:border-neutral-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-neutral-700 dark:text-neutral-300">
              <ShoppingBag size={18} />
            </div>
            <div>
              <div className="text-sm font-bold text-neutral-900 dark:text-white line-clamp-1">
                {proposal.product?.title || 'Proposed Product'}
              </div>
              <div className="text-xs text-neutral-500 dark:text-neutral-400">
                Authorized total from verified proposal
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-lg font-black text-neutral-900 dark:text-white">
              ${proposal.total_amount}
            </div>
            <div className="text-[10px] font-bold text-neutral-400">{proposal.currency}</div>
          </div>
        </div>

        {/* Security Notice */}
        <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-2">
          <ShieldCheck size={16} className="shrink-0 text-emerald-600 dark:text-emerald-400" />
          <span>
            Server-side authoritative pricing. Browser and frontend cannot alter monetary amounts.
          </span>
        </div>

        {errorMessage && (
          <div className="p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle size={16} className="shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {isApproved && (
          <div className="p-4 rounded-2xl bg-[#98EC6A]/20 dark:bg-[#2CE5B5]/20 border border-[#98EC6A] dark:border-[#2CE5B5] text-[#0A2610] dark:text-[#2CE5B5] text-xs font-bold flex items-center gap-2">
            <CheckCircle size={16} />
            <span>Buyer approved on PayPal. Executing server-side capture...</span>
          </div>
        )}

        {/* Real PayPal Buttons through SDK */}
        <div className="py-2 min-h-[140px] flex flex-col justify-center">
          <PayPalScriptProvider
            options={{
              clientId: paypalClientId,
              currency: proposal.currency || 'USD',
              intent: 'capture',
            }}
          >
            <PayPalButtons
              style={{
                layout: 'vertical',
                color: 'gold',
                shape: 'pill',
                label: 'checkout',
                height: 42,
              }}
              disabled={isProcessing}
              createOrder={handleCreateOrder}
              onApprove={handleApprove}
              onCancel={() => {
                setErrorMessage('PayPal checkout was cancelled by the user.')
                setIsProcessing(false)
              }}
              onError={(err) => {
                console.error('PayPal Buttons Error:', err)
                setErrorMessage('PayPal component encountered an error. You can use the Sandbox Direct Capture button below.')
                setIsProcessing(false)
              }}
            />
          </PayPalScriptProvider>
        </div>

        {/* Fallback Direct Sandbox Capture Button for hackathon test convenience */}
        <div className="pt-2 border-t border-neutral-100 dark:border-neutral-800 flex flex-col gap-2">
          <div className="text-[11px] text-neutral-400 text-center">
            Or execute verified server-side Sandbox capture directly:
          </div>
          <Button
            type="button"
            variant="dark"
            size="md"
            className="w-full justify-center"
            onClick={handleSimulateSandboxCheckout}
            loading={isProcessing}
          >
            Execute Verified Sandbox Capture (${proposal.total_amount})
          </Button>
        </div>
      </div>
    </Modal>
  )
}
