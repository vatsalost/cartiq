import React from 'react'
import { Check, ExternalLink, ArrowRight, Star } from 'lucide-react'
import { Button } from '../common/Button'
import { Badge } from '../common/Badge'

export interface ShoppingComparisonCardProps {
  id: string
  title: string
  retailer: string
  retailerUrl?: string
  price: string
  rating: number
  reviewsCount: number
  imageUrl: string
  isBestMatch?: boolean
  recommendationReasons: string[]
  onSelect: () => void
}

export const ShoppingComparisonCard: React.FC<ShoppingComparisonCardProps> = ({
  title,
  retailer,
  retailerUrl,
  price,
  rating,
  reviewsCount,
  imageUrl,
  isBestMatch = false,
  recommendationReasons,
  onSelect,
}) => {
  return (
    <div
      className={`rounded-xl overflow-hidden bg-white dark:bg-[#17191C] border transition-all flex flex-col justify-between shadow-[0_1px_3px_rgba(0,0,0,0.03)] ${
        isBestMatch
          ? 'border-[#95EB68] ring-1 ring-[#95EB68]/30 dark:border-[#95EB68]/60'
          : 'border-neutral-200/90 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700'
      }`}
    >
      <div>
        {/* Top Product Image */}
        <div className="relative w-full h-44 bg-neutral-100 dark:bg-neutral-800 overflow-hidden">
          <img
            src={imageUrl}
            alt={title}
            className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
          />

          {isBestMatch && (
            <div className="absolute top-3 left-3">
              <Badge variant="lime" size="xs">
                Best Match
              </Badge>
            </div>
          )}
        </div>

        {/* Product Details */}
        <div className="p-4 sm:p-5 flex flex-col gap-3">
          <div>
            <h4 className="text-[15px] font-semibold text-neutral-900 dark:text-white leading-snug line-clamp-1">
              {title}
            </h4>

            {/* Retailer & Price Row */}
            <div className="flex items-center justify-between mt-1.5">
              <div className="flex items-center gap-1 text-xs text-neutral-500 dark:text-neutral-400">
                <span className="font-medium text-neutral-700 dark:text-neutral-300">
                  {retailer}
                </span>
                {retailerUrl && (
                  <a
                    href={retailerUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="hover:text-neutral-900 dark:hover:text-white inline-flex items-center"
                    title={`Open on ${retailer}`}
                  >
                    <ExternalLink size={14} strokeWidth={1.8} />
                  </a>
                )}
              </div>

              <div className="text-lg font-bold text-neutral-900 dark:text-white tabular-nums">
                {price}
              </div>
            </div>

            {/* Rating */}
            <div className="flex items-center gap-1.5 mt-1 text-xs text-neutral-500 dark:text-neutral-400">
              <div className="flex items-center text-amber-500">
                <Star size={13} strokeWidth={1.8} className="fill-amber-400 text-amber-400" />
                <span className="font-semibold ml-1 text-neutral-800 dark:text-neutral-200 tabular-nums">
                  {rating.toFixed(1)}
                </span>
              </div>
              <span className="text-neutral-300 dark:text-neutral-600">•</span>
              <span className="text-[11px] text-neutral-400 tabular-nums">({reviewsCount} reviews)</span>
            </div>
          </div>

          {/* Why Recommended Checklist */}
          <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800/80">
            <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-2 block">
              Why recommended:
            </span>
            <ul className="space-y-1.5">
              {recommendationReasons.map((reason, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-2 text-[12px] text-neutral-600 dark:text-neutral-400 leading-tight"
                >
                  <Check
                    size={14}
                    strokeWidth={2}
                    className="text-[#1D4A18] dark:text-[#95EB68] shrink-0 mt-0.5"
                  />
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Button Action */}
      <div className="p-4 sm:p-5 pt-0">
        {isBestMatch ? (
          <Button
            variant="primary"
            size="sm"
            className="w-full justify-center"
            onClick={onSelect}
            icon={<ArrowRight size={16} strokeWidth={1.8} />}
          >
            <span>Select for Proposal</span>
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-center"
            onClick={onSelect}
          >
            <span>Select Alternative</span>
          </Button>
        )}
      </div>
    </div>
  )
}
