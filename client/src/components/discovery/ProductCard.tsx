import React from 'react'
import { Sparkles, ExternalLink, Check, AlertCircle } from 'lucide-react'
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
    <div className="rounded-[28px] overflow-hidden bg-white dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800 shadow-[0_4px_24px_rgba(0,0,0,0.03)] flex flex-col justify-between transition-all hover:border-neutral-300 dark:hover:border-neutral-700">
      <div>
        {/* Product Image & Ranking Header */}
        <div className="relative w-full h-48 bg-neutral-100 dark:bg-neutral-800 overflow-hidden">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.title}
              className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-neutral-400 text-xs">
              No Image Available
            </div>
          )}
          <div className="absolute top-3 left-3 flex items-center gap-1.5">
            <Badge variant="lime" size="sm">
              <Sparkles size={11} className="mr-1" />
              Score: {product.rank_score}
            </Badge>
          </div>
          {product.brand && (
            <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md text-white text-[11px] font-semibold">
              {product.brand}
            </div>
          )}
        </div>

        {/* Content Details */}
        <div className="p-5 flex flex-col gap-3">
          <div>
            <h4 className="text-base font-extrabold text-neutral-900 dark:text-white line-clamp-2 leading-snug">
              {product.title}
            </h4>
            <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              <span>Category: {product.category || 'General'}</span>
            </div>
          </div>

          {/* AI Ranking Explanation */}
          <div className="p-3 rounded-2xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/60 dark:border-neutral-800 text-xs text-neutral-600 dark:text-neutral-300 leading-relaxed">
            <span className="font-bold text-neutral-800 dark:text-neutral-100 mr-1">
              Agent Note:
            </span>
            {product.rank_reason}
          </div>

          {/* Retailer Offers Comparison Grid */}
          <div className="flex flex-col gap-1.5 mt-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-neutral-400">
              Verified Retailer Offers ({product.offers.length})
            </span>
            <div className="flex flex-col gap-1.5">
              {product.offers.map((offer) => (
                <div
                  key={offer.id}
                  className={`flex items-center justify-between p-2.5 px-3 rounded-xl border text-xs transition-colors ${
                    offer.is_eligible
                      ? 'bg-neutral-50/80 dark:bg-neutral-800/40 border-neutral-200 dark:border-neutral-700/80 hover:border-neutral-400'
                      : 'bg-rose-500/5 border-rose-500/20 text-neutral-400'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-neutral-800 dark:text-neutral-200">
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

                  <div className="flex items-center gap-3">
                    <span
                      className={`font-black ${
                        offer.is_eligible
                          ? 'text-neutral-900 dark:text-white'
                          : 'text-neutral-400 line-through'
                      }`}
                    >
                      ${offer.price_amount} {offer.currency}
                    </span>
                    {offer.ineligibility_reason && (
                      <span
                        className="text-[10px] text-rose-500 max-w-[120px] truncate"
                        title={offer.ineligibility_reason}
                      >
                        {offer.ineligibility_reason}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="p-5 pt-0 flex items-center justify-between gap-2 border-t border-neutral-100 dark:border-neutral-800 mt-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => onCompare(product)}
        >
          Compare Offers
        </Button>
        {bestOffer && (
          <Button
            type="button"
            variant="primary"
            size="sm"
            onClick={() => onSelectOffer(product, bestOffer)}
            disabled={!bestOffer.is_eligible}
          >
            Select Best Offer (${bestOffer.price_amount})
          </Button>
        )}
      </div>
    </div>
  )
}
