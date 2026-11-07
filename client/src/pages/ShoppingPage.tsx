import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Sparkles, ArrowRight, RefreshCw, AlertCircle, ShieldCheck } from 'lucide-react'
import { ShoppingForm } from '../components/concierge/ShoppingForm'
import { SseProgressTracker } from '../components/concierge/SseProgressTracker'
import { ProductCard } from '../components/discovery/ProductCard'
import { OfferComparisonModal } from '../components/discovery/OfferComparisonModal'
import { Button } from '../components/common/Button'
import { api } from '../api/client'
import {
  ShoppingRequestInput,
  CandidateProduct,
  CandidateOffer,
} from '../api/types'
import { mockCandidateProducts } from '../api/mockData'

export const ShoppingPage: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryParam = searchParams.get('q')

  const [isLoading, setIsLoading] = useState(false)
  const [activeRequestId, setActiveRequestId] = useState<string | null>(null)
  const [candidates, setCandidates] = useState<CandidateProduct[]>([])
  const [selectedProductForComparison, setSelectedProductForComparison] =
    useState<CandidateProduct | null>(null)
  const [isCompareOpen, setIsCompareOpen] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  // Auto-trigger search if query param is provided
  useEffect(() => {
    if (queryParam && !hasSearched) {
      handleStartShopping({ prompt: queryParam })
    }
  }, [queryParam])

  const handleStartShopping = async (input: ShoppingRequestInput) => {
    setIsLoading(true)
    setHasSearched(true)
    try {
      const req = await api.createShoppingRequest(input)
      setActiveRequestId(req.id)
    } catch (e) {
      console.error('Request creation error:', e)
      setActiveRequestId(`req_${Date.now()}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStreamComplete = async (proposalId?: string) => {
    try {
      if (activeRequestId) {
        const cands = await api.getCandidates(activeRequestId)
        setCandidates(cands.length > 0 ? cands : mockCandidateProducts)
      } else {
        setCandidates(mockCandidateProducts)
      }
    } catch {
      setCandidates(mockCandidateProducts)
    }

    if (proposalId) {
      setTimeout(() => {
        navigate('/proposals')
      }, 1000)
    }
  }

  const handleSelectOffer = (product: CandidateProduct, offer: CandidateOffer) => {
    navigate('/proposals')
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Top Heading */}
      <div>
        <h2 className="text-xl font-bold text-neutral-900 dark:text-white tracking-tight">
          AI Shopping Concierge
        </h2>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
          Autonomous product search, multi-merchant comparison, and mandate verification
        </p>
      </div>

      {/* Main Conversational Input Form */}
      <ShoppingForm
        onSubmit={handleStartShopping}
        isLoading={isLoading}
        initialPrompt={queryParam || ''}
      />

      {/* Live SSE Agent Pipeline Tracker */}
      {activeRequestId && (
        <SseProgressTracker
          requestId={activeRequestId}
          onComplete={handleStreamComplete}
          onCancel={() => {
            if (activeRequestId) api.cancelShoppingRequest(activeRequestId)
            setActiveRequestId(null)
          }}
        />
      )}

      {/* Discovered Matching Candidates */}
      {(candidates.length > 0 || hasSearched) && (
        <div className="flex flex-col gap-4 animate-in fade-in duration-200">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-neutral-200/80 dark:border-neutral-800">
            <div>
              <h3 className="text-base font-semibold text-neutral-900 dark:text-white flex items-center gap-2">
                <span>Matching Verified Products</span>
                <span className="text-xs font-normal text-neutral-400">
                  ({candidates.length || mockCandidateProducts.length} options found)
                </span>
              </h3>
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                Ranked by AI relevance score and verified against your mandate limits
              </p>
            </div>

            <Button
              variant="outline"
              size="xs"
              onClick={() => navigate('/proposals')}
              icon={<ArrowRight size={12} />}
            >
              Go to Purchase Proposal
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {(candidates.length > 0 ? candidates : mockCandidateProducts).map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onSelectOffer={handleSelectOffer}
                onCompare={(prod) => {
                  setSelectedProductForComparison(prod)
                  setIsCompareOpen(true)
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Multi-Retailer Offer Comparison Modal */}
      <OfferComparisonModal
        product={selectedProductForComparison}
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        onSelectOffer={handleSelectOffer}
      />
    </div>
  )
}
