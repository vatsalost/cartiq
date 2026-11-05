import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Bot,
  ShieldAlert,
  FileCheck2,
  ShoppingBag,
  History,
  Settings,
} from 'lucide-react'

export const BottomDock: React.FC = () => {
  const dockItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Shopping', path: '/shopping', icon: Bot },
    { name: 'Mandate', path: '/mandate', icon: ShieldAlert },
    { name: 'Proposals', path: '/proposals', icon: FileCheck2 },
    { name: 'Orders', path: '/orders', icon: ShoppingBag },
    { name: 'History', path: '/history', icon: History },
    { name: 'Settings', path: '/settings', icon: Settings },
  ]

  return (
    <aside
      aria-label="Bottom Navigation Dock"
      className="fixed bottom-5 left-1/2 -translate-x-1/2 z-40"
    >
      <div className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#111215] text-white border border-neutral-800 shadow-[0_12px_36px_rgba(0,0,0,0.45)] backdrop-blur-md">
        {/* Brand Name on Left */}
        <div className="flex items-center gap-1.5 pr-4 border-r border-neutral-800 font-extrabold tracking-tight text-sm select-none text-white">
          <span className="w-2.5 h-2.5 rounded-full bg-[#98EC6A] dark:bg-[#2CE5B5] inline-block animate-pulse" />
          <span>Carti</span>
        </div>

        {/* Navigation Icon Buttons */}
        <div className="flex items-center gap-1 sm:gap-2">
          {dockItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                title={item.name}
                className={({ isActive }) =>
                  `relative p-2 rounded-xl transition-all duration-150 flex items-center justify-center cursor-pointer ${
                    isActive
                      ? 'bg-[#98EC6A] dark:bg-[#2CE5B5] text-[#0A2610] dark:text-[#05261F] shadow-[0_2px_8px_rgba(152,236,106,0.3)] dark:shadow-[0_2px_8px_rgba(44,229,181,0.3)] font-bold scale-105'
                      : 'text-neutral-400 hover:text-white hover:bg-neutral-800/80'
                  }`
                }
              >
                <Icon size={18} />
              </NavLink>
            )
          })}
        </div>
      </div>
    </aside>
  )
}
