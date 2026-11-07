import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Sparkles,
  FileText,
  ShieldCheck,
  ShoppingBag,
  ArrowRight,
  Clock,
  CheckCircle2,
  Settings2,
  Search,
} from 'lucide-react'

interface ActivityItem {
  id: string
  title: string
  subtitle: string
  time: string
  type: 'proposal' | 'order' | 'mandate' | 'search'
  amount?: string
}

export const OverviewBottomRow: React.FC = () => {
  const navigate = useNavigate()

  const activityItems: ActivityItem[] = [
    {
      id: 'act_1',
      title: 'Proposal generated',
      subtitle: 'Desk Lamp ($49.99)',
      time: 'Today, 2:15 PM',
      type: 'proposal',
      amount: '$49.99',
    },
    {
      id: 'act_2',
      title: 'Order completed',
      subtitle: 'USB-C Hub ($34.99)',
      time: 'Yesterday, 4:30 PM',
      type: 'order',
      amount: '$34.99',
    },
    {
      id: 'act_3',
      title: 'Mandate updated',
      subtitle: 'Total Budget $150.00',
      time: 'May 10, 11:00 AM',
      type: 'mandate',
    },
    {
      id: 'act_4',
      title: 'Shopping search',
      subtitle: 'French Press Coffee Maker',
      time: 'May 9, 3:20 PM',
      type: 'search',
    },
  ]

  const getIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'proposal':
        return <FileText size={14} strokeWidth={1.8} className="text-[#6366F1]" />
      case 'order':
        return <CheckCircle2 size={14} strokeWidth={1.8} className="text-[#1D4A18] dark:text-[#95EB68]" />
      case 'mandate':
        return <ShieldCheck size={14} strokeWidth={1.8} className="text-amber-600 dark:text-amber-400" />
      case 'search':
        return <Search size={14} strokeWidth={1.8} className="text-neutral-500" />
    }
  }

  const getIconBg = (type: ActivityItem['type']) => {
    switch (type) {
      case 'proposal':
        return 'bg-[#EEF0FD] dark:bg-[#1C2038]'
      case 'order':
        return 'bg-[#ECFADF] dark:bg-[#142617]'
      case 'mandate':
        return 'bg-amber-50 dark:bg-amber-950/40'
      case 'search':
        return 'bg-neutral-100 dark:bg-neutral-800'
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
      {/* Left: Recent Activity Timeline */}
      <div className="lg:col-span-7 rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-neutral-100 dark:border-neutral-800">
            <div>
              <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
                Recent Activity
              </h3>
              <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
                Real-time timeline of shopping requests, proposals, and settled captures
              </p>
            </div>
            <Link
              to="/activity"
              className="text-xs font-medium text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white flex items-center gap-1 group"
            >
              <span>View all</span>
              <ArrowRight size={14} strokeWidth={1.8} className="group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          <div className="relative mt-4 pl-3">
            {/* Timeline vertical bar */}
            <div className="absolute left-[21px] top-3 bottom-3 w-[2px] bg-neutral-100 dark:bg-neutral-800 pointer-events-none" />

            <div className="space-y-4">
              {activityItems.map((item) => (
                <div key={item.id} className="relative flex items-start gap-3 group">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 relative z-10 ${getIconBg(
                      item.type
                    )} ring-4 ring-white dark:ring-[#17191C]`}
                  >
                    {getIcon(item.type)}
                  </div>

                  <div className="flex-1 min-w-0 flex items-center justify-between gap-2 pt-0.5">
                    <div>
                      <div className="text-xs font-semibold text-neutral-900 dark:text-white">
                        {item.title}
                      </div>
                      <div className="text-[12px] text-neutral-500 dark:text-neutral-400 truncate">
                        {item.subtitle}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      {item.amount && (
                        <div className="text-xs font-semibold text-neutral-900 dark:text-white tabular-nums">
                          {item.amount}
                        </div>
                      )}
                      <div className="text-[11px] font-mono text-neutral-400 dark:text-neutral-500 tabular-nums">
                        {item.time}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="pt-3 mt-4 border-t border-neutral-100 dark:border-neutral-800 flex justify-end">
          <Link
            to="/activity"
            className="text-xs font-medium text-[#1D4A18] dark:text-[#95EB68] hover:underline flex items-center gap-1"
          >
            <span>View all activity</span>
            <ArrowRight size={14} strokeWidth={1.8} />
          </Link>
        </div>
      </div>

      {/* Right: Quick Actions 2x2 Grid */}
      <div className="lg:col-span-5 rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col justify-between">
        <div>
          <div className="pb-3 border-b border-neutral-100 dark:border-neutral-800">
            <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
              Quick Actions
            </h3>
            <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
              Launch shopping flows and manage controls
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-4">
            {/* Action 1: New Shopping Request */}
            <button
              onClick={() => navigate('/shopping')}
              className="p-3.5 rounded-xl text-left bg-neutral-50 dark:bg-neutral-800/50 hover:bg-[#ECFADF]/60 dark:hover:bg-[#142617]/50 border border-neutral-200/80 dark:border-neutral-700/60 transition-all group flex flex-col justify-between min-h-[110px]"
            >
              <div className="w-8 h-8 rounded-lg bg-[#95EB68] text-[#17191C] flex items-center justify-center font-bold mb-2">
                <Sparkles size={20} strokeWidth={1.8} />
              </div>
              <div>
                <div className="text-xs font-semibold text-neutral-900 dark:text-white group-hover:text-neutral-950 dark:group-hover:text-[#95EB68]">
                  New Request
                </div>
                <div className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5 line-clamp-2">
                  Autonomous AI search across retailers
                </div>
              </div>
            </button>

            {/* Action 2: Review Proposal */}
            <button
              onClick={() => navigate('/proposals')}
              className="p-3.5 rounded-xl text-left bg-neutral-50 dark:bg-neutral-800/50 hover:bg-[#EEF0FD]/60 dark:hover:bg-[#1C2038]/50 border border-neutral-200/80 dark:border-neutral-700/60 transition-all group flex flex-col justify-between min-h-[110px]"
            >
              <div className="w-8 h-8 rounded-lg bg-[#AAB5F8] text-[#17191C] flex items-center justify-center font-bold mb-2">
                <FileText size={20} strokeWidth={1.8} />
              </div>
              <div>
                <div className="text-xs font-semibold text-neutral-900 dark:text-white group-hover:text-neutral-950 dark:group-hover:text-[#AAB5F8]">
                  Review Proposal
                </div>
                <div className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5 line-clamp-2">
                  1 pending approval for <span className="tabular-nums font-medium">$49.99</span>
                </div>
              </div>
            </button>

            {/* Action 3: Adjust Mandate */}
            <button
              onClick={() => navigate('/mandate')}
              className="p-3.5 rounded-xl text-left bg-neutral-50 dark:bg-neutral-800/50 hover:bg-neutral-100 dark:hover:bg-neutral-800 border border-neutral-200/80 dark:border-neutral-700/60 transition-all group flex flex-col justify-between min-h-[110px]"
            >
              <div className="w-8 h-8 rounded-lg bg-neutral-200 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 flex items-center justify-center font-bold mb-2">
                <ShieldCheck size={20} strokeWidth={1.8} />
              </div>
              <div>
                <div className="text-xs font-semibold text-neutral-900 dark:text-white">
                  Adjust Mandate
                </div>
                <div className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5 line-clamp-2">
                  Manage caps and category limits
                </div>
              </div>
            </button>

            {/* Action 4: View Orders */}
            <button
              onClick={() => navigate('/orders')}
              className="p-3.5 rounded-xl text-left bg-neutral-50 dark:bg-neutral-800/50 hover:bg-neutral-100 dark:hover:bg-neutral-800 border border-neutral-200/80 dark:border-neutral-700/60 transition-all group flex flex-col justify-between min-h-[110px]"
            >
              <div className="w-8 h-8 rounded-lg bg-neutral-200 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 flex items-center justify-center font-bold mb-2">
                <ShoppingBag size={20} strokeWidth={1.8} />
              </div>
              <div>
                <div className="text-xs font-semibold text-neutral-900 dark:text-white">
                  View Orders
                </div>
                <div className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5 line-clamp-2">
                  Track deliveries and receipts
                </div>
              </div>
            </button>
          </div>
        </div>

        <div className="pt-3 mt-4 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between text-[11px] text-neutral-500 dark:text-neutral-400">
          <span>Autonomous agent active</span>
          <span className="font-mono text-[10px] text-neutral-400">v2.0.4</span>
        </div>
      </div>
    </div>
  )
}
