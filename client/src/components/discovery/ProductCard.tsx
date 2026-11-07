import React from 'react'
import { Check, AlertTriangle, Sparkles, ArrowRight } from 'lucide-react'
import { CandidateProduct, CandidateOffer } from '../../api/types'
import { Button } from '../common/Button'
import { Badge } from '../common/Badge'

interface ProductCardProps {
  product: CandidateProduct
  onSelectOffer: (product: CandidateProduct, offer: CandidateOffer) => void
  onCompare: (product: CandidateProduct) => void
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onSelectOffer,
  onCompare,
}) => {
  const bestOffer = product.offers.find((o) => o.is_eligible) || product.offers[0]
  const matchPct = Math.round(parseFloat(product.rank_score) * 100)

  return (
    <div className="rounded-xl overflow-hidden bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between transition-all hover:border-neutral-300 dark:hover:border-neutral-700">
      <div>
        {/* Product Image & Badges */}
        <div className="relative w-full h-48 bg-neutral-100 dark:bg-neutral-800 overflow-hidden">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.title}
              className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-neutral-400 text-xs">
              No Product Image
            </div>
          )}

          <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
            <Badge variant="lime" size="xs">
              {matchPct}% Match
            </Badge>
            <Badge variant="neutral" size="xs">
              {product.category || 'General'}
            </Badge>
          </div>

          {product.brand && (
            <div className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-md bg-black/70 backdrop-blur-xs text-white text-[10px] font-medium tracking-wide">
              {product.brand}
            </div>
          )}
        </div>

        {/* Product Information */}
        <div className="p-4 sm:p-5 flex flex-col gap-3">
          <div>
            <h4 className="text-sm font-semibold text-neutral-900 dark:text-white line-clamp-2 leading-snug">
              {product.title}
            </h4>
          </div>

          {/* AI Selection Rationale */}
          <div className="p-2.5 rounded-lg bg-[#F5F6F3] dark:bg-[#131417] border border-neutral-200/70 dark:border-neutral-800/80 text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed flex items-start gap-2">
            <Sparkles size={14} className="text-[#95EB68] shrink-0 mt-0.5" />
            <span className="line-clamp-2">{product.rank_reason}</span>
          </div>

          {/* Retailer Offers Snapshot */}
          <div className="flex flex-col gap-1.5 mt-1">
            <div className="flex items-center justify-between text-[11px] font-medium text-neutral-400">
              <span>Retailer Comparison ({product.offers.length} stores)</span>
              <button
                type="button"
                onClick={() => onCompare(product)}
                className="text-neutral-600 dark:text-neutral-300 hover:underline cursor-pointer"
              >
                Compare matrix
              </button>
            </div>

            <div className="flex flex-col gap-1">
              {product.offers.slice(0, 2).map((offer) => (
                <div
                  key={offer.id}
                  className={`flex items-center justify-between p-2 rounded-lg border text-xs transition-colors ${
                    offer.is_eligible
                      ? 'bg-neutral-50 dark:bg-neutral-800/40 border-neutral-200/80 dark:border-neutral-700/80'
                      : 'bg-neutral-50/40 dark:bg-neutral-900/40 border-neutral-200/50 dark:border-neutral-800/60 text-neutral-400'
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    <span className="font-medium text-neutral-800 dark:text-neutral-200">
                      {offer.domain}
                    </span>
                    {offer.availability === 'InStock' ? (
                      <span className="text-[10px] text-emerald-600 dark:text-emerald-400 flex items-center gap-0.5">
                        <Check size={10} /> In Stock
                      </span>
                    ) : (
                      <span className="text-[10px] text-rose-500">Out of Stock</span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`font-semibold ${
                        offer.is_eligible
                          ? 'text-neutral-900 dark:text-white'
                          : 'text-neutral-400 line-through'
                      }`}
                    >
                      ${offer.price_amount}
                    </span>
                    {offer.is_eligible ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
                        Eligible
                      </span>
                    ) : (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 flex items-center gap-0.5">
                        <AlertTriangle size={9} /> Cap
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Card Footer Actions */}
      <div className="p-4 sm:p-5 pt-0 flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          className="flex-1"
          onClick={() => onCompare(product)}
        >
          Compare Offers
        </Button>

        {bestOffer && (
          <Button
            variant="primary"
            size="sm"
            className="flex-1"
            onClick={() => onSelectOffer(product, bestOffer)}
            icon={<ArrowRight size={13} />}
          >
            Review Proposal
          </Button>
        )}
      </div>
    </div>
  )
}
