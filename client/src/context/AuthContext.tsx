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
        setMandate(res?.mandate || null)
        setBreakdown(res?.breakdown || null)
      } catch {
        setMandate(null)
        setBreakdown(null)
      }
    } catch (e) {
      console.warn('Backend connection error:', e)
      setBackendConnected(false)
      setMandate(null)
      setBreakdown(null)
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
