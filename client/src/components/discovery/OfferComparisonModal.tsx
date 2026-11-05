import React from 'react'
import { Check, X, ExternalLink, ShieldCheck, Tag } from 'lucide-react'
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
    <Modal isOpen={isOpen} onClose={onClose} title="Compare Retailer Offers" maxWidth="lg">
      <div className="flex flex-col gap-6">
        <div>
          <h4 className="text-lg font-bold text-neutral-900 dark:text-white">
            {product.title}
          </h4>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
            Prices and availability verified across approved retailers
          </p>
        </div>

        {/* Side-by-side Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-800 text-neutral-400 uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Retailer</th>
                <th className="py-2.5 px-3">Price</th>
                <th className="py-2.5 px-3">Stock Availability</th>
                <th className="py-2.5 px-3">Condition</th>
                <th className="py-2.5 px-3">Mandate Guardrails</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {product.offers.map((offer) => (
                <tr
                  key={offer.id}
                  className={`hover:bg-neutral-50/50 dark:hover:bg-neutral-800/30 transition-colors ${
                    !offer.is_eligible ? 'opacity-60 bg-rose-500/5' : ''
                  }`}
                >
                  <td className="py-3.5 px-3 font-bold text-neutral-900 dark:text-white">
                    <div className="flex items-center gap-1.5">
                      <span>{offer.domain}</span>
                      <a
                        href={offer.buy_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
                      >
                        <ExternalLink size={12} />
                      </a>
                    </div>
                  </td>
                  <td className="py-3.5 px-3 font-black text-sm text-neutral-900 dark:text-white">
                    ${offer.price_amount} {offer.currency}
                  </td>
                  <td className="py-3.5 px-3">
                    {offer.availability === 'InStock' ? (
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                        <Check size={12} /> In Stock
                      </span>
                    ) : (
                      <span className="text-rose-500 font-medium">Out of Stock</span>
                    )}
                  </td>
                  <td className="py-3.5 px-3 capitalize text-neutral-600 dark:text-neutral-300">
                    {offer.condition}
                  </td>
                  <td className="py-3.5 px-3">
                    {offer.is_eligible ? (
                      <Badge variant="success" size="sm">
                        Passed All Checks
                      </Badge>
                    ) : (
                      <div className="text-rose-600 dark:text-rose-400 text-[11px] font-medium leading-tight">
                        {offer.ineligibility_reason}
                      </div>
                    )}
                  </td>
                  <td className="py-3.5 px-3 text-right">
                    <Button
                      type="button"
                      variant={offer.is_eligible ? 'primary' : 'outline'}
                      size="sm"
                      disabled={!offer.is_eligible}
                      onClick={() => {
                        onSelectOffer(product, offer)
                        onClose()
                      }}
                    >
                      Select
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-neutral-100 dark:border-neutral-800 text-xs text-neutral-500">
          <span>* Only eligible offers that conform to mandate rules can be proposed.</span>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  )
}
