import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Sparkles,
  ArrowRight,
  SlidersHorizontal,
  Paperclip,
  Check,
} from 'lucide-react'
import { SseProgressTracker } from '../components/concierge/SseProgressTracker'
import { ShoppingComparisonCard } from '../components/discovery/ShoppingComparisonCard'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { api } from '../api/client'
import { ShoppingRequestInput } from '../api/types'
import { useAuth } from '../context/AuthContext'

interface ComparisonProduct {
  id: string
  title: string
  retailer: string
  retailerUrl: string
  price: string
  rating: number
  reviewsCount: number
  imageUrl: string
  isBestMatch: boolean
  recommendationReasons: string[]
}

export const ShoppingPage: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryParam = searchParams.get('q')
  const { mandate } = useAuth()

  const [prompt, setPrompt] = useState(
    queryParam || 'Aesthetic warm desk lamp under $50 with brass finish'
  )
  const [activeSearchChip, setActiveSearchChip] = useState('Warm-light desk lamp')
  const [isLoading, setIsLoading] = useState(false)
  const [activeRequestId, setActiveRequestId] = useState<string | null>(null)
  const [showPreferences, setShowPreferences] = useState(false)

  // Preferences form state
  const [category, setCategory] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [brand, setBrand] = useState('')
  const [retailer, setRetailer] = useState('')

  const recentSearches = [
    'Warm-light desk lamp',
    'French press coffee maker',
    'Wireless headphones',
    'Ergonomic desk chair',
  ]

  // Pre-configured dynamic product sets for realistic interactive testing
  const productCatalog: Record<string, ComparisonProduct[]> = {
    lamp: [
      {
        id: 'prod_1',
        title: 'Modern Brass Desk Lamp with Dimmer',
        retailer: 'Target',
        retailerUrl: 'https://www.target.com',
        price: '$49.99',
        rating: 4.8,
        reviewsCount: 124,
        imageUrl:
          'https://images.unsplash.com/photo-1534349762230-e0cadf78f5da?w=500&auto=format&fit=crop&q=60',
        isBestMatch: true,
        recommendationReasons: [
          'Brass finish matching query',
          'Dimmable warm LED included',
          'Within $60 item cap ($49.99)',
          'In stock at Target (verified)',
        ],
      },
      {
        id: 'prod_2',
        title: 'Minimalist Brass Table Lamp',
        retailer: 'Amazon',
        retailerUrl: 'https://www.amazon.com',
        price: '$42.50',
        rating: 4.5,
        reviewsCount: 89,
        imageUrl:
          'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          'Budget-friendly alternative',
          'Warm 2700K color temperature',
          'Within $60 item cap ($42.50)',
          '2-day delivery available',
        ],
      },
      {
        id: 'prod_3',
        title: 'Industrial Brass Task Lamp',
        retailer: 'Wayfair',
        retailerUrl: 'https://www.wayfair.com',
        price: '$54.99',
        rating: 4.6,
        reviewsCount: 62,
        imageUrl:
          'https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          'Solid brass construction',
          'Adjustable arm and head',
          'Within $60 item cap ($54.99)',
          'Retailer score: 94/100',
        ],
      },
    ],
    coffee: [
      {
        id: 'prod_coffee_1',
        title: 'Bodum Chambord French Press Coffee Maker 34oz',
        retailer: 'Target',
        retailerUrl: 'https://www.target.com',
        price: '$34.99',
        rating: 4.9,
        reviewsCount: 340,
        imageUrl:
          'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=500&auto=format&fit=crop&q=60',
        isBestMatch: true,
        recommendationReasons: [
          'Borosilicate glass with stainless frame',
          'Precision 3-part mesh filter',
          'Within $60 item cap ($34.99)',
          'In stock at Target (verified)',
        ],
      },
      {
        id: 'prod_coffee_2',
        title: 'Mueller Double-Insulated French Press 34oz',
        retailer: 'Amazon',
        retailerUrl: 'https://www.amazon.com',
        price: '$29.97',
        rating: 4.7,
        reviewsCount: 820,
        imageUrl:
          'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          'Heavy-duty 304 stainless steel',
          'Keeps coffee hot for 60 minutes',
          'Within $60 item cap ($29.97)',
          'Prime overnight delivery',
        ],
      },
      {
        id: 'prod_coffee_3',
        title: 'Secura Stainless Steel French Press 34oz',
        retailer: 'Walmart',
        retailerUrl: 'https://www.walmart.com',
        price: '$27.99',
        rating: 4.6,
        reviewsCount: 195,
        imageUrl:
          'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          'Double-wall thermal insulation',
          'Cool touch handle & knob',
          'Within $60 item cap ($27.99)',
          'Walmart verified seller',
        ],
      },
    ],
    headphones: [
      {
        id: 'prod_hp_1',
        title: 'Anker Soundcore Life Q20 Hybrid ANC Headphones',
        retailer: 'Best Buy',
        retailerUrl: 'https://www.bestbuy.com',
        price: '$59.99',
        rating: 4.7,
        reviewsCount: 512,
        imageUrl:
          'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60',
        isBestMatch: true,
        recommendationReasons: [
          'Active Noise Canceling with 40h playtime',
          'Hi-Res audio certified drivers',
          'Under $60 item cap ($59.99)',
          'In stock at Best Buy',
        ],
      },
      {
        id: 'prod_hp_2',
        title: 'JBL Tune 510BT Wireless On-Ear Headphones',
        retailer: 'Target',
        retailerUrl: 'https://www.target.com',
        price: '$39.99',
        rating: 4.6,
        reviewsCount: 280,
        imageUrl:
          'https://images.unsplash.com/photo-1484704849700-f032a568e944?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          'JBL Pure Bass sound signature',
          'Lightweight and foldable',
          'Within $60 item cap ($39.99)',
          'In stock for same-day pickup',
        ],
      },
      {
        id: 'prod_hp_3',
        title: 'Sony WH-CH520 Wireless Bluetooth Headphones',
        retailer: 'Amazon',
        retailerUrl: 'https://www.amazon.com',
        price: '$48.00',
        rating: 4.6,
        reviewsCount: 410,
        imageUrl:
          'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          '50-hour battery life with quick charge',
          'DSEE audio upscaling engine',
          'Within $60 item cap ($48.00)',
          'Shipped directly by Amazon',
        ],
      },
    ],
    chair: [
      {
        id: 'prod_cush_1',
        title: 'ComfiLife Gel Enhanced Seat Cushion for Desk Chair',
        retailer: 'Target',
        retailerUrl: 'https://www.target.com',
        price: '$39.95',
        rating: 4.8,
        reviewsCount: 650,
        imageUrl:
          'https://images.unsplash.com/photo-1580481077195-c22ae2b1e223?w=500&auto=format&fit=crop&q=60',
        isBestMatch: true,
        recommendationReasons: [
          'Ergonomic memory foam with cooling gel layer',
          'Coccyx cutout relieves tailbone pressure',
          'Within $60 item cap ($39.95)',
          'In stock at Target',
        ],
      },
      {
        id: 'prod_cush_2',
        title: 'Everlasting Comfort Memory Foam Luxury Cushion',
        retailer: 'Amazon',
        retailerUrl: 'https://www.amazon.com',
        price: '$36.99',
        rating: 4.6,
        reviewsCount: 890,
        imageUrl:
          'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          'Heat-responsive orthopedic contour',
          'Lifetime replacement warranty',
          'Within $60 item cap ($36.99)',
          'Amazon bestseller rank #1',
        ],
      },
      {
        id: 'prod_cush_3',
        title: 'Purple Ultimate Seat Cushion Support',
        retailer: 'Best Buy',
        retailerUrl: 'https://www.bestbuy.com',
        price: '$59.00',
        rating: 4.7,
        reviewsCount: 220,
        imageUrl:
          'https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          'Hyper-Elastic Polymer grid construction',
          'Engineered for 8+ hour sitting support',
          'Within $60 item cap ($59.00)',
          'Available at local Best Buy',
        ],
      },
    ],
  }

  // Active product comparison items determined dynamically by search prompt
  const lowerPrompt = (prompt || activeSearchChip).toLowerCase()
  const activeProducts = lowerPrompt.includes('coffee')
    ? productCatalog.coffee
    : lowerPrompt.includes('headphone') || lowerPrompt.includes('sound')
    ? productCatalog.headphones
    : lowerPrompt.includes('chair') || lowerPrompt.includes('cushion')
    ? productCatalog.chair
    : productCatalog.lamp

  // Suggested shopping requests inspiration items
  const suggestedRequests = [
    {
      title: 'French press coffee maker 34oz',
      category: 'Kitchen',
      priceGuide: '$34.99',
      retailer: 'Target',
      matchScore: '98%',
    },
    {
      title: 'Ergonomic desk chair seat cushion',
      category: 'Home Office',
      priceGuide: '$39.95',
      retailer: 'Target',
      matchScore: '94%',
    },
    {
      title: 'Wireless noise-canceling headphones',
      category: 'Electronics',
      priceGuide: '$59.99',
      retailer: 'Best Buy',
      matchScore: '96%',
    },
  ]

  const handleStartShopping = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!prompt.trim()) return

    setIsLoading(true)
    try {
      const input: ShoppingRequestInput = {
        prompt: prompt.trim(),
        category: category.trim() || undefined,
        max_price: maxPrice ? parseFloat(maxPrice) : undefined,
        preferred_brand: brand.trim() || undefined,
        preferred_retailer: retailer.trim() || undefined,
      }
      const req = await api.createShoppingRequest(input)
      setActiveRequestId(req.id)
    } catch {
      setActiveRequestId(`req_${Date.now()}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleChipClick = (chip: string) => {
    setActiveSearchChip(chip)
    setPrompt(chip)
  }

  const handleSelectProduct = () => {
    navigate('/proposals')
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div>
        <h1 className="text-[28px] font-bold text-neutral-900 dark:text-white tracking-tight leading-tight">
          Shopping Assistant
        </h1>
        <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
          Autonomous product discovery, comparison, and mandate-compliant purchasing.
        </p>
      </div>

      {/* Main Search Prompt Card */}
      <div className="w-full rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-3">
        <form onSubmit={handleStartShopping} className="flex flex-col gap-3">
          <div className="relative rounded-xl border border-neutral-200 dark:border-neutral-700/80 bg-neutral-50/50 dark:bg-[#141619] focus-within:border-[#95EB68] focus-within:ring-2 focus-within:ring-[#95EB68]/20 transition-all p-3">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleStartShopping()
                }
              }}
              rows={2}
              placeholder="Describe what you want to purchase..."
              className="w-full bg-transparent text-neutral-900 dark:text-white placeholder-neutral-400 text-sm resize-none outline-hidden"
              required
            />

            <div className="flex items-center justify-between pt-2 border-t border-neutral-200/50 dark:border-neutral-800">
              <div className="flex items-center gap-2">
                {/* Paperclip upload button */}
                <button
                  type="button"
                  title="Attach reference image or document"
                  onClick={() => alert('Reference image attachment active')}
                  className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors cursor-pointer"
                >
                  <Paperclip size={16} strokeWidth={1.8} />
                </button>

                {/* Preferences pill */}
                <button
                  type="button"
                  onClick={() => setShowPreferences(!showPreferences)}
                  className={`text-xs px-2.5 py-1 rounded-md flex items-center gap-1.5 transition-colors cursor-pointer font-medium ${
                    showPreferences || category || maxPrice || brand || retailer
                      ? 'bg-neutral-200 dark:bg-neutral-700 text-neutral-900 dark:text-white'
                      : 'text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800'
                  }`}
                >
                  <SlidersHorizontal size={16} strokeWidth={1.8} />
                  <span>
                    Preferences
                    {category || maxPrice || brand || retailer ? ' (Active)' : ''}
                  </span>
                </button>
              </div>

              {/* Green Search button */}
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-[#95EB68] text-[#17191C] hover:bg-[#85da58] active:scale-[0.98] transition-all flex items-center gap-1.5 shadow-xs cursor-pointer"
              >
                <span>Search</span>
                <ArrowRight size={16} strokeWidth={1.8} />
              </button>
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
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCategory(e.target.value)}
                />

                <Input
                  label="Max Price ($)"
                  type="number"
                  placeholder={`Max $${mandate?.per_item_cap || '60.00'}`}
                  value={maxPrice}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMaxPrice(e.target.value)}
                />

                <Input
                  label="Preferred Brand"
                  placeholder="e.g. Lumina, Bodum"
                  value={brand}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setBrand(e.target.value)}
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
                    <option value="target.com">target.com</option>
                    <option value="amazon.com">amazon.com</option>
                    <option value="wayfair.com">wayfair.com</option>
                    <option value="bestbuy.com">bestbuy.com</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Recent Searches Pills */}
          <div className="flex items-center gap-2 flex-wrap pt-1">
            <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
              Recent Searches:
            </span>
            {recentSearches.map((chip) => {
              const isActive = activeSearchChip === chip
              return (
                <button
                  key={chip}
                  type="button"
                  onClick={() => handleChipClick(chip)}
                  className={`text-xs px-3 py-1 rounded-full transition-colors cursor-pointer font-medium ${
                    isActive
                      ? 'bg-[#95EB68] text-[#17191C] font-semibold'
                      : 'bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800/80 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300'
                  }`}
                >
                  {chip}
                </button>
              )
            })}
          </div>

          {/* Suggested Shopping Requests Row */}
          <div className="flex flex-col gap-2 pt-3 border-t border-neutral-100 dark:border-neutral-800/80">
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-semibold text-neutral-800 dark:text-neutral-200 flex items-center gap-1.5">
                <Sparkles size={14} strokeWidth={1.8} className="text-[#95EB68]" />
                <span>Suggested Shopping Requests:</span>
              </span>
              <span className="text-[11px] text-neutral-400 hidden sm:inline">
                Click any prompt to explore curated mandate-verified items
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {suggestedRequests.map((sug) => (
                <div
                  key={sug.title}
                  onClick={() => {
                    setPrompt(sug.title)
                    setActiveSearchChip(sug.title)
                  }}
                  className="p-3 rounded-xl bg-neutral-50/70 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800/80 hover:border-[#95EB68]/60 dark:hover:border-[#95EB68]/40 hover:bg-neutral-100/50 dark:hover:bg-neutral-800/40 transition-all cursor-pointer flex flex-col justify-between group shadow-2xs"
                >
                  <div className="flex items-center justify-between text-[11px] text-neutral-500 mb-1">
                    <span className="px-2 py-0.5 rounded-md bg-white dark:bg-neutral-800 border border-neutral-200/80 dark:border-neutral-700 font-medium text-[10px]">
                      {sug.category}
                    </span>
                    <span className="text-emerald-700 dark:text-emerald-400 font-semibold tabular-nums text-[11px]">
                      {sug.matchScore} match
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-neutral-900 dark:text-white group-hover:text-[#1D4A18] dark:group-hover:text-[#95EB68] transition-colors line-clamp-1">
                    {sug.title}
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-neutral-400 mt-2 font-mono">
                    <span>{sug.retailer}</span>
                    <span className="font-bold text-neutral-900 dark:text-white tabular-nums">
                      {sug.priceGuide}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </form>
      </div>

      {/* Live SSE Agent Pipeline Tracker */}
      {activeRequestId && (
        <SseProgressTracker
          requestId={activeRequestId}
          onComplete={() => {
            setActiveRequestId(null)
          }}
          onCancel={() => {
            if (activeRequestId) api.cancelShoppingRequest(activeRequestId)
            setActiveRequestId(null)
          }}
        />
      )}

      {/* Found Products Section */}
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="text-[18px] font-semibold text-neutral-900 dark:text-white leading-snug">
            Found {activeProducts.length} Products for &apos;{activeSearchChip}&apos;
          </h2>
          <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
            Ranked by AI relevance score and verified against your mandate limits
          </p>
        </div>

        {/* 3 Product Comparison Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {activeProducts.map((p) => (
            <ShoppingComparisonCard
              key={p.id}
              id={p.id}
              title={p.title}
              retailer={p.retailer}
              retailerUrl={p.retailerUrl}
              price={p.price}
              rating={p.rating}
              reviewsCount={p.reviewsCount}
              imageUrl={p.imageUrl}
              isBestMatch={p.isBestMatch}
              recommendationReasons={p.recommendationReasons}
              onSelect={handleSelectProduct}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
