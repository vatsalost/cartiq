import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, ShoppingBag, Plus } from 'lucide-react'
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
  const { mandate, breakdown } = useAuth()
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
      {/* Top Controls Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg md:text-xl font-bold text-neutral-900 dark:text-white tracking-tight">
            Overview
          </h2>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
            Spending budget, active requests, and settled orders
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/mandate')}
            icon={<Shield size={13} />}
          >
            Mandate
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/orders')}
            icon={<ShoppingBag size={13} />}
          >
            Orders
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/shopping')}
            icon={<Plus size={14} />}
          >
            New Request
          </Button>
        </div>
      </div>

      {/* Metric Cards & Spending Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
        {/* Left Stat Cards */}
        <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-3 gap-3">
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
            subtitle="Pending checkout"
            variant="dark"
            iconType="neutral"
          />
        </div>

        {/* Right Spending Overview */}
        <div className="lg:col-span-5">
          <CashflowChart />
        </div>
      </div>

      {/* Recent Activity Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="p-4 sm:p-5 rounded-2xl bg-neutral-50/70 dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800">
          <RecentRequestsTable requests={requests} />
        </div>

        <div className="p-4 sm:p-5 rounded-2xl bg-neutral-50/70 dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800">
          <RecentOrdersTable orders={orders} />
        </div>
      </div>
    </div>
  )
}
