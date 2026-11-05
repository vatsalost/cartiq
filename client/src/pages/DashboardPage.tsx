import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, Shield, ShoppingBag, Plus, ArrowUpRight } from 'lucide-react'
import { StatCard } from '../components/dashboard/StatCard'
import { CashflowChart } from '../components/dashboard/CashflowChart'
import { RecentRequestsTable } from '../components/dashboard/RecentRequestsTable'
import { RecentOrdersTable } from '../components/dashboard/RecentOrdersTable'
import { Button } from '../components/common/Button'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import { ShoppingRequest, Order } from '../api/types'
import { mockRequests, mockOrders } from '../api/mockData'

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const { mandate, breakdown, isLoadingMandate } = useAuth()
  const [requests, setRequests] = useState<ShoppingRequest[]>(mockRequests)
  const [orders, setOrders] = useState<Order[]>(mockOrders)

  useEffect(() => {
    async function loadData() {
      try {
        const orderRes = await api.listOrders()
        if (orderRes.items && orderRes.items.length > 0) {
          setOrders(orderRes.items)
        }
      } catch {
        // Fallback to mock data already initialized
      }
    }
    loadData()
  }, [])

  return (
    <div className="flex flex-col gap-6">
      {/* Top Banner & Quick Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl md:text-2xl font-black text-neutral-900 dark:text-white tracking-tight flex items-center gap-2">
            <span>Welcome to Carti Concierge</span>
          </h2>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
            Real-time autonomous purchasing governed by verified spending mandates
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/mandate')}
            icon={<Shield size={14} />}
          >
            Manage Mandate
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/orders')}
            icon={<ShoppingBag size={14} />}
          >
            All Orders
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/shopping')}
            icon={<Plus size={16} />}
          >
            New Shopping Request
          </Button>
        </div>
      </div>

      {/* Hero Visual Section matching reference screenshots */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* Left 3 Stat Cards ("Cash flow" row from screenshots) */}
        <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            title="Available Budget"
            amount={`$${breakdown?.available_budget || '65.02'}`}
            subtitle={`${mandate?.currency || 'USD'} Remaining`}
            variant="lime"
            iconType="up"
          />

          <StatCard
            title="Captured Spending"
            amount={`$${breakdown?.captured_spending || '34.99'}`}
            subtitle="Confirmed payments"
            variant="lavender"
            iconType="down"
          />

          <StatCard
            title="Active Reservations"
            amount={`$${breakdown?.active_reservations || '49.99'}`}
            subtitle="Pipeline checkouts"
            variant="dark"
            iconType="neutral"
          />
        </div>

        {/* Right Dark Chart Container ("Profit and loss" card from screenshots) */}
        <div className="lg:col-span-5">
          <CashflowChart />
        </div>
      </div>

      {/* Two Tabular Panels matching screenshots bottom layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-2">
        <div className="p-5 md:p-6 rounded-[28px] bg-neutral-50/70 dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800">
          <RecentRequestsTable requests={requests} />
        </div>

        <div className="p-5 md:p-6 rounded-[28px] bg-neutral-50/70 dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800">
          <RecentOrdersTable orders={orders} />
        </div>
      </div>
    </div>
  )
}
