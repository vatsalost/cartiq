import React, { useState } from 'react'
import { NavLink, useNavigate, Link } from 'react-router-dom'
import { Search, Bell, Shield, ShoppingBag, User, ChevronDown } from 'lucide-react'
import { ThemeToggle } from '../common/ThemeToggle'
import { useAuth } from '../../context/AuthContext'

export const Header: React.FC<{ pageTitle?: string }> = ({ pageTitle = 'Shopping Concierge' }) => {
  const { userEmail, mandate } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const navigate = useNavigate()

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/shopping?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  const navTabs = [
    { name: 'Dashboard', path: '/' },
    { name: 'Shopping', path: '/shopping' },
    { name: 'Spending Mandate', path: '/mandate' },
    { name: 'Proposals', path: '/proposals' },
    { name: 'Orders', path: '/orders' },
    { name: 'History & Audit', path: '/history' },
    { name: 'Settings', path: '/settings' },
  ]

  return (
    <header className="w-full flex flex-col gap-4 pb-4 border-b border-neutral-200/70 dark:border-neutral-800">
      {/* Top Header Row */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Brand & Page Heading */}
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="w-9 h-9 rounded-xl bg-[#98EC6A] dark:bg-[#2CE5B5] flex items-center justify-center text-[#0A2610] dark:text-[#05261F] font-black text-sm tracking-tighter"
            title="Carti Concierge"
          >
            C
          </Link>
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-neutral-900 dark:text-white tracking-tight">
              {pageTitle}
            </h1>
          </div>
        </div>

        {/* Action Controls & Profile */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Pill Search Bar */}
          <form onSubmit={handleSearchSubmit} className="relative min-w-[200px] max-w-xs">
            <Search
              size={15}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search products, orders..."
              className="w-full bg-neutral-50 dark:bg-[#1A1D23] text-neutral-900 dark:text-white placeholder-neutral-400 text-xs rounded-full pl-9 pr-4 py-2 border border-neutral-200 dark:border-neutral-700/80 focus:outline-hidden focus:ring-2 focus:ring-neutral-300 dark:focus:ring-neutral-700"
            />
          </form>

          {/* Mandate Summary Badge */}
          {mandate && (
            <Link
              to="/mandate"
              className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-xs text-neutral-700 dark:text-neutral-300 font-medium hover:border-neutral-300 dark:hover:border-neutral-600 transition-colors"
            >
              <Shield size={13} className="text-[#98EC6A] dark:text-[#2CE5B5]" />
              <span>
                Budget: ${mandate.total_budget} {mandate.currency}
              </span>
            </Link>
          )}

          {/* Notification Button */}
          <button
            className="w-8 h-8 rounded-full flex items-center justify-center bg-white dark:bg-[#1A1D23] border border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800 relative cursor-pointer"
            title="Notifications"
          >
            <Bell size={15} />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[#98EC6A] dark:bg-[#2CE5B5]" />
          </button>

          {/* Theme Switcher */}
          <ThemeToggle />

          {/* User Profile Pill */}
          <div className="flex items-center gap-2 pl-1.5 pr-3 py-1 rounded-full bg-white dark:bg-[#1A1D23] border border-neutral-200 dark:border-neutral-700">
            <div className="w-6 h-6 rounded-full bg-neutral-200 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 flex items-center justify-center font-bold text-xs">
              <User size={13} />
            </div>
            <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300 hidden sm:inline max-w-[120px] truncate">
              {userEmail.split('@')[0]}
            </span>
          </div>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <nav className="flex items-center gap-6 overflow-x-auto pt-1 no-scrollbar border-t border-neutral-100 dark:border-neutral-800/80">
        {navTabs.map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path}
            end={tab.path === '/'}
            className={({ isActive }) =>
              `text-xs sm:text-sm pt-2 pb-2 whitespace-nowrap transition-colors relative cursor-pointer ${
                isActive
                  ? 'font-bold text-neutral-900 dark:text-white border-b-2 border-neutral-900 dark:border-[#2CE5B5]'
                  : 'font-medium text-neutral-500 dark:text-neutral-400 hover:text-neutral-800 dark:hover:text-neutral-200'
              }`
            }
          >
            {tab.name}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}
