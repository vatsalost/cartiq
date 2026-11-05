import React from 'react'
import {
  Settings as SettingsIcon,
  Shield,
  Sun,
  Moon,
  Laptop,
  CheckCircle2,
  AlertTriangle,
  Server,
  CreditCard,
  Globe,
  Sparkles,
} from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { Button } from '../components/common/Button'
import { Badge } from '../components/common/Badge'

export const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useTheme()
  const { userEmail, userId, backendConnected } = useAuth()

  const integrations = [
    {
      name: 'Carti FastAPI Backend',
      service: 'Modules B1–B10 Orchestration Layer',
      status: backendConnected ? 'Connected (localhost:8000)' : 'Mock Mode (Standalone)',
      icon: Server,
      active: backendConnected,
    },
    {
      name: 'PayPal Sandbox v2 API',
      service: 'Orders v2 & Payments Captures / Refunds',
      status: 'Active (sandbox.paypal.com)',
      icon: CreditCard,
      active: true,
    },
    {
      name: 'Channel3 Product Catalog',
      service: 'Retailer Catalog Index & Multi-offer Aggregator',
      status: 'Active (Mock Adapter Mode)',
      icon: Globe,
      active: true,
    },
    {
      name: 'KERNEL Browser Verification',
      service: 'Automated Headless Cart & Retailer Stock Verification',
      status: 'Active (B9 Kernel Verification Service)',
      icon: Sparkles,
      active: true,
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl md:text-2xl font-black text-neutral-900 dark:text-white tracking-tight flex items-center gap-2">
          <span>Application Settings & System Integrations</span>
        </h2>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
          Carti environment preferences, theme selection, and service connectivity
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Profile Card */}
        <div className="rounded-[28px] p-6 bg-white dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800 shadow-[0_4px_24px_rgba(0,0,0,0.03)] flex flex-col justify-between gap-4">
          <div className="flex flex-col gap-3">
            <h3 className="text-base font-extrabold text-neutral-900 dark:text-white pb-3 border-b border-neutral-100 dark:border-neutral-800">
              Authenticated Session (B2)
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span className="text-neutral-500">Email Address</span>
                <span className="font-semibold text-neutral-900 dark:text-white">{userEmail}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span className="text-neutral-500">User UUID</span>
                <span className="font-mono text-[11px] text-neutral-400">{userId}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-100 dark:border-neutral-800">
                <span className="text-neutral-500">Demo User Authority</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                  Full Authorized Sandbox Access
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-neutral-500">Authentication Method</span>
                <span className="font-medium text-neutral-700 dark:text-neutral-300">
                  Bearer Token Session
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Visual Theme Selection matching reference screenshots */}
        <div className="rounded-[28px] p-6 bg-white dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800 shadow-[0_4px_24px_rgba(0,0,0,0.03)] flex flex-col gap-4">
          <h3 className="text-base font-extrabold text-neutral-900 dark:text-white pb-3 border-b border-neutral-100 dark:border-neutral-800">
            Appearance & Visual Theme
          </h3>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            Reproduces the exact design language of the Light and Dark theme reference screenshots.
          </p>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <button
              onClick={() => setTheme('light')}
              className={`p-4 rounded-2xl border transition-all text-left flex flex-col justify-between min-h-[90px] cursor-pointer ${
                theme === 'light'
                  ? 'bg-neutral-100 border-neutral-900 text-neutral-900 shadow-xs'
                  : 'bg-white dark:bg-neutral-800/40 border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400'
              }`}
            >
              <div className="flex items-center justify-between">
                <Sun size={18} className="text-amber-500" />
                {theme === 'light' && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-neutral-900 text-white">
                    Active
                  </span>
                )}
              </div>
              <div>
                <div className="text-xs font-bold mt-2">Light Theme</div>
                <div className="text-[10px] text-neutral-400">Off-white & Lime green</div>
              </div>
            </button>

            <button
              onClick={() => setTheme('dark')}
              className={`p-4 rounded-2xl border transition-all text-left flex flex-col justify-between min-h-[90px] cursor-pointer ${
                theme === 'dark'
                  ? 'bg-[#121316] border-[#2CE5B5] text-white shadow-xs'
                  : 'bg-white dark:bg-neutral-800/40 border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400'
              }`}
            >
              <div className="flex items-center justify-between">
                <Moon size={18} className="text-[#2CE5B5]" />
                {theme === 'dark' && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#2CE5B5] text-[#05261F]">
                    Active
                  </span>
                )}
              </div>
              <div>
                <div className="text-xs font-bold mt-2">Dark Theme</div>
                <div className="text-[10px] text-neutral-400">Near-black & Vibrant Teal</div>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Integration Status Table */}
      <div className="rounded-[28px] p-6 md:p-8 bg-white dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800 shadow-[0_4px_24px_rgba(0,0,0,0.03)] flex flex-col gap-4">
        <h3 className="text-base font-extrabold text-neutral-900 dark:text-white pb-3 border-b border-neutral-100 dark:border-neutral-800">
          Core Module Service Connectivity
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {integrations.map((item, idx) => {
            const Icon = item.icon
            return (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-neutral-50/80 dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800 flex items-start gap-3.5"
              >
                <div className="w-10 h-10 rounded-xl bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-neutral-700 dark:text-neutral-300 shrink-0">
                  <Icon size={18} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-neutral-900 dark:text-white">
                      {item.name}
                    </span>
                    <Badge variant={item.active ? 'success' : 'warning'} size="sm">
                      {item.active ? 'Live' : 'Standby'}
                    </Badge>
                  </div>
                  <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                    {item.service}
                  </div>
                  <div className="text-[11px] font-mono text-neutral-400 mt-1">
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
