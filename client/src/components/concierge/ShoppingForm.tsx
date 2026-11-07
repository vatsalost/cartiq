import React, { useState } from 'react'
import { SlidersHorizontal, CornerDownLeft, Sparkles, X, ShieldCheck } from 'lucide-react'
import { Button } from '../common/Button'
import { Input } from '../common/Input'
import { ShoppingRequestInput } from '../../api/types'
import { useAuth } from '../../context/AuthContext'

interface ShoppingFormProps {
  onSubmit: (input: ShoppingRequestInput) => void
  isLoading: boolean
  initialPrompt?: string
}

export const ShoppingForm: React.FC<ShoppingFormProps> = ({
  onSubmit,
  isLoading,
  initialPrompt = '',
}) => {
  const { mandate, breakdown } = useAuth()
  const [prompt, setPrompt] = useState(initialPrompt)
  const [showPreferences, setShowPreferences] = useState(false)
  const [category, setCategory] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [brand, setBrand] = useState('')
  const [retailer, setRetailer] = useState('')

  const examplePrompts = [
    'Aesthetic warm desk lamp under $50',
    'French press coffee maker 34oz',
    'Ergonomic memory foam cushion',
    'Wireless noise-canceling headphones',
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
    <div className="w-full rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-4">
      {/* Header with Mandate Context */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-neutral-100 dark:border-neutral-800">
        <div>
          <h2 className="text-[18px] font-semibold text-neutral-900 dark:text-white flex items-center gap-2">
            <Sparkles size={18} strokeWidth={1.8} className="text-[#95EB68]" />
            <span>Autonomous AI Shopping Assistant</span>
          </h2>
          <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
            Describe the product you want. Carti handles search, retailer stock checks, and guardrails.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400 self-start sm:self-auto bg-neutral-50 dark:bg-neutral-800/60 px-2.5 py-1 rounded-md border border-neutral-200/60 dark:border-neutral-700/60 font-mono tabular-nums">
          <ShieldCheck size={14} strokeWidth={1.8} className="text-[#95EB68]" />
          <span>Cap: ${mandate?.per_item_cap || '60.00'}/item</span>
          <span>•</span>
          <span>Avail: ${breakdown?.available_budget || '65.02'}</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        {/* Main Prompt Input Box */}
        <div className="relative rounded-xl border border-neutral-200 dark:border-neutral-700/90 bg-neutral-50/50 dark:bg-[#141619] focus-within:border-[#95EB68] dark:focus-within:border-[#95EB68] focus-within:ring-2 focus-within:ring-[#95EB68]/20 transition-all p-3">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
            placeholder="e.g. Find me an aesthetic warm-light desk lamp under $50 with adjustable brightness..."
            rows={2}
            className="w-full bg-transparent text-neutral-900 dark:text-white placeholder-neutral-400 text-sm resize-none outline-hidden"
            required
          />

          <div className="flex items-center justify-between pt-2 border-t border-neutral-200/50 dark:border-neutral-800">
            <button
              type="button"
              onClick={() => setShowPreferences(!showPreferences)}
              className={`text-xs px-2.5 py-1 rounded-md flex items-center gap-1.5 transition-colors cursor-pointer font-medium ${
                showPreferences || category || maxPrice || brand || retailer
                  ? 'bg-neutral-200 dark:bg-neutral-700 text-neutral-900 dark:text-white'
                  : 'text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800'
              }`}
            >
              <SlidersHorizontal size={14} strokeWidth={1.8} />
              <span>
                Preferences
                {category || maxPrice || brand || retailer ? ' (Active)' : ''}
              </span>
            </button>

            <div className="flex items-center gap-2">
              <span className="text-[11px] text-neutral-400 hidden sm:inline">
                Press <kbd className="font-mono bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded px-1 py-0.2">↵</kbd> to search
              </span>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                loading={isLoading}
                icon={<Sparkles size={16} strokeWidth={1.8} />}
              >
                <span>Search</span>
              </Button>
            </div>
          </div>
        </div>

        {/* Expandable Preferences Drawer */}
        {showPreferences && (
          <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 animate-in fade-in slide-in-from-top-2 duration-150">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-neutral-200/60 dark:border-neutral-800">
              <span className="text-xs font-semibold text-neutral-800 dark:text-neutral-200">
                Purchasing Preferences & Constraints
              </span>
              <button
                type="button"
                onClick={() => {
                  setCategory('')
                  setMaxPrice('')
                  setBrand('')
                  setRetailer('')
                }}
                className="text-[11px] text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200"
              >
                Reset filters
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <Input
                label="Target Category"
                placeholder="e.g. Lighting, Kitchen"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              />

              <Input
                label="Max Price ($)"
                type="number"
                placeholder={`Max $${mandate?.per_item_cap || '60.00'}`}
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
              />

              <Input
                label="Preferred Brand"
                placeholder="e.g. Lumina, Bodum"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
              />

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-neutral-700 dark:text-neutral-300">
                  Preferred Retailer
                </label>
                <select
                  value={retailer}
                  onChange={(e) => setRetailer(e.target.value)}
                  className="w-full rounded-lg bg-white dark:bg-[#1C1F24] text-neutral-900 dark:text-neutral-100 border border-neutral-200 dark:border-neutral-700/80 text-xs py-2 px-3 outline-hidden"
                >
                  <option value="">Any Approved Retailer</option>
                  {mandate?.allowed_retailers?.map((ret) => (
                    <option key={ret} value={ret}>
                      {ret}
                    </option>
                  )) || (
                    <>
                      <option value="target.com">target.com</option>
                      <option value="bestbuy.com">bestbuy.com</option>
                      <option value="walmart.com">walmart.com</option>
                      <option value="amazon.com">amazon.com</option>
                    </>
                  )}
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Recent Search Suggestions */}
        <div className="flex items-center gap-1.5 flex-wrap pt-1">
          <span className="text-[11px] font-medium text-neutral-400">Suggestions:</span>
          {examplePrompts.map((eg, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setPrompt(eg)}
              className="text-xs px-2.5 py-1 rounded-md bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800/80 dark:hover:bg-neutral-700 text-neutral-600 dark:text-neutral-300 transition-colors cursor-pointer"
            >
              {eg}
            </button>
          ))}
        </div>
      </form>
    </div>
  )
}
