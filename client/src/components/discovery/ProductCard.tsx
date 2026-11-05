import React from 'react'
import { Check, AlertCircle } from 'lucide-react'
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

  return (
    <div className="rounded-2xl overflow-hidden bg-white dark:bg-[#16181D] border border-neutral-200 dark:border-neutral-800 shadow-xs flex flex-col justify-between transition-colors">
      <div>
        {/* Product Image & Ranking Header */}
        <div className="relative w-full h-44 bg-neutral-100 dark:bg-neutral-800 overflow-hidden">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-neutral-400 text-xs">
              No Image Available
            </div>
          )}
          <div className="absolute top-2.5 left-2.5">
            <Badge variant="lime" size="sm">
              Match: {Math.round(parseFloat(product.rank_score) * 100)}%
            </Badge>
          </div>
          {product.brand && (
            <div className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-xs text-white text-[11px] font-medium">
              {product.brand}
            </div>
          )}
        </div>

        {/* Content Details */}
        <div className="p-4 sm:p-5 flex flex-col gap-3">
          <div>
            <h4 className="text-sm font-bold text-neutral-900 dark:text-white line-clamp-2 leading-snug">
              {product.title}
            </h4>
            <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              Category: {product.category || 'General'}
            </div>
          </div>

          {/* Ranking Explanation */}
          <div className="p-2.5 rounded-xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800 text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
            {product.rank_reason}
          </div>

          {/* Retailer Offers */}
          <div className="flex flex-col gap-1 mt-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400">
              Retailer Offers ({product.offers.length})
            </span>
            <div className="flex flex-col gap-1.5">
              {product.offers.map((offer) => (
                <div
                  key={offer.id}
                  className={`flex items-center justify-between p-2 px-2.5 rounded-lg border text-xs transition-colors ${
                    offer.is_eligible
                      ? 'bg-neutral-50 dark:bg-neutral-800/40 border-neutral-200 dark:border-neutral-700/80'
                      : 'bg-neutral-100/60 dark:bg-neutral-900/40 border-neutral-200 dark:border-neutral-800 text-neutral-400'
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
                      className={`font-bold ${
                        offer.is_eligible
                          ? 'text-neutral-900 dark:text-white'
                          : 'text-neutral-400 line-through'
                      }`}
                    >
                      ${offer.price_amount}
                    </span>
                    {!offer.is_eligible && (
                      <span title={offer.ineligibility_reason || 'Disallowed'}>
                        <AlertCircle size={12} className="text-amber-500" />
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Card Action Footer */}
      <div className="p-4 pt-0 sm:p-5 sm:pt-0 flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          className="w-1/2"
          onClick={() => onCompare(product)}
        >
          Compare
        </Button>
        <Button
          variant="primary"
          size="sm"
          className="w-1/2"
          onClick={() => onSelectOffer(product, bestOffer)}
        >
          Select Offer
        </Button>
      </div>
    </div>
  )
}
