import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Menu,
  Search,
  Bell,
  ShieldCheck,
  User,
  ChevronDown,
  Check,
  CreditCard,
  Sparkles,
} from 'lucide-react'
import { ThemeToggle } from '../common/ThemeToggle'
import { useAuth } from '../../context/AuthContext'

interface HeaderProps {
  pageTitle: string
  onOpenMobileMenu: () => void
}

export const Header: React.FC<HeaderProps> = ({ pageTitle, onOpenMobileMenu }) => {
  const { userEmail, mandate, breakdown } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [isNotifOpen, setIsNotifOpen] = useState(false)
  const [isProfileOpen, setIsProfileOpen] = useState(false)
  const navigate = useNavigate()

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/shopping?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  const notifications = [
    {
      id: '1',
      title: 'Mandate Active',
      desc: `v${mandate?.version || 2} active with $${mandate?.total_budget || '150.00'} budget`,
      time: '10m ago',
      read: false,
    },
    {
      id: '2',
      title: 'Proposal Ready',
      desc: 'Bodum French Press matches all 8 purchase guardrails',
      time: '1h ago',
      read: false,
    },
    {
      id: '3',
      title: 'Payment Captured',
      desc: 'PayPal Capture CAP-74910382910 confirmed ($34.99)',
      time: '2h ago',
      read: true,
    },
  ]

  return (
    <header className="sticky top-0 z-30 h-14 w-full bg-white/80 dark:bg-[#17191C]/80 backdrop-blur-md border-b border-neutral-200/80 dark:border-neutral-800 px-4 md:px-8 flex items-center justify-between gap-4">
      {/* Left: Mobile Menu & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileMenu}
          className="lg:hidden p-1.5 rounded-lg text-neutral-500 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800 cursor-pointer"
          aria-label="Open sidebar"
        >
          <Menu size={18} />
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs text-neutral-400 hidden sm:inline">Workspace /</span>
          <h1 className="text-sm md:text-base font-semibold text-neutral-900 dark:text-white tracking-tight">
            {pageTitle}
          </h1>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5">
        {/* Global Search */}
        <form onSubmit={handleSearchSubmit} className="relative hidden md:block w-56 lg:w-72">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400"
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search products or orders..."
            className="w-full bg-neutral-100/80 dark:bg-[#141619] text-neutral-900 dark:text-white placeholder-neutral-400 text-xs rounded-lg pl-8.5 pr-8 py-1.5 border border-transparent focus:border-neutral-300 dark:focus:border-neutral-700 focus:bg-white dark:focus:bg-[#1C1F24] outline-hidden transition-all"
          />
          <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-neutral-400 border border-neutral-200 dark:border-neutral-700 rounded px-1 py-0.2 bg-white dark:bg-neutral-800">
            ↵
          </kbd>
        </form>

        {/* Mandate Balance Indicator Pill */}
        <Link
          to="/mandate"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-neutral-100/90 dark:bg-neutral-800/80 hover:bg-neutral-200/70 dark:hover:bg-neutral-700/80 text-xs text-neutral-700 dark:text-neutral-300 transition-colors"
          title="View Spending Mandate"
        >
          <span className="w-2 h-2 rounded-full bg-[#95EB68] shrink-0 animate-pulse" />
          <span className="font-semibold text-neutral-900 dark:text-white">
            ${breakdown?.available_budget || '65.02'}
          </span>
          <span className="text-[11px] text-neutral-400 hidden sm:inline">available</span>
        </Link>

        {/* Notifications Popover Toggle */}
        <div className="relative">
          <button
            onClick={() => setIsNotifOpen(!isNotifOpen)}
            className="w-8 h-8 rounded-lg flex items-center justify-center border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#17191C] text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-50 dark:hover:bg-neutral-800 relative cursor-pointer"
            title="Notifications"
          >
            <Bell size={15} />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[#95EB68]" />
          </button>

          {isNotifOpen && (
            <div
              className="absolute right-0 mt-2 w-72 rounded-xl bg-white dark:bg-[#17191C] border border-neutral-200 dark:border-neutral-800 shadow-xl p-3 z-50 animate-in fade-in zoom-in-95"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-100 dark:border-neutral-800">
                <span className="text-xs font-semibold text-neutral-900 dark:text-white">
                  Notifications
                </span>
                <span className="text-[10px] text-neutral-400 font-medium">3 unread</span>
              </div>
              <div className="flex flex-col gap-2 max-h-60 overflow-y-auto">
                {notifications.map((n) => (
                  <div
                    key={n.id}
                    className="p-2 rounded-lg bg-neutral-50 dark:bg-neutral-800/50 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-xs transition-colors"
                  >
                    <div className="flex items-center justify-between font-semibold text-neutral-800 dark:text-neutral-200">
                      <span>{n.title}</span>
                      <span className="text-[10px] text-neutral-400 font-normal">{n.time}</span>
                    </div>
                    <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5">
                      {n.desc}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* User Profile Menu */}
        <div className="relative">
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-1.5 pl-1.5 pr-2 py-1 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#17191C] hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors cursor-pointer text-xs"
          >
            <div className="w-6 h-6 rounded-md bg-[#95EB68]/30 dark:bg-[#95EB68]/20 text-[#17191C] dark:text-[#95EB68] font-bold flex items-center justify-center text-[11px]">
              {userEmail.charAt(0).toUpperCase()}
            </div>
            <span className="font-medium text-neutral-700 dark:text-neutral-300 hidden sm:inline max-w-[100px] truncate">
              {userEmail.split('@')[0]}
            </span>
            <ChevronDown size={12} className="text-neutral-400" />
          </button>

          {isProfileOpen && (
            <div
              className="absolute right-0 mt-2 w-52 rounded-xl bg-white dark:bg-[#17191C] border border-neutral-200 dark:border-neutral-800 shadow-xl p-2 z-50 animate-in fade-in zoom-in-95"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="px-2.5 py-2 border-b border-neutral-100 dark:border-neutral-800 mb-1">
                <div className="text-xs font-semibold text-neutral-900 dark:text-white truncate">
                  {userEmail}
                </div>
                <div className="text-[10px] text-neutral-400 mt-0.5">
                  Role: Authorized Purchasing Agent
                </div>
              </div>
              <Link
                to="/settings"
                onClick={() => setIsProfileOpen(false)}
                className="w-full px-2.5 py-1.5 rounded-lg text-xs text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 flex items-center gap-2 transition-colors"
              >
                Settings & Integration
              </Link>
              <Link
                to="/mandate"
                onClick={() => setIsProfileOpen(false)}
                className="w-full px-2.5 py-1.5 rounded-lg text-xs text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 flex items-center gap-2 transition-colors"
              >
                Active Mandate Rules
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
