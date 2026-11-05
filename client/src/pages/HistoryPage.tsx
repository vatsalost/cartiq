import React, { useEffect, useState } from 'react'
import { HistoryTabs } from '../components/history/HistoryTabs'
import { api } from '../api/client'
import { ShoppingRequest, CandidateProduct, Order, AuditEvent } from '../api/types'
import {
  mockRequests,
  mockCandidateProducts,
  mockOrders,
  mockAuditTimeline,
} from '../api/mockData'

export const HistoryPage: React.FC = () => {
  const [requests, setRequests] = useState<ShoppingRequest[]>(mockRequests)
  const [candidates, setCandidates] = useState<CandidateProduct[]>(mockCandidateProducts)
  const [orders, setOrders] = useState<Order[]>(mockOrders)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>(mockAuditTimeline)

  useEffect(() => {
    async function loadHistory() {
      try {
        const [ordersRes, timelineRes] = await Promise.all([
          api.listOrders().catch(() => ({ items: mockOrders, total: mockOrders.length })),
          api.getAuditTimeline().catch(() => mockAuditTimeline),
        ])
        if (ordersRes.items && ordersRes.items.length > 0) {
          setOrders(ordersRes.items)
        }
        if (timelineRes && timelineRes.length > 0) {
          setAuditEvents(timelineRes)
        }
      } catch {
        // Fallback to mock state
      }
    }
    loadHistory()
  }, [])

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg md:text-xl font-bold text-neutral-900 dark:text-white tracking-tight">
          History & Audit Trail
        </h2>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
          Review previous requests, product comparisons, completed orders, and audit logs
        </p>
      </div>

      <HistoryTabs
        requests={requests}
        candidates={candidates}
        orders={orders}
        auditEvents={auditEvents}
      />
    </div>
  )
}
