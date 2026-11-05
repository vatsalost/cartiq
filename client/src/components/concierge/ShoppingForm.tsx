import React, { useState } from 'react'
import { SlidersHorizontal, CornerDownLeft, Search } from 'lucide-react'
import { Button } from '../common/Button'
import { Input } from '../common/Input'
import { ShoppingRequestInput } from '../../api/types'

interface ShoppingFormProps {
  onSubmit: (input: ShoppingRequestInput) => void
  isLoading: boolean
}

export const ShoppingForm: React.FC<ShoppingFormProps> = ({ onSubmit, isLoading }) => {
  const [prompt, setPrompt] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [category, setCategory] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [brand, setBrand] = useState('')
  const [retailer, setRetailer] = useState('')

  const examplePrompts = [
    'Warm-light desk lamp under $50',
    'French press coffee maker 34oz',
    'Ergonomic memory foam seat cushion',
    'Wireless over-ear headphones under $60',
  ]

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim()) return

    onSubmit({
      prompt: prompt.trim(),
      category: category.trim() || undefined,
      max_price: maxPrice ? parseFloat(maxPrice) : undefined,
      preferred_brand: brand.trim() || undefined,
      preferred_retailer: retailer.trim() || undefined,
    })
  }

  return (
    <div className="w-full rounded-2xl p-5 sm:p-6 bg-white dark:bg-[#16181D] border border-neutral-200 dark:border-neutral-800 shadow-xs flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-bold text-neutral-900 dark:text-white tracking-tight">
          Product Search
        </h2>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
          Describe the product you want to find within your active mandate limits
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        {/* Main Prompt Input Box */}
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., Find me an aesthetic warm-light desk lamp under $50 from Target..."
            rows={3}
            className="w-full rounded-xl bg-neutral-50 dark:bg-[#1A1D23] text-neutral-900 dark:text-white placeholder-neutral-400 dark:placeholder-neutral-500 border border-neutral-200 dark:border-neutral-700/80 focus:border-neutral-400 dark:focus:border-neutral-500 focus:ring-2 focus:ring-neutral-200/50 p-3.5 text-sm resize-none outline-hidden"
            required
          />
          <div className="absolute right-3 bottom-3 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
                showAdvanced
                  ? 'bg-neutral-200 dark:bg-neutral-700 text-neutral-900 dark:text-white'
                  : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white bg-white/80 dark:bg-neutral-800/80'
              }`}
            >
              <SlidersHorizontal size={13} />
              <span>Filters</span>
            </button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              loading={isLoading}
              icon={<Search size={13} />}
            >
              <span>Search</span>
            </Button>
          </div>
        </div>

        {/* Compact Example Quick Suggestions */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] font-medium text-neutral-400">Suggestions:</span>
          {examplePrompts.map((eg, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setPrompt(eg)}
              className="text-xs px-2.5 py-1 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors cursor-pointer"
            >
              {eg}
            </button>
          ))}
        </div>

        {/* Optional Structured Filter Drawer */}
        {showAdvanced && (
          <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200 dark:border-neutral-700/80 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 mt-1">
            <Input
              label="Category"
              placeholder="e.g., Lighting"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            />
            <Input
              label="Max Price ($)"
              type="number"
              placeholder="e.g., 50.00"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
            />
            <Input
              label="Preferred Brand"
              placeholder="e.g., Lumina"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
            />
            <Input
              label="Preferred Retailer"
              placeholder="e.g., target.com"
              value={retailer}
              onChange={(e) => setRetailer(e.target.value)}
            />
          </div>
        )}
      </form>
    </div>
  )
}
