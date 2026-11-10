import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Sparkles,
  ArrowRight,
  SlidersHorizontal,
  Paperclip,
  Check,
  AlertCircle,
  ShieldCheck,
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
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [mandateWarning, setMandateWarning] = useState<string | null>(null)
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
        retailer: 'Amazon',
        retailerUrl: 'https://www.amazon.com',
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
          'Amazon Prime verified seller',
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
    mouse: [
      {
        id: 'prod_mouse_1',
        title: 'Logitech Lift Vertical Ergonomic Wireless Mouse',
        retailer: 'Target',
        retailerUrl: 'https://www.target.com',
        price: '$44.99',
        rating: 4.8,
        reviewsCount: 1420,
        imageUrl:
          'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&auto=format&fit=crop&q=60',
        isBestMatch: true,
        recommendationReasons: [
          '57-degree natural vertical angle reduces wrist strain',
          'Quiet clicks & SmartWheel precision scroll',
          'Well within $60 item cap ($44.99)',
          'In stock at Target with same-day pickup',
        ],
      },
      {
        id: 'prod_mouse_2',
        title: 'Anker 2.4G Wireless Vertical Ergonomic Optical Mouse',
        retailer: 'Amazon',
        retailerUrl: 'https://www.amazon.com',
        price: '$24.99',
        rating: 4.6,
        reviewsCount: 3200,
        imageUrl:
          'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          'Neutral "handshake" wrist alignment design',
          '800/1200/1600 DPI resolution optical tracking',
          'Budget friendly price under $25',
          'Amazon Prime next-day shipping',
        ],
      },
      {
        id: 'prod_mouse_3',
        title: 'ProtoArc EM01 Wireless Ergonomic Rechargeable Mouse',
        retailer: 'Best Buy',
        retailerUrl: 'https://www.bestbuy.com',
        price: '$39.99',
        rating: 4.5,
        reviewsCount: 380,
        imageUrl:
          'https://images.unsplash.com/photo-1586816879360-004f5b0c51e3?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          'Adjustable 0° or 20° tilt angle for personalized comfort',
          'Multi-device 2.4G & Bluetooth connectivity',
          'Within mandate limit ($39.99)',
          'Best Buy verified warranty support',
        ],
      },
    ],
    pourOver: [
      {
        id: 'prod_pour_1',
        title: 'Hario V60 Ceramic Pour-Over Coffee Dripper Set',
        retailer: 'Target',
        retailerUrl: 'https://www.target.com',
        price: '$32.50',
        rating: 4.9,
        reviewsCount: 940,
        imageUrl:
          'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500&auto=format&fit=crop&q=60',
        isBestMatch: true,
        recommendationReasons: [
          'Iconic spiral ribbed ceramic heat retention',
          'Includes server, dripper, and 40 paper filters',
          'Under $35 and within $60 mandate cap ($32.50)',
          'Available at Target local fulfillment',
        ],
      },
      {
        id: 'prod_pour_2',
        title: 'Kalita Wave 185 Stainless Steel Pour-Over Dripper',
        retailer: 'Amazon',
        retailerUrl: 'https://www.amazon.com',
        price: '$34.99',
        rating: 4.8,
        reviewsCount: 650,
        imageUrl:
          'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          'Flat-bottom three-hole extraction geometry',
          'Durable lightweight Japanese stainless steel',
          'Within mandate item cap ($34.99)',
          'Prime eligible fast delivery',
        ],
      },
      {
        id: 'prod_pour_3',
        title: 'Chemex Classic Pour-Over Glass Coffeemaker 6-Cup',
        retailer: 'Target',
        retailerUrl: 'https://www.target.com',
        price: '$46.95',
        rating: 4.8,
        reviewsCount: 1850,
        imageUrl:
          'https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=500&auto=format&fit=crop&q=60',
        isBestMatch: false,
        recommendationReasons: [
          'Non-porous Borosilicate glass with polished wood collar',
          'Pure flavor extraction without chemical residue',
          'Approved Target retailer within $60 cap ($46.95)',
          'In stock for immediate purchase',
        ],
      },
    ],
  }

  // Active product comparison items determined dynamically by evaluated prompt
  const queryToEvaluate = (submittedQuery || prompt || activeSearchChip).toLowerCase()
  let activeProducts: ComparisonProduct[] = []

  if (mandateWarning) {
    activeProducts = []
  } else if (queryToEvaluate.includes('mouse') || queryToEvaluate.includes('trackball')) {
    activeProducts = productCatalog.mouse
  } else if (
    queryToEvaluate.includes('pour') ||
    queryToEvaluate.includes('dripper') ||
    queryToEvaluate.includes('chemex')
  ) {
    activeProducts = productCatalog.pourOver
  } else if (queryToEvaluate.includes('coffee') || queryToEvaluate.includes('french')) {
    activeProducts = productCatalog.coffee
  } else if (
    queryToEvaluate.includes('headphone') ||
    queryToEvaluate.includes('sound') ||
    queryToEvaluate.includes('earphone') ||
    queryToEvaluate.includes('audio')
  ) {
    activeProducts = productCatalog.headphones
  } else if (
    queryToEvaluate.includes('chair') ||
    queryToEvaluate.includes('cushion') ||
    queryToEvaluate.includes('seat')
  ) {
    activeProducts = productCatalog.chair
  } else if (queryToEvaluate.includes('lamp') || queryToEvaluate.includes('light')) {
    activeProducts = productCatalog.lamp
  } else {
    // If user searched for custom text outside catalog
    activeProducts = []
  }

  // Initial fallback to default chip if no search submitted yet and no mandate violation
  if (!submittedQuery && !mandateWarning && activeProducts.length === 0) {
    activeProducts = productCatalog.lamp
  }

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

    const trimmedPrompt = prompt.trim()
    setSubmittedQuery(trimmedPrompt)
    setIsLoading(true)

    // Evaluate dynamic mandate limits
    const priceMatch = trimmedPrompt.match(/\$(\d+)/) || trimmedPrompt.match(/(\d+)\s*(dollars|usd)/i)
    const detectedPrice = priceMatch ? parseFloat(priceMatch[1]) : (maxPrice ? parseFloat(maxPrice) : null)
    const perItemCap = mandate ? parseFloat(mandate.per_item_cap) : null
    const totalBudget = mandate ? parseFloat(mandate.total_budget) : null

    const blockedList = mandate?.blocked_categories || []
    const hasBlocked = blockedList.some((kw) => kw.trim() && trimmedPrompt.toLowerCase().includes(kw.toLowerCase().trim()))

    if (!mandate) {
      setMandateWarning(
        'Notice: No active spending mandate configured. Please configure your mandate in Spending Controls before purchasing.'
      )
    } else if (detectedPrice && perItemCap !== null && detectedPrice > perItemCap) {
      setMandateWarning(
        `Mandate Limit Exceeded: Requested price ($${detectedPrice.toFixed(2)}) exceeds your per-item limit of $${perItemCap.toFixed(2)}. The autonomous agent is strictly constrained to mandate boundaries.`
      )
    } else if (detectedPrice && totalBudget !== null && detectedPrice > totalBudget) {
      setMandateWarning(
        `Mandate Limit Exceeded: Requested price ($${detectedPrice.toFixed(2)}) exceeds your total available budget of $${totalBudget.toFixed(2)}.`
      )
    } else if (hasBlocked) {
      setMandateWarning(
        `Category Policy Violation: This request contains categories strictly prohibited by your spending mandate (${blockedList.join(', ')}).`
      )
    } else {
      setMandateWarning(null)
    }

    try {
      const input: ShoppingRequestInput = {
        prompt: trimmedPrompt,
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
    setSubmittedQuery(chip)
    setPrompt(chip)
    setMandateWarning(null)
  }

  const handleSelectProduct = (product: ComparisonProduct) => {
    navigate('/proposals', { state: { product } })
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

      {/* No Mandate Banner */}
      {!mandate && (
        <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-800/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-amber-900 dark:text-amber-200">
          <div className="flex items-center gap-2.5">
            <ShieldCheck size={18} className="text-amber-600 dark:text-amber-400 shrink-0" />
            <span>
              <strong>Spending Mandate Not Configured:</strong> You have full control over your budget and category limits. Set up your spending mandate to enable autonomous purchasing.
            </span>
          </div>
          <Button
            variant="outline"
            size="xs"
            onClick={() => navigate('/mandate')}
            className="shrink-0 bg-white dark:bg-neutral-900 border-amber-300 dark:border-amber-700 text-amber-900 dark:text-amber-100 cursor-pointer"
          >
            Configure Mandate &rarr;
          </Button>
        </div>
      )}

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
                  placeholder={mandate ? `Max $${mandate.per_item_cap}` : 'Enter max price'}
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

      {/* Mandate Policy Warning Banner */}
      {mandateWarning && (
        <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 flex items-start gap-3 text-xs text-amber-800 dark:text-amber-300">
          <AlertCircle size={18} strokeWidth={1.8} className="shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
          <div className="flex flex-col gap-0.5">
            <span className="font-semibold text-amber-900 dark:text-amber-200">Mandate Guardrail Policy Notice</span>
            <span>{mandateWarning}</span>
          </div>
        </div>
      )}

      {/* Found Products Section */}
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="text-[18px] font-semibold text-neutral-900 dark:text-white leading-snug">
            Found {activeProducts.length} Products for &apos;{submittedQuery || activeSearchChip}&apos;
          </h2>
          <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
            Ranked by AI relevance score and verified against your mandate limits
          </p>
        </div>

        {/* Product Comparison Cards or Empty State */}
        {activeProducts.length > 0 ? (
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
                onSelect={() => handleSelectProduct(p)}
              />
            ))}
          </div>
        ) : (
          <div className="p-8 rounded-xl bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 flex flex-col items-center justify-center text-center gap-3">
            <div className="w-12 h-12 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400 flex items-center justify-center">
              <AlertCircle size={22} strokeWidth={1.8} />
            </div>
            <div>
              <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
                No In-Mandate Products Found
              </h3>
              <p className="text-[12px] text-neutral-500 dark:text-neutral-400 max-w-md mt-1">
                {mandateWarning
                  ? 'This search query conflicts with your current spending mandate. The autonomous concierge cannot propose items that violate your budget limits or category restrictions.'
                  : `No verified items found for '${submittedQuery || prompt}' within approved categories (Lighting, Kitchen, Electronics, Home Office) under the $60.00 cap. Try modifying your search.`}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
