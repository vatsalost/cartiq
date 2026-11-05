import React, { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Sparkles, ArrowRight, RefreshCw, AlertCircle } from 'lucide-react'
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

  const handleStartShopping = async (input: ShoppingRequestInput) => {
    setIsLoading(true)
    setHasSearched(true)
    try {
      const req = await api.createShoppingRequest(input)
      setActiveRequestId(req.id)
    } catch (e) {
      console.error('Request creation error:', e)
      // Use fallback request ID to demonstrate SSE progress
      setActiveRequestId(`req_${Date.now()}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStreamComplete = async (proposalId?: string) => {
    // When SSE completes, load candidate comparison results or navigate to proposal
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
      // Small pause so user sees the "Completed" state before transitioning
      setTimeout(() => {
        navigate('/proposals')
      }, 1200)
    }
  }

  const handleSelectOffer = (product: CandidateProduct, offer: CandidateOffer) => {
    navigate('/proposals')
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Search Input Box */}
      <ShoppingForm onSubmit={handleStartShopping} isLoading={isLoading} />

      {/* SSE Progress Timeline when request is active */}
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

      {/* Discovered Candidates Section */}
      {(candidates.length > 0 || hasSearched) && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-extrabold text-neutral-900 dark:text-white tracking-tight flex items-center gap-2">
                <span>Evaluated Product Candidates</span>
              </h3>
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                Channel3 catalog items filtered against active mandate and category rules
              </p>
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/proposals')}
              icon={<ArrowRight size={14} />}
            >
              Go to Final Proposal
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

      {/* Comparison Modal */}
      <OfferComparisonModal
        product={selectedProductForComparison}
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        onSelectOffer={handleSelectOffer}
      />
    </div>
  )
}
