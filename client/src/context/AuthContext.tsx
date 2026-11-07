import React, { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'
import { Mandate, BudgetBreakdown } from '../api/types'

interface AuthContextType {
  userId: string
  userEmail: string
  mandate: Mandate | null
  breakdown: BudgetBreakdown | null
  isLoadingMandate: boolean
  backendConnected: boolean
  refreshMandate: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [userId] = useState('00000000-0000-0000-0000-000000000001')
  const [userEmail] = useState('demo-user@carti.local')
  const [mandate, setMandate] = useState<Mandate | null>(null)
  const [breakdown, setBreakdown] = useState<BudgetBreakdown | null>(null)
  const [isLoadingMandate, setIsLoadingMandate] = useState(true)
  const [backendConnected, setBackendConnected] = useState(false)

  const refreshMandate = async () => {
    try {
      setIsLoadingMandate(true)
      const health = await api.checkHealth()
      const isConnected = health.status === 'ok'
      setBackendConnected(isConnected)

      try {
        const res = await api.getCurrentMandate()
        setMandate(res.mandate)
        setBreakdown(res.breakdown)
      } catch (mandateErr) {
        if (isConnected) {
          console.info('No active mandate found on live backend, auto-seeding initial mandate...', mandateErr)
          try {
            const seeded = await api.saveMandate({
              total_budget: '150.00',
              per_item_cap: '60.00',
              currency: 'USD',
              allowed_categories: ['Lighting', 'Kitchen', 'Electronics', 'Home Office'],
              blocked_categories: [],
              allowed_retailers: ['amazon.com', 'target.com', 'bestbuy.com'],
              max_quantity_per_product: 2,
              price_tolerance_pct: 10,
            })
            setMandate(seeded)
            setBreakdown({
              mandate_id: seeded.id,
              total_budget: seeded.total_budget,
              captured_spending: '0.00',
              active_reservations: '0.00',
              available_budget: seeded.total_budget,
              currency: seeded.currency,
            })
          } catch (seedErr) {
            console.warn('Could not auto-seed mandate:', seedErr)
          }
        }
      }
    } catch (e) {
      console.warn('Backend unavailable, using Carti offline mock state', e)
      setBackendConnected(false)
    } finally {
      setIsLoadingMandate(false)
    }
  }

  useEffect(() => {
    refreshMandate()
  }, [])

  return (
    <AuthContext.Provider
      value={{
        userId,
        userEmail,
        mandate,
        breakdown,
        isLoadingMandate,
        backendConnected,
        refreshMandate,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
