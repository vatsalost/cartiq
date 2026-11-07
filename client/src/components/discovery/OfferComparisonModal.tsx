import React from 'react'
import { Check, X, ExternalLink, ShieldCheck, Tag, ArrowRight } from 'lucide-react'
import { CandidateProduct, CandidateOffer } from '../../api/types'
import { Modal } from '../common/Modal'
import { Button } from '../common/Button'
import { Badge } from '../common/Badge'

interface OfferComparisonModalProps {
  product: CandidateProduct | null
  isOpen: boolean
  onClose: () => void
  onSelectOffer: (product: CandidateProduct, offer: CandidateOffer) => void
}

export const OfferComparisonModal: React.FC<OfferComparisonModalProps> = ({
  product,
  isOpen,
  onClose,
  onSelectOffer,
}) => {
  if (!product) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Multi-Retailer Offer Matrix"
      description={`Comparing verified pricing, stock, and mandate limits for "${product.title}"`}
      maxWidth="lg"
    >
      <div className="flex flex-col gap-4">
        {/* Comparison Table */}
        <div className="overflow-x-auto border border-neutral-200/80 dark:border-neutral-800 rounded-xl">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-neutral-50 dark:bg-[#141619] border-b border-neutral-200/80 dark:border-neutral-800 text-neutral-500 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3.5">Retailer Domain</th>
                <th className="py-2.5 px-3.5">Price Quote</th>
                <th className="py-2.5 px-3.5">Live Stock</th>
                <th className="py-2.5 px-3.5">Condition</th>
                <th className="py-2.5 px-3.5">Mandate Status</th>
                <th className="py-2.5 px-3.5 text-right">Select</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {product.offers.map((offer) => (
                <tr
                  key={offer.id}
                  className={`hover:bg-neutral-50/50 dark:hover:bg-neutral-800/30 transition-colors ${
                    !offer.is_eligible ? 'opacity-70 bg-rose-50/30 dark:bg-rose-950/10' : ''
                  }`}
                >
                  <td className="py-3 px-3.5 font-semibold text-neutral-900 dark:text-white">
                    <div className="flex items-center gap-1.5">
                      <span>{offer.domain}</span>
                      {offer.buy_url && (
                        <a
                          href={offer.buy_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
                        >
                          <ExternalLink size={14} strokeWidth={1.8} />
                        </a>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-3.5 font-bold text-neutral-900 dark:text-white tabular-nums">
                    ${offer.price_amount} <span className="text-[10px] text-neutral-400 font-normal">{offer.currency}</span>
                  </td>
                  <td className="py-3 px-3.5">
                    {offer.availability === 'InStock' ? (
                      <span className="text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1">
                        <Check size={14} strokeWidth={2} /> In Stock
                      </span>
                    ) : (
                      <span className="text-rose-500 font-medium">Out of Stock</span>
                    )}
                  </td>
                  <td className="py-3 px-3.5 capitalize text-neutral-600 dark:text-neutral-300">
                    {offer.condition}
                  </td>
                  <td className="py-3 px-3.5">
                    {offer.is_eligible ? (
                      <Badge variant="success" size="xs" dot>
                        Passed Guardrails
                      </Badge>
                    ) : (
                      <div className="text-rose-600 dark:text-rose-400 text-[11px] font-medium leading-tight max-w-[180px]">
                        {offer.ineligibility_reason}
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-3.5 text-right">
                    <Button
                      type="button"
                      variant={offer.is_eligible ? 'primary' : 'outline'}
                      size="xs"
                      disabled={!offer.is_eligible}
                      onClick={() => {
                        onSelectOffer(product, offer)
                        onClose()
                      }}
                      icon={offer.is_eligible ? <ArrowRight size={11} /> : undefined}
                    >
                      {offer.is_eligible ? 'Select' : 'Ineligible'}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="text-[11px] text-neutral-400 flex items-center gap-1.5 pt-1">
          <ShieldCheck size={13} className="text-[#95EB68]" />
          <span>All offers are validated against your active mandate limits and approved retailer policy.</span>
        </div>
      </div>
    </Modal>
  )
}
