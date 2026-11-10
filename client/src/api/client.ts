/**
 * Centralized typed API service for Carti backend integration.
 * Strictly adheres to Core Module Specification v1.0.
 */

import {
  Mandate,
  BudgetBreakdown,
  ShoppingRequest,
  ShoppingRequestInput,
  CandidateProduct,
  Proposal,
  Order,
  Refund,
  AuditEvent,
} from './types'
import {
  mockMandate,
  mockBudgetBreakdown,
  mockCandidateProducts,
  mockProposal,
  mockRequests,
  mockOrders,
  mockAuditTimeline,
} from './mockData'

const API_BASE = '/api'

export class CartiApiClient {
  private demoToken = '00000000-0000-0000-0000-000000000001'
  private useMockFallback = true

  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${this.demoToken}`,
    }
  }

  // --- HEALTH & STATUS ---
  async checkHealth(): Promise<{ status: string; environment?: string; database?: string }> {
    try {
      const res = await fetch(`${API_BASE}/health`, { method: 'GET' })
      if (!res.ok) throw new Error('Health check failed')
      return await res.json()
    } catch {
      return { status: 'mock_mode', environment: 'development', database: 'mock' }
    }
  }

  // --- MANDATE SERVICE (B3 / F2) ---
  async getCurrentMandate(): Promise<{ mandate: Mandate; breakdown: BudgetBreakdown }> {
    try {
      const res = await fetch(`${API_BASE}/mandates/current`, {
        headers: this.getHeaders(),
      })
      if (!res.ok) throw new Error('Failed to fetch mandate')
      const data = await res.json()
      return {
        mandate: data,
        breakdown: {
          mandate_id: data.id,
          total_budget: data.total_budget,
          captured_spending: data.captured_spending || '0.00',
          active_reservations: data.active_reservations || '0.00',
          available_budget: data.available_budget || data.total_budget,
          currency: data.currency || 'USD',
        },
      }
    } catch (err) {
      if (this.useMockFallback) {
        return { mandate: mockMandate, breakdown: mockBudgetBreakdown }
      }
      throw err
    }
  }

  async saveMandate(payload: {
    total_budget: number | string
    per_item_cap: number | string
    currency: string
    allowed_categories: string[]
    blocked_categories: string[]
    allowed_retailers: string[]
    max_quantity_per_product: number
    price_tolerance_pct: number
    expires_at?: string
  }): Promise<Mandate> {
    try {
      // Normalize price_tolerance_pct: if user passes whole number like 10 (10%), scale to 0.10 for backend validation
      const priceTolerance =
        Number(payload.price_tolerance_pct) > 0.5
          ? Number((Number(payload.price_tolerance_pct) / 100).toFixed(4))
          : Number(Number(payload.price_tolerance_pct).toFixed(4))

      // Ensure valid future ISO expiration timestamp (default +90 days)
      const expiresAt =
        payload.expires_at ||
        new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString()

      const formattedPayload = {
        total_budget: String(payload.total_budget),
        per_item_cap: String(payload.per_item_cap),
        currency: payload.currency || 'USD',
        allowed_categories: payload.allowed_categories,
        blocked_categories: payload.blocked_categories || [],
        allowed_retailers: payload.allowed_retailers || [],
        max_quantity_per_product: payload.max_quantity_per_product || 1,
        price_tolerance_pct: priceTolerance,
        expires_at: expiresAt,
      }

      const res = await fetch(`${API_BASE}/mandates`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(formattedPayload),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData?.error?.message || 'Failed to update spending mandate')
      }
      return await res.json()
    } catch (err) {
      if (this.useMockFallback) {
        return {
          ...mockMandate,
          version: mockMandate.version + 1,
          total_budget: String(payload.total_budget),
          per_item_cap: String(payload.per_item_cap),
          currency: payload.currency,
          allowed_categories: payload.allowed_categories,
          blocked_categories: payload.blocked_categories,
          allowed_retailers: payload.allowed_retailers,
          max_quantity_per_product: payload.max_quantity_per_product,
          price_tolerance_pct: payload.price_tolerance_pct,
          updated_at: new Date().toISOString(),
        }
      }
      throw err
    }
  }

  // --- SHOPPING CONCIERGE & REQUEST LIFECYCLE (B4 / B5 / F3) ---
  async createShoppingRequest(input: ShoppingRequestInput): Promise<ShoppingRequest> {
    try {
      const payload = {
        text: input.prompt,
        filters: {
          category: input.category || undefined,
          max_price: input.max_price ? Number(input.max_price) : undefined,
          preferred_brand: input.preferred_brand || undefined,
          preferred_retailer: input.preferred_retailer || undefined,
        },
      }
      const res = await fetch(`${API_BASE}/requests`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData?.error?.message || 'Failed to create shopping request')
      }
      const data = await res.json()
      return {
        id: data.request_id || data.id,
        user_id: this.demoToken,
        mandate_id: mockMandate.id,
        mandate_version: 1,
        prompt: input.prompt,
        status: data.status || 'queued',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        ...data,
      }
    } catch (err) {
      if (this.useMockFallback) {
        const newReq: ShoppingRequest = {
          id: `req_${Date.now()}`,
          user_id: this.demoToken,
          mandate_id: mockMandate.id,
          mandate_version: mockMandate.version,
          prompt: input.prompt,
          normalized_category: input.category || 'General',
          status: 'submitted',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        return newReq
      }
      throw err
    }
  }

  async getShoppingRequest(requestId: string): Promise<ShoppingRequest> {
    try {
      const res = await fetch(`${API_BASE}/requests/${requestId}`, {
        headers: this.getHeaders(),
      })
      if (!res.ok) throw new Error('Shopping request not found')
      return await res.json()
    } catch (err) {
      if (this.useMockFallback) {
        return mockRequests.find((r) => r.id === requestId) || mockRequests[0]
      }
      throw err
    }
  }

  async cancelShoppingRequest(requestId: string): Promise<ShoppingRequest> {
    try {
      const res = await fetch(`${API_BASE}/requests/${requestId}/cancel`, {
        method: 'POST',
        headers: this.getHeaders(),
      })
      if (!res.ok) throw new Error('Failed to cancel request')
      return await res.json()
    } catch (err) {
      if (this.useMockFallback) {
        return { ...mockRequests[0], id: requestId, status: 'cancelled' }
      }
      throw err
    }
  }

  async getCandidates(requestId: string): Promise<CandidateProduct[]> {
    try {
      const res = await fetch(`${API_BASE}/requests/${requestId}/candidates`, {
        headers: this.getHeaders(),
      })
      if (!res.ok) throw new Error('Failed to fetch candidate products')
      const data = await res.json()
      return Array.isArray(data) ? data : data.candidates || []
    } catch (err) {
      if (this.useMockFallback) {
        return mockCandidateProducts
      }
      throw err
    }
  }

  // --- PROPOSAL SERVICE (B9 / F5) ---
  async getProposal(proposalId: string): Promise<Proposal> {
    try {
      const cleanId = proposalId.startsWith('prop_') ? proposalId.replace(/^prop_/, '') : proposalId
      const res = await fetch(`${API_BASE}/proposals/${cleanId}`, {
        headers: this.getHeaders(),
      })
      if (!res.ok) throw new Error('Proposal not found')
      return await res.json()
    } catch (err) {
      if (this.useMockFallback) {
        return mockProposal
      }
      throw err
    }
  }

  async rejectProposal(proposalId: string, reason = 'user_rejected'): Promise<Proposal> {
    try {
      const cleanId = proposalId.startsWith('prop_') ? proposalId.replace(/^prop_/, '') : proposalId
      const res = await fetch(`${API_BASE}/proposals/${cleanId}/reject`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ reason }),
      })
      if (!res.ok) throw new Error('Failed to reject proposal')
      return await res.json()
    } catch (err) {
      if (this.useMockFallback) {
        return { ...mockProposal, status: 'rejected' }
      }
      throw err
    }
  }

  // --- PAYPAL ORDER & CHECKOUT (B10 / F6) ---
  async createOrderFromProposal(
    proposalId: string,
    checkoutAttemptId: string
  ): Promise<{ order_id: string; paypal_order_id: string; status: string; amount: string; currency: string; approval_url?: string }> {
    try {
      const cleanId = proposalId.startsWith('prop_') ? proposalId.replace(/^prop_/, '') : proposalId
      const res = await fetch(`${API_BASE}/proposals/${cleanId}/order`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ checkout_attempt_id: checkoutAttemptId }),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData?.error?.message || 'Failed to initialize PayPal order')
      }
      return await res.json()
    } catch (err) {
      const isLivePayPal = !!import.meta.env.VITE_PAYPAL_CLIENT_ID && import.meta.env.VITE_PAYPAL_CLIENT_ID !== 'test'
      if (this.useMockFallback && !isLivePayPal) {
        return {
          order_id: `ord_${Date.now()}`,
          paypal_order_id: `PP-SANDBOX-${Math.random().toString(36).substring(2, 10).toUpperCase()}`,
          status: 'created',
          amount: mockProposal.total_amount,
          currency: mockProposal.currency,
          approval_url: 'https://www.sandbox.paypal.com/checkoutnow',
        }
      }
      throw err
    }
  }

  async captureOrder(
    orderId: string,
    paypalOrderId?: string
  ): Promise<Order> {
    try {
      const res = await fetch(`${API_BASE}/orders/${orderId}/capture`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ paypal_order_id: paypalOrderId }),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData?.error?.message || 'Payment capture failed')
      }
      return await res.json()
    } catch (err) {
      if (this.useMockFallback) {
        return {
          ...mockOrders[0],
          id: orderId,
          paypal_order_id: paypalOrderId || mockOrders[0].paypal_order_id,
          paypal_capture_id: `CAP-${Math.random().toString(36).substring(2, 12).toUpperCase()}`,
          status: 'completed',
          captured_at: new Date().toISOString(),
        }
      }
      throw err
    }
  }

  async refundOrder(orderId: string, reason = 'Buyer requested return'): Promise<Refund> {
    try {
      const res = await fetch(`${API_BASE}/orders/${orderId}/refund`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ reason }),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData?.error?.message || 'Refund processing failed')
      }
      return await res.json()
    } catch (err) {
      if (this.useMockFallback) {
        return {
          id: `ref_${Date.now()}`,
          order_id: orderId,
          paypal_refund_id: `REF-${Math.random().toString(36).substring(2, 10).toUpperCase()}`,
          amount: '49.99',
          currency: 'USD',
          status: 'completed',
          created_at: new Date().toISOString(),
          reason,
        }
      }
      throw err
    }
  }

  async getOrder(orderId: string): Promise<Order> {
    try {
      const res = await fetch(`${API_BASE}/orders/${orderId}`, {
        headers: this.getHeaders(),
      })
      if (!res.ok) throw new Error('Order not found')
      return await res.json()
    } catch (err) {
      if (this.useMockFallback) {
        return mockOrders.find((o) => o.id === orderId) || mockOrders[0]
      }
      throw err
    }
  }

  async listOrders(): Promise<{ items: Order[]; total: number }> {
    try {
      const res = await fetch(`${API_BASE}/orders`, {
        headers: this.getHeaders(),
      })
      if (!res.ok) throw new Error('Failed to list orders')
      const data = await res.json()
      return {
        items: Array.isArray(data.items) ? data.items : data,
        total: data.total || data.length || 0,
      }
    } catch (err) {
      if (this.useMockFallback) {
        return { items: mockOrders, total: mockOrders.length }
      }
      throw err
    }
  }

  // --- HISTORY & AUDIT TIMELINE (B13 / F8) ---
  async getAuditTimeline(): Promise<AuditEvent[]> {
    try {
      const res = await fetch(`${API_BASE}/audit/timeline`, {
        headers: this.getHeaders(),
      })
      if (!res.ok) throw new Error('Failed to load audit timeline')
      const data = await res.json()
      return Array.isArray(data) ? data : data.items || []
    } catch (err) {
      if (this.useMockFallback) {
        return mockAuditTimeline
      }
      throw err
    }
  }

  // SSE Stream URL generator
  getStreamUrl(requestId: string): string {
    return `${API_BASE}/requests/${requestId}/stream`
  }
}

export const api = new CartiApiClient()
