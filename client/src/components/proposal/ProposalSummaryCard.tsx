import React from 'react'
import { ExternalLink, ShieldCheck, AlertCircle, ShoppingCart } from 'lucide-react'
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
  const isPending = proposal.status === 'pending' || proposal.status === 'accepted'

  return (
    <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-[#16181D] border border-neutral-200 dark:border-neutral-800 shadow-xs flex flex-col gap-5">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-neutral-100 dark:border-neutral-800">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-neutral-900 dark:text-white">
              Purchase Proposal
            </h3>
            <Badge variant="lime" size="sm">
              Mandate v{proposal.mandate_version}
            </Badge>
            <Badge variant="success" size="sm">
              Approved
            </Badge>
          </div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
            Proposal ID: {proposal.id}
          </p>
        </div>

        {proposal.verification_status === 'verified' && (
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 flex items-center gap-1 self-start sm:self-auto">
            <ShieldCheck size={13} /> Stock Verified
          </span>
        )}
      </div>

      {/* Product & Price Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Product Snapshot Image */}
        <div className="rounded-xl overflow-hidden bg-neutral-100 dark:bg-neutral-800 h-48 md:h-auto relative border border-neutral-200/60 dark:border-neutral-700/60">
          {proposal.product?.image_url ? (
            <img
              src={proposal.product.image_url}
              alt={proposal.product.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-xs text-neutral-400">
              Product Image
            </div>
          )}
          {proposal.product?.brand && (
            <div className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-xs text-white text-[11px] font-medium">
              {proposal.product.brand}
            </div>
          )}
        </div>

        {/* Details & Rationale */}
        <div className="md:col-span-2 flex flex-col justify-between gap-4">
          <div>
            <h4 className="text-base font-bold text-neutral-900 dark:text-white leading-snug">
              {proposal.product?.title || 'Selected Product'}
            </h4>
            <div className="flex items-center gap-3 text-xs text-neutral-500 dark:text-neutral-400 mt-1.5 flex-wrap">
              <span>Retailer: <strong className="text-neutral-800 dark:text-neutral-200">{proposal.offer?.domain || 'target.com'}</strong></span>
              <span>•</span>
              <span>Quantity: <strong className="text-neutral-800 dark:text-neutral-200">{proposal.quantity} unit</strong></span>
              {proposal.offer?.buy_url && (
                <>
                  <span>•</span>
                  <a
                    href={proposal.offer.buy_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-neutral-600 dark:text-neutral-300 hover:underline flex items-center gap-1 font-medium"
                  >
                    <span>View Retailer Page</span>
                    <ExternalLink size={11} />
                  </a>
                </>
              )}
            </div>

            {/* Selection Rationale */}
            {proposal.rationale && (
              <div className="mt-3 p-3 rounded-xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/60 dark:border-neutral-800">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400 block mb-0.5">
                  Selection Rationale
                </span>
                <p className="text-xs text-neutral-700 dark:text-neutral-300 leading-relaxed">
                  {proposal.rationale}
                </p>
              </div>
            )}
          </div>

          {/* Pricing Ledger Breakdown */}
          <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/80 dark:border-neutral-700/60 flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-xs text-neutral-600 dark:text-neutral-400">
              <span>Item Price</span>
              <span className="font-medium text-neutral-900 dark:text-white">
                ${proposal.unit_price_at_proposal}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs text-neutral-600 dark:text-neutral-400">
              <span>Shipping</span>
              <span className="font-medium text-neutral-900 dark:text-white">
                {proposal.shipping_amount === '0.00' ? 'FREE' : `$${proposal.shipping_amount}`}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs text-neutral-600 dark:text-neutral-400">
              <span>Estimated Tax</span>
              <span className="font-medium text-neutral-900 dark:text-white">
                ${proposal.tax_amount}
              </span>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-neutral-200 dark:border-neutral-700 text-sm">
              <span className="font-bold text-neutral-900 dark:text-white">
                Total Authorized Amount
              </span>
              <span className="text-lg font-extrabold text-neutral-900 dark:text-white">
                ${proposal.total_amount} {proposal.currency}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Sandbox Payment Disclosure */}
      <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 text-xs flex items-start gap-2">
        <AlertCircle size={15} className="shrink-0 mt-0.5" />
        <span>
          <strong>Sandbox Notice:</strong> This order uses PayPal Sandbox. No real money will be charged, and demo orders will not be physically fulfilled.
        </span>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pt-2 border-t border-neutral-100 dark:border-neutral-800">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onReject}
          loading={isRejecting}
        >
          Reject Proposal
        </Button>
        <Button
          type="button"
          variant="primary"
          size="md"
          onClick={onProceedToCheckout}
          disabled={!isPending}
          icon={<ShoppingCart size={15} />}
        >
          Continue with PayPal
        </Button>
      </div>
    </div>
  )
}
