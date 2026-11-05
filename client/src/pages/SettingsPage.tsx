import React from 'react'
import {
  Sun,
  Moon,
  Server,
  CreditCard,
  Globe,
  CheckCircle2,
  Shield,
  User,
} from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { Badge } from '../components/common/Badge'

export const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useTheme()
  const { userEmail, userId, backendConnected } = useAuth()

  const services = [
    {
      name: 'Carti API Backend',
      description: 'Request routing, mandate enforcement & payment capture',
      status: backendConnected ? 'Connected (localhost:8000)' : 'Offline / Standalone Preview',
      icon: Server,
      active: backendConnected,
    },
    {
      name: 'PayPal Sandbox API',
      description: 'Order authorization & payment captures',
      status: 'Active (sandbox.paypal.com)',
      icon: CreditCard,
      active: true,
    },
    {
      name: 'Product Catalog Service',
      description: 'Retailer catalog indexing & search',
      status: 'Active',
      icon: Globe,
      active: true,
    },
    {
      name: 'Retailer Verification Engine',
      description: 'Automated stock & live price verification',
      status: 'Active',
      icon: Shield,
      active: true,
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg md:text-xl font-bold text-neutral-900 dark:text-white tracking-tight">
          Settings
        </h2>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
          Theme preferences, session info, and service connectivity
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Appearance Settings */}
        <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-[#16181D] border border-neutral-200 dark:border-neutral-800 shadow-xs flex flex-col gap-4">
          <h3 className="text-sm font-bold text-neutral-900 dark:text-white pb-2 border-b border-neutral-100 dark:border-neutral-800">
            Appearance
          </h3>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setTheme('light')}
              className={`p-3.5 rounded-xl border transition-all text-left flex flex-col justify-between min-h-[85px] cursor-pointer ${
                theme === 'light'
                  ? 'bg-neutral-100 border-neutral-900 text-neutral-900'
                  : 'bg-white dark:bg-neutral-800/40 border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400'
              }`}
            >
              <div className="flex items-center justify-between">
                <Sun size={16} className="text-amber-500" />
                {theme === 'light' && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-neutral-900 text-white">
                    Active
                  </span>
                )}
              </div>
              <div>
                <div className="text-xs font-bold mt-2">Light Theme</div>
                <div className="text-[11px] text-neutral-400">Off-white & lime green</div>
              </div>
            </button>

            <button
              onClick={() => setTheme('dark')}
              className={`p-3.5 rounded-xl border transition-all text-left flex flex-col justify-between min-h-[85px] cursor-pointer ${
                theme === 'dark'
                  ? 'bg-[#121316] border-[#2CE5B5] text-white'
                  : 'bg-white dark:bg-neutral-800/40 border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400'
              }`}
            >
              <div className="flex items-center justify-between">
                <Moon size={16} className="text-[#2CE5B5]" />
                {theme === 'dark' && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#2CE5B5] text-[#05261F]">
                    Active
                  </span>
                )}
              </div>
              <div>
                <div className="text-xs font-bold mt-2">Dark Theme</div>
                <div className="text-[11px] text-neutral-400">Near-black & neon teal</div>
              </div>
            </button>
          </div>
        </div>

        {/* Account & Session */}
        <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-[#16181D] border border-neutral-200 dark:border-neutral-800 shadow-xs flex flex-col justify-between gap-4">
          <div className="flex flex-col gap-3">
            <h3 className="text-sm font-bold text-neutral-900 dark:text-white pb-2 border-b border-neutral-100 dark:border-neutral-800">
              Account & Session
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span className="text-neutral-500">Email</span>
                <span className="font-semibold text-neutral-900 dark:text-white">{userEmail}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span className="text-neutral-500">User ID</span>
                <span className="font-mono text-[11px] text-neutral-500">{userId.slice(0, 18)}...</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-neutral-500">Permissions</span>
                <span className="font-medium text-emerald-600 dark:text-emerald-400">
                  Authorized Sandbox Access
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Service Connectivity */}
      <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-[#16181D] border border-neutral-200 dark:border-neutral-800 shadow-xs flex flex-col gap-4">
        <h3 className="text-sm font-bold text-neutral-900 dark:text-white pb-2 border-b border-neutral-100 dark:border-neutral-800">
          Service Connectivity
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {services.map((item, idx) => {
            const Icon = item.icon
            return (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800 flex items-start gap-3"
              >
                <div className="w-8 h-8 rounded-lg bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-neutral-700 dark:text-neutral-300 shrink-0">
                  <Icon size={16} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-neutral-900 dark:text-white">
                      {item.name}
                    </span>
                    <Badge variant={item.active ? 'success' : 'warning'} size="sm">
                      {item.active ? 'Connected' : 'Offline'}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5 truncate">
                    {item.description}
                  </div>
                  <div className="text-[10px] font-mono text-neutral-400 mt-1">
                    {item.status}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
