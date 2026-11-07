/**
 * TypeScript data models and API response types for Carti.
 * Conforms strictly to Carti Core Module Specification v1.0 and FastAPI backend schemas.
 */

export type RequestStatus =
  | 'submitted'
  | 'planning'
  | 'searching'
  | 'comparing'
  | 'verifying'
  | 'proposal_ready'
  | 'user_review'
  | 'checkout_started'
  | 'completed'
  | 'cancelled'
  | 'failed'

export type ProposalStatus =
  | 'pending'
  | 'accepted'
  | 'checkout_started'
  | 'ordered'
  | 'rejected'
  | 'expired'
  | 'invalidated'

export type OrderStatus =
  | 'created'
  | 'buyer_approved'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'refunded'

export type MandateStatus = 'active' | 'superseded' | 'revoked' | 'expired'

export interface User {
  id: string
  email: string
  full_name?: string
  status: 'active' | 'inactive' | 'suspended'
  created_at: string
}

export interface Mandate {
  id: string
  user_id: string
  version: number
  total_budget: string // Decimal as string e.g. "100.00"
  per_item_cap: string // Decimal as string e.g. "50.00"
  currency: string
  allowed_categories: string[]
  blocked_categories: string[]
  allowed_retailers: string[]
  max_quantity_per_product: number
  price_tolerance_pct: number
  status: MandateStatus
  expires_at: string
  created_at: string
  updated_at?: string
}

export interface BudgetBreakdown {
  mandate_id: string
  total_budget: string
  captured_spending: string
  active_reservations: string
  available_budget: string
  currency: string
}

export interface ShoppingRequestInput {
  prompt: string
  category?: string
  max_price?: number | string
  preferred_brand?: string
  preferred_retailer?: string
  required_attributes?: Record<string, any>
}

export interface ShoppingRequest {
  id: string
  user_id: string
  mandate_id: string
  mandate_version: number
  prompt: string
  normalized_category?: string
  extracted_constraints?: Record<string, any>
  status: RequestStatus
  error_message?: string
  selected_candidate_id?: string
  active_proposal_id?: string
  created_at: string
  updated_at: string
}

export interface CandidateOffer {
  id: string
  candidate_id: string
  provider_offer_id: string
  domain: string
  buy_url: string
  price_amount: string // Decimal string
  currency: string
  availability: 'InStock' | 'OutOfStock' | 'PreOrder'
  condition: string
  shipping_amount: string
  tax_amount: string
  is_eligible: boolean
  ineligibility_reason?: string
  last_refreshed_at: string
}

export interface CandidateProduct {
  id: string
  request_id: string
  channel3_product_id: string
  title: string
  brand?: string
  category?: string
  image_url?: string
  attributes?: Record<string, any>
  rank_score: string // e.g. "0.95"
  rank_reason: string
  offers: CandidateOffer[]
  created_at: string
}

export interface GuardrailCheck {
  rule: string
  passed: boolean
  actual?: string
  limit?: string
  reason: string
}

export interface GuardrailResult {
  passed: boolean
  checks: GuardrailCheck[]
  blocked_reason?: string
}

export interface Proposal {
  id: string
  request_id: string
  user_id: string
  mandate_id: string
  mandate_version: number
  candidate_id: string
  offer_id: string
  quantity: number
  unit_price_at_proposal: string
  subtotal_at_proposal: string
  shipping_amount: string
  tax_amount: string
  total_amount: string
  currency: string
  rationale: string
  guardrail_result: GuardrailResult
  verification_status: 'unverified' | 'verified' | 'failed'
  verification_result?: Record<string, any>
  product?: {
    product_id: string
    title: string
    brand?: string
    category?: string
    image_url?: string
  }
  offer?: {
    offer_id: string
    domain: string
    buy_url: string
    price_amount: string
    currency: string
    availability: string
    condition: string
  }
  status: ProposalStatus
  expires_at: string
  created_at: string
  updated_at?: string
}

export interface Order {
  id: string
  proposal_id: string
  user_id: string
  paypal_order_id?: string
  paypal_capture_id?: string
  create_request_id?: string
  amount: string
  currency: string
  status: OrderStatus
  budget_reserved: string
  captured_at?: string
  created_at: string
  updated_at: string
  product_title?: string
  retailer_domain?: string
  retailer_buy_url?: string
  quantity?: number
  fulfillment_note?: string
  refunds?: Refund[]
}

export interface Refund {
  id: string
  order_id: string
  paypal_refund_id?: string
  amount: string
  currency: string
  status: 'completed' | 'pending' | 'failed'
  created_at: string
  reason?: string
}

export interface AuditEvent {
  id: string
  user_id: string
  event_type: string
  entity_type?: string
  entity_id?: string
  request_id?: string
  proposal_id?: string
  order_id?: string
  decision?: string
  reason?: string
  details?: Record<string, any>
  created_at: string
}

export interface SSEAgentEvent {
  step: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  timestamp: string
  payload?: any
}
