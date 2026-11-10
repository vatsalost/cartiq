import React, { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ShoppingCart,
  Check,
  ShieldCheck,
  AlertCircle,
  Info,
  ArrowRight,
  ExternalLink,
} from 'lucide-react'
import { PayPalCheckoutModal } from '../components/checkout/PayPalCheckoutModal'
import { Button } from '../components/common/Button'
import { api } from '../api/client'
import { Proposal, Order } from '../api/types'
import { mockProposal } from '../api/mockData'
import { useAuth } from '../context/AuthContext'

export const ProposalsPage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const selectedProduct = location.state?.product
  const { refreshMandate, breakdown, mandate } = useAuth()
  const [proposal, setProposal] = useState<Proposal>(mockProposal)
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false)
  const [isRejecting, setIsRejecting] = useState(false)
  const [rejectSuccess, setRejectSuccess] = useState(false)

  useEffect(() => {
    async function loadActiveProposal() {
      if (selectedProduct) {
        const rawPrice = selectedProduct.price.replace(/[^0-9.]/g, '') || '49.99'
        const domain = selectedProduct.retailerUrl
          ? selectedProduct.retailerUrl.replace(/^https?:\/\//, '').replace(/\/.*$/, '')
          : `${selectedProduct.retailer.toLowerCase()}.com`
        setProposal({
          ...mockProposal,
          id: '98765432-1111-2222-3333-444455556666',
          unit_price_at_proposal: rawPrice,
          subtotal_at_proposal: rawPrice,
          total_amount: rawPrice,
          currency: 'USD',
          product: {
            product_id: selectedProduct.id,
            title: selectedProduct.title,
            brand: selectedProduct.title.split(' ')[0] || 'Selected Brand',
            category: 'Electronics',
            image_url: selectedProduct.imageUrl,
          },
          offer: {
            offer_id: 'off_98765432-2222-3333-4444-555566667777',
            domain: domain,
            buy_url: selectedProduct.retailerUrl || `https://www.${domain}`,
            price_amount: rawPrice,
            currency: 'USD',
            availability: 'in_stock',
            condition: 'new',
          },
          rationale: `Selected best match from comparison matrix for "${selectedProduct.title}". Compliant with $60 item cap and verified within active spending mandate.`,
        })
        return
      }

      try {
        const prop = await api.getProposal('98765432-1111-2222-3333-444455556666')
        if (prop) setProposal(prop)
      } catch {
        // Use default mock proposal
      }
    }
    loadActiveProposal()
  }, [selectedProduct])

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

  const totalBudget = mandate ? parseFloat(mandate.total_budget) : 0
  const capturedToDate = parseFloat(breakdown?.captured_spending || '0.00')
  const thisPurchase = parseFloat(proposal.total_amount || '0.00')
  const remainingAfter = mandate ? Math.max(0, totalBudget - capturedToDate - thisPurchase).toFixed(2) : '0.00'

  return (
    <div className="flex flex-col gap-5">
      {/* Back Link */}
      <div>
        <button
          onClick={() => navigate('/shopping')}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white transition-colors cursor-pointer"
        >
          <ArrowLeft size={16} strokeWidth={1.8} />
          <span>Back to Shopping</span>
        </button>
      </div>

      {/* Header with Icon, Title, and Metadata Pills */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-neutral-200/80 dark:border-neutral-800">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center font-bold">
            <ShoppingCart size={20} strokeWidth={1.8} />
          </div>
          <div>
            <h1 className="text-[28px] font-bold text-neutral-900 dark:text-white tracking-tight leading-tight">
              Purchase Proposal
            </h1>
          </div>
        </div>

        {/* Metadata Pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-2.5 py-1 rounded-md bg-neutral-100 dark:bg-neutral-800 text-[11px] font-mono tabular-nums text-neutral-600 dark:text-neutral-300">
            Proposal #prop_98765432
          </span>
          <span className="px-2.5 py-1 rounded-md bg-[#95EB68] text-[#17191C] text-[11px] font-semibold flex items-center gap-1">
            <Check size={13} strokeWidth={2.5} />
            <span>All Checks Passed</span>
          </span>
          <span className="px-2.5 py-1 rounded-md bg-neutral-100 dark:bg-neutral-800 text-[11px] font-medium text-neutral-600 dark:text-neutral-300">
            Mandate v{proposal.mandate_version || 2}
          </span>
          <span className="px-2.5 py-1 rounded-md bg-neutral-100 dark:bg-neutral-800 text-[11px] font-medium text-neutral-600 dark:text-neutral-300">
            Stock Verified
          </span>
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

      {/* Main 2-Column Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Column (7 cols): Product Spec + Rationale + Compliance */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          {/* Card 1: Product Snapshot */}
          <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col sm:flex-row gap-5 items-center sm:items-start">
            <div className="w-full sm:w-40 h-40 rounded-lg overflow-hidden bg-neutral-100 dark:bg-neutral-800 shrink-0">
              <img
                src={
                  proposal.product?.image_url ||
                  'https://images.unsplash.com/photo-1534349762230-e0cadf78f5da?w=500&auto=format&fit=crop&q=60'
                }
                alt={proposal.product?.title || 'Product'}
                className="w-full h-full object-cover"
              />
            </div>

            <div className="flex-1 min-w-0 flex flex-col justify-between h-full gap-3">
              <div>
                <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white leading-snug">
                  {proposal.product?.title || 'Modern Brass Desk Lamp with Dimmer'}
                </h3>
                <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 flex items-center gap-2">
                  <span>Target • Electronics & Home</span>
                  <a
                    href="https://www.target.com"
                    target="_blank"
                    rel="noreferrer"
                    className="hover:text-neutral-900 dark:hover:text-white"
                  >
                    <ExternalLink size={14} strokeWidth={1.8} />
                  </a>
                </div>

                <div className="text-xl font-bold text-neutral-900 dark:text-white mt-3 tabular-nums">
                  ${proposal.total_amount}{' '}
                  <span className="text-xs font-normal text-neutral-400">
                    {proposal.currency}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-wrap pt-2">
                <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 text-emerald-700 dark:text-emerald-400 text-[11px] font-medium flex items-center gap-1">
                  <Check size={13} strokeWidth={2} /> In Stock (Target)
                </span>
                <span className="px-2 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 text-[11px] font-medium">
                  Free Shipping
                </span>
              </div>
            </div>
          </div>

          {/* Card 2: Why Carti Selected This Product */}
          <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-3">
            <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
              Why Carti Selected This Product
            </h3>
            <ul className="space-y-2.5">
              <li className="flex items-start gap-2.5 text-xs text-neutral-700 dark:text-neutral-300">
                <div className="w-4 h-4 rounded-full bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0 mt-0.5">
                  <Check size={11} strokeWidth={2.5} />
                </div>
                <span>Ranked #1 of 3 candidates (score: 94/100)</span>
              </li>
              <li className="flex items-start gap-2.5 text-xs text-neutral-700 dark:text-neutral-300">
                <div className="w-4 h-4 rounded-full bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0 mt-0.5">
                  <Check size={11} strokeWidth={2.5} />
                </div>
                <span>Exactly matches aesthetic warm desk lamp with brass finish</span>
              </li>
              <li className="flex items-start gap-2.5 text-xs text-neutral-700 dark:text-neutral-300">
                <div className="w-4 h-4 rounded-full bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0 mt-0.5">
                  <Check size={11} strokeWidth={2.5} />
                </div>
                <span>Real-time stock verified at Target (qty: 12 available)</span>
              </li>
              <li className="flex items-start gap-2.5 text-xs text-neutral-700 dark:text-neutral-300">
                <div className="w-4 h-4 rounded-full bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0 mt-0.5">
                  <Check size={11} strokeWidth={2.5} />
                </div>
                <span>Price $49.99 is 16.7% below $60.00 per-item cap</span>
              </li>
            </ul>
          </div>

          {/* Card 3: Mandate & Compliance */}
          <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-3">
            <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
              Mandate & Compliance
            </h3>
            <ul className="space-y-2.5">
              <li className="flex items-start gap-2.5 text-xs text-neutral-700 dark:text-neutral-300">
                <div className="w-4 h-4 rounded-full bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0 mt-0.5">
                  <Check size={13} strokeWidth={2.5} />
                </div>
                <span>Within per-item cap ($49.99 vs $60.00 limit)</span>
              </li>
              <li className="flex items-start gap-2.5 text-xs text-neutral-700 dark:text-neutral-300">
                <div className="w-4 h-4 rounded-full bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0 mt-0.5">
                  <Check size={13} strokeWidth={2.5} />
                </div>
                <span>Category &apos;home-decor&apos; is explicitly permitted</span>
              </li>
              <li className="flex items-start gap-2.5 text-xs text-neutral-700 dark:text-neutral-300">
                <div className="w-4 h-4 rounded-full bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0 mt-0.5">
                  <Check size={13} strokeWidth={2.5} />
                </div>
                <span>Retailer &apos;Target&apos; is on approved merchant list</span>
              </li>
              <li className="flex items-start gap-2.5 text-xs text-neutral-700 dark:text-neutral-300">
                <div className="w-4 h-4 rounded-full bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0 mt-0.5">
                  <Check size={13} strokeWidth={2.5} />
                </div>
                <span>Budget reservation #res_456789 active ($49.99 held)</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Right Column (5 cols): Price Breakdown + Sandbox Notice + Actions */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          {/* Card: Price Breakdown */}
          <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-4">
            <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white pb-2 border-b border-neutral-100 dark:border-neutral-800">
              Price Breakdown
            </h3>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between text-neutral-600 dark:text-neutral-400">
                <span>Item Price</span>
                <span className="font-semibold text-neutral-900 dark:text-white tabular-nums">
                  ${proposal.unit_price_at_proposal || '49.99'}
                </span>
              </div>
              <div className="flex items-center justify-between text-neutral-600 dark:text-neutral-400">
                <span>Shipping</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">FREE</span>
              </div>
              <div className="flex items-center justify-between text-neutral-600 dark:text-neutral-400">
                <span>Estimated Tax</span>
                <span className="font-semibold text-neutral-900 dark:text-white tabular-nums">$0.00</span>
              </div>

              <div className="pt-2.5 border-t border-neutral-200 dark:border-neutral-700/80 flex items-center justify-between text-sm">
                <span className="font-bold text-neutral-900 dark:text-white">Total</span>
                <span className="font-bold text-neutral-900 dark:text-white text-base tabular-nums">
                  ${proposal.total_amount} {proposal.currency}
                </span>
              </div>
            </div>

            {/* Budget Impact */}
            <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800">
              <div className="text-[11px] font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider mb-2">
                Budget Impact
              </div>
              <div className="space-y-1.5 text-xs text-neutral-600 dark:text-neutral-400">
                <div className="flex items-center justify-between">
                  <span>Total Budget</span>
                  <span className="tabular-nums">${totalBudget.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Captured to Date</span>
                  <span className="tabular-nums">${capturedToDate.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>This Purchase</span>
                  <span className="font-medium text-neutral-900 dark:text-white tabular-nums">
                    ${thisPurchase.toFixed(2)}
                  </span>
                </div>
                <div className="pt-1.5 border-t border-dashed border-neutral-200 dark:border-neutral-800 flex items-center justify-between font-semibold text-neutral-900 dark:text-white">
                  <span>Remaining After</span>
                  <span className="text-[#1D4A18] dark:text-[#95EB68] tabular-nums">${remainingAfter}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sandbox Demo Notice Banner */}
          <div className="p-3.5 rounded-xl bg-neutral-100 dark:bg-neutral-800/60 border border-neutral-200/80 dark:border-neutral-700/60 text-xs text-neutral-600 dark:text-neutral-300 flex items-start gap-2.5">
            <Info size={16} strokeWidth={1.8} className="text-neutral-400 shrink-0 mt-0.5" />
            <div className="leading-relaxed">
              <span className="font-semibold text-neutral-900 dark:text-white">
                PayPal Sandbox Mode
              </span>{' '}
              — Payments are simulated. No real charges will occur.
            </div>
          </div>

          {/* Actions Bar */}
          <div className="flex flex-col gap-2.5">
            <button
              onClick={() => {
                if (!mandate) {
                  navigate('/mandate')
                  return
                }
                setIsCheckoutOpen(true)
              }}
              disabled={proposal.status === 'rejected'}
              className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold bg-[#17191C] hover:bg-neutral-800 text-white dark:bg-[#95EB68] dark:text-[#17191C] dark:hover:bg-[#85da58] transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs disabled:opacity-50"
            >
              <span>{!mandate ? 'Configure Mandate to Checkout' : 'Continue with PayPal Checkout'}</span>
              <ArrowRight size={16} strokeWidth={1.8} />
            </button>

            <Button
              variant="outline"
              size="sm"
              className="w-full justify-center"
              onClick={handleReject}
              disabled={isRejecting || proposal.status === 'rejected'}
              loading={isRejecting}
            >
              <span>Reject Proposal</span>
            </Button>
          </div>
        </div>
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
