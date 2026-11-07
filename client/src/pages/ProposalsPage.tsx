import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, AlertCircle, ShieldCheck } from 'lucide-react'
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
        // Fallback to mock proposal
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-neutral-900 dark:text-white tracking-tight">
            Purchase Proposals
          </h2>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
            Review AI recommended products with deterministic mandate verification and checkout
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/shopping')}
            icon={<ArrowLeft size={14} />}
          >
            Back to Shopping
          </Button>
        </div>
      </div>

      {rejectSuccess && (
        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 dark:bg-amber-950/20 dark:border-amber-800/40 dark:text-amber-300 text-xs font-medium flex items-center gap-2 animate-in fade-in">
          <AlertCircle size={16} className="shrink-0" />
          <span>
            Proposal rejected. In-flight budget reservation of ${proposal.total_amount} {proposal.currency} has been released.
          </span>
        </div>
      )}

      {/* Main Review Card & 8 Guardrail Checks */}
      <div className="flex flex-col gap-5">
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
