import React, { useState } from 'react'
import { ExternalLink, ShieldCheck, AlertCircle, ShoppingCart, ChevronDown, ChevronUp, Info, CheckCircle2 } from 'lucide-react'
import { Proposal } from '../../api/types'
import { Button } from '../common/Button'
import { Badge } from '../common/Badge'

interface ProposalSummaryCardProps {
  proposal: Proposal
  onProceedToCheckout: () => void
  onReject: () => void
  isRejecting?: boolean
}

export const ProposalSummaryCard: React.FC<ProposalSummaryCardProps> = ({
  proposal,
  onProceedToCheckout,
  onReject,
  isRejecting = false,
}) => {
  const [showRationale, setShowRationale] = useState(true)
  const isPending = proposal.status === 'pending' || proposal.status === 'accepted'

  return (
    <div className="rounded-xl p-5 md:p-6 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-5">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center font-bold">
            <ShieldCheck size={18} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-neutral-900 dark:text-white">
                Purchase Proposal
              </h3>
              <Badge variant="lime" size="xs">
                Mandate v{proposal.mandate_version} Locked
              </Badge>
              <Badge variant="success" size="xs" dot>
                Approved
              </Badge>
            </div>
            <p className="text-[11px] text-neutral-400 font-mono mt-0.5">
              ID: {proposal.id}
            </p>
          </div>
        </div>

        {proposal.verification_status === 'verified' && (
          <span className="text-xs font-medium px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20 flex items-center gap-1.5 self-start sm:self-auto">
            <CheckCircle2 size={13} /> Live Stock Verified
          </span>
        )}
      </div>

      {/* Side-by-Side Product Info & Pricing Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Product Media & Rationale (7 cols) */}
        <div className="lg:col-span-7 flex flex-col sm:flex-row gap-4">
          {/* Image */}
          <div className="w-full sm:w-48 h-48 rounded-xl overflow-hidden bg-neutral-100 dark:bg-neutral-800 shrink-0 border border-neutral-200/80 dark:border-neutral-700/80 relative">
            {proposal.product?.image_url ? (
              <img
                src={proposal.product.image_url}
                alt={proposal.product.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-xs text-neutral-400">
                No Image
              </div>
            )}
            {proposal.product?.brand && (
              <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-black/70 backdrop-blur-xs text-white text-[10px] font-medium">
                {proposal.product.brand}
              </div>
            )}
          </div>

          {/* Details & Expandable Rationale */}
          <div className="flex-1 flex flex-col justify-between gap-3 min-w-0">
            <div>
              <h4 className="text-sm md:text-base font-semibold text-neutral-900 dark:text-white leading-snug">
                {proposal.product?.title || 'Selected Verified Product'}
              </h4>

              <div className="flex items-center gap-3 text-xs text-neutral-500 dark:text-neutral-400 mt-2 flex-wrap">
                <span>
                  Retailer: <strong className="text-neutral-800 dark:text-neutral-200">{proposal.offer?.domain || 'target.com'}</strong>
                </span>
                <span>•</span>
                <span>
                  Quantity: <strong className="text-neutral-800 dark:text-neutral-200">{proposal.quantity} unit</strong>
                </span>
                {proposal.offer?.buy_url && (
                  <>
                    <span>•</span>
                    <a
                      href={proposal.offer.buy_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-neutral-600 dark:text-neutral-300 hover:underline flex items-center gap-1 font-medium"
                    >
                      <span>Retailer URL</span>
                      <ExternalLink size={11} />
                    </a>
                  </>
                )}
              </div>
            </div>

            {/* Expandable AI Rationale */}
            {proposal.rationale && (
              <div className="p-3 rounded-lg bg-[#F5F6F3] dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800">
                <button
                  type="button"
                  onClick={() => setShowRationale(!showRationale)}
                  className="w-full flex items-center justify-between text-xs font-semibold text-neutral-800 dark:text-neutral-200 cursor-pointer"
                >
                  <span className="flex items-center gap-1.5">
                    <span>AI Selection Rationale</span>
                  </span>
                  {showRationale ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
                {showRationale && (
                  <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-2 leading-relaxed">
                    {proposal.rationale}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right: Pricing Breakdown & Financial Guardrails (5 cols) */}
        <div className="lg:col-span-5 p-4 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 flex flex-col justify-between gap-4">
          <div>
            <div className="text-xs font-semibold text-neutral-900 dark:text-white uppercase tracking-wider pb-2 border-b border-neutral-200/60 dark:border-neutral-800">
              Pricing Breakdown
            </div>

            <div className="flex flex-col gap-2 mt-3 text-xs">
              <div className="flex items-center justify-between text-neutral-600 dark:text-neutral-400">
                <span>Unit Price</span>
                <span className="font-mono text-neutral-900 dark:text-white font-medium">
                  ${proposal.unit_price_at_proposal}
                </span>
              </div>

              <div className="flex items-center justify-between text-neutral-600 dark:text-neutral-400">
                <span>Estimated Shipping</span>
                <span className="font-mono text-neutral-900 dark:text-white font-medium">
                  ${proposal.shipping_amount || '0.00'}
                </span>
              </div>

              <div className="flex items-center justify-between text-neutral-600 dark:text-neutral-400">
                <span>Estimated Tax</span>
                <span className="font-mono text-neutral-900 dark:text-white font-medium">
                  ${proposal.tax_amount || '0.00'}
                </span>
              </div>

              <div className="pt-2.5 mt-1 border-t border-neutral-200/60 dark:border-neutral-800 flex items-center justify-between font-bold text-sm text-neutral-900 dark:text-white">
                <span>Authoritative Total</span>
                <span className="font-mono text-base font-bold text-neutral-900 dark:text-white">
                  ${proposal.total_amount} <span className="text-xs font-normal text-neutral-400">{proposal.currency}</span>
                </span>
              </div>
            </div>
          </div>

          {/* Sandbox Notice */}
          <div className="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-800/40 text-[11px] text-amber-800 dark:text-amber-300 leading-normal flex items-start gap-2">
            <Info size={14} className="shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
            <span>
              <strong>PayPal Sandbox Notice:</strong> Payment authorization executes in the simulated PayPal sandbox environment. Completing checkout does not automatically place an order on the external merchant website.
            </span>
          </div>
        </div>
      </div>

      {/* Prominent Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-4 border-t border-neutral-100 dark:border-neutral-800">
        <div className="text-xs text-neutral-500 dark:text-neutral-400">
          Proposal Status: <strong className="capitalize text-neutral-800 dark:text-neutral-200">{proposal.status}</strong>
        </div>

        <div className="flex items-center gap-2.5 self-end sm:self-auto">
          {isPending && (
            <Button
              variant="outline"
              size="sm"
              onClick={onReject}
              loading={isRejecting}
              className="text-neutral-600 hover:text-rose-600 dark:text-neutral-400 dark:hover:text-rose-400"
            >
              Reject Proposal
            </Button>
          )}

          <Button
            variant="primary"
            size="sm"
            onClick={onProceedToCheckout}
            disabled={!isPending}
            icon={<ShoppingCart size={14} />}
          >
            Continue with PayPal Checkout
          </Button>
        </div>
      </div>
    </div>
  )
}
