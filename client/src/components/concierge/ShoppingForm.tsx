import React, { useState } from 'react'
import { Sparkles, SlidersHorizontal, ArrowRight, CornerDownLeft } from 'lucide-react'
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
    'Warm-light Nordic desk lamp with adjustable arm under $50',
    'Double-walled stainless steel French press coffee maker 34oz',
    'Ergonomic memory foam seat cushion for desk chair',
    'Noise-cancelling wireless over-ear headphones under $60',
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
    <div className="w-full rounded-[28px] p-6 md:p-8 bg-white dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800 shadow-[0_4px_24px_rgba(0,0,0,0.03)] flex flex-col gap-6">
      <div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#98EC6A] dark:bg-[#2CE5B5] inline-block animate-pulse" />
          <h2 className="text-xl md:text-2xl font-black text-neutral-900 dark:text-white tracking-tight">
            Tell Carti What You Need
          </h2>
        </div>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
          Natural language shopping assistant with automated mandate guardrails & retailer comparison
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {/* Main Prompt Input Box */}
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., Find me an aesthetic warm-light desk lamp under $50 with matte finish from Target..."
            rows={3}
            className="w-full rounded-2xl bg-neutral-50 dark:bg-[#1A1D23] text-neutral-900 dark:text-white placeholder-neutral-400 dark:placeholder-neutral-500 border border-neutral-200 dark:border-neutral-700/80 focus:border-neutral-400 dark:focus:border-neutral-500 focus:ring-2 focus:ring-neutral-200/50 p-4 text-sm resize-none outline-hidden"
            required
          />
          <div className="absolute right-3 bottom-3 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className={`p-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
                showAdvanced
                  ? 'bg-neutral-200 dark:bg-neutral-700 text-neutral-900 dark:text-white'
                  : 'text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 bg-white/70 dark:bg-neutral-800/70'
              }`}
              title="Toggle precise filters"
            >
              <SlidersHorizontal size={14} />
              <span className="hidden sm:inline">Preferences</span>
            </button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              loading={isLoading}
              icon={<Sparkles size={14} />}
            >
              <span>Search</span>
              <CornerDownLeft size={12} className="opacity-60" />
            </Button>
          </div>
        </div>

        {/* Example Quick Prompt Chips */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[11px] font-bold text-neutral-400 uppercase tracking-wider">
            Try:
          </span>
          {examplePrompts.map((eg, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setPrompt(eg)}
              className="text-xs px-3 py-1 rounded-full bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 border border-neutral-200/70 dark:border-neutral-700 transition-colors text-left"
            >
              {eg}
            </button>
          ))}
        </div>

        {/* Collapsible Advanced Preferences */}
        {showAdvanced && (
          <div className="p-4 rounded-2xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 animate-fade-in">
            <Input
              label="Category"
              placeholder="e.g. Lighting"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            />
            <Input
              label="Max Price ($)"
              type="number"
              placeholder="e.g. 50"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
            />
            <Input
              label="Brand Preference"
              placeholder="e.g. Lumina"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
            />
            <Input
              label="Preferred Retailer"
              placeholder="e.g. target.com"
              value={retailer}
              onChange={(e) => setRetailer(e.target.value)}
            />
          </div>
        )}
      </form>
    </div>
  )
}
