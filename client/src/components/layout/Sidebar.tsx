import React from 'react'
import { NavLink, Link } from 'react-router-dom'
import {
  LayoutDashboard,
  Sparkles,
  ShieldCheck,
  FileCheck2,
  Receipt,
  Activity,
  Settings,
  X,
  CreditCard,
  ExternalLink,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { mandate, breakdown, userEmail } = useAuth()

  const navItems = [
    { name: 'Overview', path: '/', icon: LayoutDashboard },
    { name: 'Shopping', path: '/shopping', icon: Sparkles },
    { name: 'Mandate', path: '/mandate', icon: ShieldCheck },
    { name: 'Proposals', path: '/proposals', icon: FileCheck2 },
    { name: 'Orders', path: '/orders', icon: Receipt },
    { name: 'Activity & Audit', path: '/history', icon: Activity },
    { name: 'Settings', path: '/settings', icon: Settings },
  ]

  // Calculate budget utilization percentage
  const totalBudget = parseFloat(mandate?.total_budget || '150.00')
  const availableBudget = parseFloat(breakdown?.available_budget || '65.02')
  const usedPercent = Math.min(
    100,
    Math.max(0, Math.round(((totalBudget - availableBudget) / totalBudget) * 100))
  )

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-xs lg:hidden transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-64 bg-white dark:bg-[#17191C] border-r border-neutral-200/90 dark:border-neutral-800 flex flex-col justify-between transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Top: Logo & Nav */}
        <div className="flex flex-col">
          {/* Logo & Close on mobile */}
          <div className="h-14 px-5 flex items-center justify-between border-b border-neutral-100 dark:border-neutral-800">
            <Link to="/" onClick={onClose} className="flex items-center gap-2.5 group">
              <div className="w-7 h-7 rounded-lg bg-[#95EB68] flex items-center justify-center text-[#17191C] font-black text-sm tracking-tighter shadow-xs">
                C
              </div>
              <div className="flex flex-col">
                <span className="text-base font-bold text-neutral-900 dark:text-white tracking-tight leading-none group-hover:text-neutral-700 dark:group-hover:text-neutral-200 transition-colors">
                  Carti
                </span>
                <span className="text-[10px] text-neutral-400 font-medium tracking-wide uppercase mt-0.5">
                  AI Purchasing
                </span>
              </div>
            </Link>

            <button
              onClick={onClose}
              className="lg:hidden p-1.5 rounded-md text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800"
            >
              <X size={18} />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 flex flex-col gap-1">
            <div className="px-3 py-1.5 text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
              Platform
            </div>
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onClose}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-white font-semibold'
                        : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <div className="flex items-center gap-2.5">
                        <Icon
                          size={16}
                          className={isActive ? 'text-[#17191C] dark:text-[#95EB68]' : 'text-neutral-400'}
                        />
                        <span>{item.name}</span>
                      </div>
                      {isActive && (
                        <span className="w-1.5 h-1.5 rounded-full bg-[#95EB68]" />
                      )}
                    </>
                  )}
                </NavLink>
              )
            })}
          </nav>
        </div>

        {/* Bottom: Mandate Widget & User Profile */}
        <div className="p-3 border-t border-neutral-100 dark:border-neutral-800 flex flex-col gap-3">
          {/* Compact Mandate Budget Card */}
          <Link
            to="/mandate"
            onClick={onClose}
            className="p-3 rounded-xl bg-neutral-50 dark:bg-[#131417] border border-neutral-200/80 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 transition-all group"
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-neutral-700 dark:text-neutral-300 group-hover:text-neutral-900 dark:group-hover:text-white flex items-center gap-1.5">
                <ShieldCheck size={13} className="text-[#95EB68]" />
                Mandate v{mandate?.version || 2}
              </span>
              <span className="text-[11px] font-mono text-neutral-500 dark:text-neutral-400">
                ${availableBudget.toFixed(2)} left
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-1.5 bg-neutral-200 dark:bg-neutral-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-[#95EB68] rounded-full transition-all duration-500"
                style={{ width: `${usedPercent}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-[10px] text-neutral-400 mt-1.5">
              <span>Used: {usedPercent}%</span>
              <span>Cap: ${mandate?.per_item_cap || '60.00'}/item</span>
            </div>
          </Link>

          {/* User Profile Pill */}
          <div className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-neutral-50/50 dark:bg-transparent text-xs">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded-full bg-neutral-200 dark:bg-neutral-700 flex items-center justify-center font-bold text-neutral-700 dark:text-neutral-300 shrink-0 text-xs">
                {userEmail.charAt(0).toUpperCase()}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-neutral-800 dark:text-neutral-200 truncate">
                  {userEmail.split('@')[0]}
                </span>
                <span className="text-[10px] text-neutral-400 truncate">
                  Authorized Buyer
                </span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
