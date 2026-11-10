import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ShieldCheck,
  CreditCard,
  Clock,
  CheckCircle2,
  Plus,
} from 'lucide-react'
import { StatCard } from '../components/dashboard/StatCard'
import { SpendingOverviewCard } from '../components/dashboard/SpendingOverviewCard'
import { OverviewBottomRow } from '../components/dashboard/OverviewBottomRow'
import { Button } from '../components/common/Button'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import { Order } from '../api/types'
import { mockOrders } from '../api/mockData'

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const { mandate, breakdown, userEmail } = useAuth()
  const [orders, setOrders] = useState<Order[]>(mockOrders)

  useEffect(() => {
    async function loadData() {
      try {
        const orderRes = await api.listOrders()
        if (orderRes.items && orderRes.items.length > 0) {
          setOrders(orderRes.items)
        }
      } catch {
        // Fallback to mock state
      }
    }
    loadData()
  }, [])

  const availableAmount = mandate ? (breakdown?.available_budget || mandate.total_budget || '0.00') : '0.00'
  const capturedAmount = parseFloat(breakdown?.captured_spending || '0.00')
  const reservedAmount = parseFloat(breakdown?.active_reservations || '0.00')
  const totalCommitted = (capturedAmount + reservedAmount).toFixed(2)

  return (
    <div className="flex flex-col gap-6">
      {/* Top Header / Greeting */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400">
            Good to see you, {userEmail ? userEmail.split('@')[0] : 'demo-user'}
          </div>
          <h1 className="text-[28px] font-bold text-neutral-900 dark:text-white tracking-tight mt-0.5 leading-tight">
            Overview
          </h1>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/shopping')}
            icon={<Plus size={16} strokeWidth={1.8} />}
          >
            New Shopping Request
          </Button>
        </div>
      </div>

      {/* No Mandate Alert */}
      {!mandate && (
        <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-800/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-amber-900 dark:text-amber-200">
          <div className="flex items-center gap-2.5">
            <ShieldCheck size={18} className="text-amber-600 dark:text-amber-400 shrink-0" />
            <span>
              <strong>No Active Spending Mandate:</strong> Budget metrics and authorized boundaries will appear once you set up your spending mandate.
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

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Available Budget"
          amount={`$${availableAmount}`}
          subtitle={`of $${mandate?.total_budget || '150.00'} total cap`}
          badge={{ text: '43.3% available', variant: 'lime' }}
          icon={<ShieldCheck size={20} strokeWidth={1.8} />}
          variant="accent"
        />

        <StatCard
          title="Committed"
          amount={`$${totalCommitted}`}
          subtitle="Captured + in-flight"
          badge={{ text: 'Active Mandate', variant: 'neutral' }}
          icon={<CreditCard size={20} strokeWidth={1.8} />}
        />

        <StatCard
          title="Pending Proposals"
          amount="1"
          subtitle={`$${reservedAmount.toFixed(2)} held in reservation`}
          badge={{ text: 'Needs Review', variant: 'lavender' }}
          icon={<Clock size={20} strokeWidth={1.8} />}
        />

        <StatCard
          title="Completed Orders"
          amount={`${orders.length}`}
          subtitle="100% retailer verified"
          badge={{ text: 'This Mandate', variant: 'success' }}
          icon={<CheckCircle2 size={20} strokeWidth={1.8} />}
        />
      </div>

      {/* Middle Row: Spending Overview with Line Area Chart + Donut & Ledger */}
      <SpendingOverviewCard />

      {/* Bottom Row: Recent Activity Timeline + Quick Actions 2x2 Grid */}
      <OverviewBottomRow />
    </div>
  )
}
