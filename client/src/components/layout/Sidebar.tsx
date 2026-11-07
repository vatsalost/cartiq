import React from 'react'
import { NavLink, Link, useLocation } from 'react-router-dom'
import {
  ShoppingBag,
  FileCheck2,
  Package,
  ShieldCheck,
  History,
  LayoutDashboard,
  Settings,
  X,
  ArrowRight,
  Sparkles,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { mandate, breakdown } = useAuth()
  const location = useLocation()

  // Shopping-first navigation order:
  // 1. Shopping
  // 2. Proposals
  // 3. Orders
  // 4. Mandate
  // 5. Activity
  // 6. Overview
  // (Settings placed separately at bottom)
  const navItems = [
    { name: 'Shopping', path: '/', altPath: '/shopping', icon: ShoppingBag },
    { name: 'Proposals', path: '/proposals', icon: FileCheck2 },
    { name: 'Orders', path: '/orders', icon: Package },
    { name: 'Mandate', path: '/mandate', icon: ShieldCheck },
    { name: 'Activity', path: '/activity', icon: History },
    { name: 'Overview', path: '/overview', altPath: '/dashboard', icon: LayoutDashboard },
  ]

  const isNavActive = (item: (typeof navItems)[0]) => {
    if (item.path === '/') {
      return location.pathname === '/' || location.pathname === '/shopping'
    }
    if (item.altPath && location.pathname === item.altPath) {
      return true
    }
    return location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)
  }

  const isSettingsActive = location.pathname === '/settings' || location.pathname.startsWith('/settings/')

  const availableBudget = parseFloat(breakdown?.available_budget || '65.02')

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs lg:hidden transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Fixed Left Sidebar */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-[230px] bg-[#17191C] text-white border-r border-[#22252B] flex flex-col justify-between transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{
          backgroundImage: 'radial-gradient(circle at bottom left, rgba(149, 235, 104, 0.08), transparent 70%)',
        }}
      >
        {/* Top: Logo & Main Navigation List */}
        <div className="flex flex-col">
          {/* Brand Header - Carti Logo navigates to Shopping */}
          <div className="h-16 px-4 flex items-center justify-between border-b border-[#22252B]">
            <Link
              to="/"
              onClick={onClose}
              className="flex items-center gap-2.5 group cursor-pointer"
              title="Carti - Autonomous AI Shopping Home"
            >
              <div className="w-8 h-8 rounded-lg bg-[#95EB68] flex items-center justify-center text-[#17191C] font-black text-sm tracking-tighter shadow-sm group-hover:scale-105 transition-transform">
                <Sparkles size={20} strokeWidth={1.8} className="text-[#17191C] fill-[#17191C]" />
              </div>
              <div className="flex flex-col">
                <span className="text-base font-bold text-white tracking-tight leading-none">
                  Carti
                </span>
                <span className="text-[10px] text-neutral-400 font-medium tracking-wide mt-0.5">
                  Autonomous AI Purchasing
                </span>
              </div>
            </Link>

            <button
              onClick={onClose}
              className="lg:hidden p-1.5 rounded-md text-neutral-400 hover:text-white hover:bg-neutral-800"
              aria-label="Close navigation"
            >
              <X size={18} />
            </button>
          </div>

          {/* Primary Shopping & Purchasing Workflow Navigation Links */}
          <nav className="p-3 flex flex-col gap-1 mt-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = isNavActive(item)
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  onClick={onClose}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs transition-all font-medium ${
                    active
                      ? 'bg-[#1E301F] text-[#95EB68] font-semibold border border-[#95EB68]/30 shadow-xs'
                      : 'text-neutral-400 hover:text-white hover:bg-neutral-800/60'
                  }`}
                >
                  <Icon size={20} strokeWidth={1.8} className="shrink-0" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Bottom Section: Settings & Mandate Balance */}
        <div className="p-3 border-t border-[#22252B] flex flex-col gap-2">
          {/* Settings Link placed separately at bottom of sidebar */}
          <Link
            to="/settings"
            onClick={onClose}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs transition-all font-medium ${
              isSettingsActive
                ? 'bg-[#1E301F] text-[#95EB68] font-semibold border border-[#95EB68]/30 shadow-xs'
                : 'text-neutral-400 hover:text-white hover:bg-neutral-800/60'
            }`}
          >
            <Settings size={20} strokeWidth={1.8} className="shrink-0" />
            <span>Settings</span>
          </Link>

          {/* Mandate Balance Indicator Card */}
          <Link
            to="/mandate"
            onClick={onClose}
            className="p-3 rounded-xl bg-[#111215] border border-[#262930] hover:border-[#95EB68]/40 transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-2.5">
              <span className="w-2 h-2 rounded-full bg-[#95EB68] shrink-0" />
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-white">
                  Mandate v{mandate?.version || 2}
                </span>
                <span className="text-[11px] text-neutral-400 font-mono tabular-nums">
                  ${availableBudget.toFixed(2)} available
                </span>
              </div>
            </div>
            <ArrowRight size={16} strokeWidth={1.8} className="text-neutral-400 group-hover:text-[#95EB68] group-hover:translate-x-0.5 transition-all" />
          </Link>
        </div>
      </aside>
    </>
  )
}
