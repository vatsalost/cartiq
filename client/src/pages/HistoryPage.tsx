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
        <h2 className="text-xl md:text-2xl font-black text-neutral-900 dark:text-white tracking-tight flex items-center gap-2">
          <span>History & Audit Trail</span>
        </h2>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
          Carti Core Module B13: Cryptographically non-repudiable audit logs and lineage snapshots
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
