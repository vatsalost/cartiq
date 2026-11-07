import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ShieldCheck,
  CreditCard,
  Clock,
  CheckCircle2,
  Plus,
  Sparkles,
  ArrowRight,
  TrendingUp,
} from 'lucide-react'
import { StatCard } from '../components/dashboard/StatCard'
import { CashflowChart } from '../components/dashboard/CashflowChart'
import { UnifiedActivitySection } from '../components/dashboard/UnifiedActivitySection'
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
        // Fallback to mock state
      }
    }
    loadData()
  }, [])

  const availableAmount = breakdown?.available_budget || '65.02'
  const capturedAmount = breakdown?.captured_spending || '34.99'
  const reservedAmount = breakdown?.active_reservations || '49.99'

  return (
    <div className="flex flex-col gap-6">
      {/* Top Controls Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-neutral-900 dark:text-white tracking-tight">
            Overview
          </h2>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
            Real-time financial authority, spending trajectory, and autonomous purchasing activity
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/mandate')}
            icon={<ShieldCheck size={14} />}
          >
            Manage Mandate
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/shopping')}
            icon={<Plus size={15} />}
          >
            New Shopping Request
          </Button>
        </div>
      </div>

      {/* 4 Compact Financial Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Available Budget"
          amount={`$${availableAmount}`}
          subtitle={`of $${mandate?.total_budget || '150.00'} total cap`}
          badge={{ text: 'Active & Verified', variant: 'lime' }}
          icon={<ShieldCheck size={16} />}
          variant="accent"
        />

        <StatCard
          title="Committed Spending"
          amount={`$${capturedAmount}`}
          subtitle="Confirmed PayPal captures"
          badge={{ text: '+12% this mo', variant: 'neutral' }}
          icon={<CreditCard size={16} />}
        />

        <StatCard
          title="Pending Proposals"
          amount="1 Active"
          subtitle={`$${reservedAmount} reserved in-flight`}
          badge={{ text: 'Action Needed', variant: 'lavender' }}
          icon={<Clock size={16} />}
        />

        <StatCard
          title="Completed Orders"
          amount={`${orders.length} Settled`}
          subtitle="100% retailer verified"
          badge={{ text: '0 Disputes', variant: 'success' }}
          icon={<CheckCircle2 size={16} />}
        />
      </div>

      {/* Middle Row: Spending Trajectory Chart + AI Quick Launch */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        <div className="lg:col-span-7">
          <CashflowChart />
        </div>

        <div className="lg:col-span-5 rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-neutral-100 dark:border-neutral-800">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-md bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center">
                  <Sparkles size={13} />
                </div>
                <span className="text-xs font-semibold text-neutral-900 dark:text-white">
                  Autonomous Concierge
                </span>
              </div>
              <span className="text-[10px] font-mono text-neutral-400">
                Rule Engine B5/B9 Active
              </span>
            </div>

            <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-3 leading-relaxed">
              Describe what you need in plain natural language. The autonomous agent parses specs, queries multi-merchant catalogs, checks stock in real-time, and locks proposals strictly under mandate limits.
            </p>

            {/* Quick Prompt Pill Examples */}
            <div className="mt-3.5 flex flex-col gap-1.5">
              <span className="text-[11px] font-medium text-neutral-400">Try quick prompt:</span>
              <button
                onClick={() => navigate('/shopping?q=Aesthetic%20warm%20desk%20lamp%20under%20$50')}
                className="text-left text-xs p-2 rounded-lg bg-neutral-50 dark:bg-neutral-800/60 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 transition-colors flex items-center justify-between group"
              >
                <span className="truncate">"Aesthetic warm desk lamp under $50"</span>
                <ArrowRight size={12} className="text-neutral-400 group-hover:translate-x-0.5 transition-transform shrink-0" />
              </button>
              <button
                onClick={() => navigate('/shopping?q=French%20press%20coffee%20maker%2034oz')}
                className="text-left text-xs p-2 rounded-lg bg-neutral-50 dark:bg-neutral-800/60 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 transition-colors flex items-center justify-between group"
              >
                <span className="truncate">"French press coffee maker 34oz"</span>
                <ArrowRight size={12} className="text-neutral-400 group-hover:translate-x-0.5 transition-transform shrink-0" />
              </button>
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-neutral-100 dark:border-neutral-800">
            <Button
              variant="secondary"
              size="sm"
              className="w-full justify-between"
              onClick={() => navigate('/shopping')}
              icon={<Sparkles size={14} />}
            >
              <span>Launch AI Shopping Assistant</span>
              <ArrowRight size={14} />
            </Button>
          </div>
        </div>
      </div>

      {/* Unified Recent Activity Section */}
      <UnifiedActivitySection requests={requests} orders={orders} />
    </div>
  )
}
