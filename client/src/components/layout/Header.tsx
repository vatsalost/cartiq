import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Menu,
  Search,
  Bell,
  ShieldCheck,
  User,
  ChevronDown,
} from 'lucide-react'
import { ThemeToggle } from '../common/ThemeToggle'
import { useAuth } from '../../context/AuthContext'

interface HeaderProps {
  pageTitle?: string
  onOpenMobileMenu: () => void
}

export const Header: React.FC<HeaderProps> = ({ onOpenMobileMenu }) => {
  const { userEmail, mandate } = useAuth()
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
      title: 'Proposal Ready',
      desc: 'Nordic Adjustable LED Desk Lamp matches all 8 purchase guardrails',
      time: '10m ago',
    },
    {
      id: '2',
      title: 'Order Completed',
      desc: 'Bodum French Press ($34.99) payment captured via PayPal',
      time: '1h ago',
    },
    {
      id: '3',
      title: 'Mandate Active',
      desc: `Mandate v${mandate?.version || 2} active with $${mandate?.total_budget || '150.00'} budget`,
      time: '2h ago',
    },
  ]

  return (
    <header className="sticky top-0 z-30 h-16 w-full bg-white dark:bg-[#17191C] border-b border-[#E4E7E1] dark:border-neutral-800 px-4 md:px-8 flex items-center justify-between gap-4">
      {/* Left: Mobile menu toggle + Global Search Input */}
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <button
          onClick={onOpenMobileMenu}
          className="lg:hidden p-1.5 rounded-lg text-neutral-500 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800 cursor-pointer"
          aria-label="Open sidebar"
        >
          <Menu size={18} />
        </button>

        <form onSubmit={handleSearchSubmit} className="relative w-full">
          <Search
            size={15}
            className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400"
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search products, orders, or requests..."
            className="w-full bg-[#F5F6F3] dark:bg-[#121316] text-neutral-900 dark:text-white placeholder-neutral-400 text-xs rounded-full pl-9 pr-14 py-2 border border-transparent focus:border-neutral-300 dark:focus:border-neutral-700 outline-hidden transition-all"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-neutral-400 font-medium px-1.5 py-0.5 rounded border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 pointer-events-none">
            Ctrl K
          </div>
        </form>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Mandate Balance Pill */}
        <Link
          to="/mandate"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#ECFADF] dark:bg-[#142617] border border-[#95EB68]/40 dark:border-[#95EB68]/30 text-xs text-[#1D4A18] dark:text-[#95EB68] font-medium hover:brightness-95 transition-all"
          title="View Spending Mandate"
        >
          <ShieldCheck size={14} className="text-[#1D4A18] dark:text-[#95EB68]" />
          <span>Mandate: ${mandate?.total_budget || '150.00'}</span>
        </Link>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsNotifOpen(!isNotifOpen)}
            className="w-9 h-9 rounded-full flex items-center justify-center border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#17191C] text-neutral-600 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800 relative cursor-pointer"
            title="Notifications"
          >
            <Bell size={16} />
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#95EB68]" />
          </button>

          {isNotifOpen && (
            <div
              className="absolute right-0 mt-2 w-72 rounded-2xl bg-white dark:bg-[#17191C] border border-neutral-200 dark:border-neutral-800 shadow-xl p-3 z-50 animate-in fade-in"
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
                    className="p-2.5 rounded-xl bg-neutral-50 dark:bg-neutral-800/50 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-xs transition-colors"
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

        {/* Theme Toggle Button */}
        <ThemeToggle />

        {/* User Profile Pill Menu */}
        <div className="relative">
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-2 pl-1 pr-2.5 py-1 rounded-full border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#17191C] hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors cursor-pointer text-xs"
          >
            <div className="w-7 h-7 rounded-full bg-[#17191C] text-white flex items-center justify-center text-xs">
              <User size={14} />
            </div>
            <span className="font-semibold text-neutral-800 dark:text-neutral-200 hidden sm:inline">
              demo-user
            </span>
            <ChevronDown size={13} className="text-neutral-400" />
          </button>

          {isProfileOpen && (
            <div
              className="absolute right-0 mt-2 w-52 rounded-xl bg-white dark:bg-[#17191C] border border-neutral-200 dark:border-neutral-800 shadow-xl p-2 z-50 animate-in fade-in"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="px-2.5 py-2 border-b border-neutral-100 dark:border-neutral-800 mb-1">
                <div className="text-xs font-semibold text-neutral-900 dark:text-white truncate">
                  {userEmail}
                </div>
                <div className="text-[10px] text-neutral-400 mt-0.5">
                  Authority: Mandate v2
                </div>
              </div>
              <Link
                to="/settings"
                onClick={() => setIsProfileOpen(false)}
                className="w-full px-2.5 py-1.5 rounded-lg text-xs text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 flex items-center gap-2"
              >
                Settings
              </Link>
              <Link
                to="/mandate"
                onClick={() => setIsProfileOpen(false)}
                className="w-full px-2.5 py-1.5 rounded-lg text-xs text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 flex items-center gap-2"
              >
                Spending Mandate
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
