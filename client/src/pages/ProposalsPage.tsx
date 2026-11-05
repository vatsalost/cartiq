import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileCheck2, ArrowLeft, AlertCircle, ShoppingBag } from 'lucide-react'
import { ProposalSummaryCard } from '../components/proposal/ProposalSummaryCard'
import { VerificationChecksPanel } from '../components/proposal/VerificationChecksPanel'
import { PayPalCheckoutModal } from '../components/checkout/PayPalCheckoutModal'
import { Button } from '../components/common/Button'
import { api } from '../api/client'
import { Proposal, Order } from '../api/types'
import { mockProposal } from '../api/mockData'
import { useAuth } from '../context/AuthContext'

export const ProposalsPage: React.FC = () => {
  const navigate = useNavigate()
  const { refreshMandate } = useAuth()
  const [proposal, setProposal] = useState<Proposal>(mockProposal)
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false)
  const [isRejecting, setIsRejecting] = useState(false)
  const [rejectSuccess, setRejectSuccess] = useState(false)

  useEffect(() => {
    async function loadActiveProposal() {
      try {
        const prop = await api.getProposal('prop_98765432-1111-2222-3333-444455556666')
        if (prop) setProposal(prop)
      } catch {
        // Fallback to mock proposal already in state
      }
    }
    loadActiveProposal()
  }, [])

  const handleReject = async () => {
    try {
      setIsRejecting(true)
      await api.rejectProposal(proposal.id, 'User rejected in frontend review')
      await refreshMandate()
      setProposal({ ...proposal, status: 'rejected' })
      setRejectSuccess(true)
    } catch (e) {
      console.error('Rejection failed:', e)
    } finally {
      setIsRejecting(false)
    }
  }

  const handleCheckoutSuccess = (order: Order) => {
    refreshMandate()
    navigate('/orders', { state: { newOrder: order } })
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Top Navigation Row */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/shopping')}
          icon={<ArrowLeft size={16} />}
        >
          Back to Shopping
        </Button>
        <span className="text-xs text-neutral-500 font-mono">
          Mandate Snapshot: v{proposal.mandate_version}
        </span>
      </div>

      {rejectSuccess && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 text-sm font-medium flex items-center gap-2">
          <AlertCircle size={18} />
          <span>
            Proposal rejected. In-flight budget reservation of ${proposal.total_amount} has been released.
          </span>
        </div>
      )}

      {/* Main Review Card & Guardrail Checks */}
      <div className="flex flex-col gap-6">
        <ProposalSummaryCard
          proposal={proposal}
          onProceedToCheckout={() => setIsCheckoutOpen(true)}
          onReject={handleReject}
          isRejecting={isRejecting}
        />

        <VerificationChecksPanel guardrailResult={proposal.guardrail_result} />
      </div>

      {/* PayPal Checkout Modal */}
      <PayPalCheckoutModal
        proposal={proposal}
        isOpen={isCheckoutOpen}
        onClose={() => setIsCheckoutOpen(false)}
        onSuccess={handleCheckoutSuccess}
      />
    </div>
  )
}
