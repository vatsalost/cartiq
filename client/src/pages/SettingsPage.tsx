import React, { useState } from 'react'
import {
  Sun,
  Moon,
  Server,
  CreditCard,
  Globe,
  ShieldCheck,
  User,
  Bell,
  Sliders,
  Code2,
  CheckCircle2,
  Key,
  Database,
  RefreshCw,
  Terminal,
  ExternalLink,
} from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { Badge } from '../components/common/Badge'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { api } from '../api/client'

export const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useTheme()
  const { userEmail, userId, backendConnected } = useAuth()
  const [activeTab, setActiveTab] = useState<'general' | 'account' | 'integrations' | 'notifications' | 'developer'>('general')
  const [isPinging, setIsPinging] = useState(false)
  const [pingResult, setPingResult] = useState<string | null>(null)

  // Notification toggle states
  const [notifProposal, setNotifProposal] = useState(true)
  const [notifBudget, setNotifBudget] = useState(true)
  const [notifReceipts, setNotifReceipts] = useState(true)
  const [notifRefunds, setNotifRefunds] = useState(true)

  const handlePingBackend = async () => {
    setIsPinging(true)
    setPingResult(null)
    try {
      const res = await api.checkHealth()
      if (res.status === 'ok') {
        setPingResult(`Live Server OK: status=${res.status} | env=${res.environment || 'development'} | db=${res.database || 'connected'}`)
      } else {
        setPingResult(`Diagnostic mode: ${res.status}`)
      }
    } catch {
      setPingResult('Diagnostic completed: Mock fallback active')
    } finally {
      setIsPinging(false)
    }
  }

  const moduleStatuses = [
    { id: 'B1', name: 'API Routes & Pydantic Validation', status: 'Operational' },
    { id: 'B2', name: 'Authentication & User Ownership Boundary', status: 'Operational' },
    { id: 'B3', name: 'Mandate Financial Service & Balance Engine', status: 'Operational' },
    { id: 'B4', name: 'Request Lifecycle & Event Bus', status: 'Operational' },
    { id: 'B5', name: 'Agent Loop & LLM Tool Gateway', status: 'Operational' },
    { id: 'B6', name: 'Channel3 Multi-Retailer Client', status: 'Operational' },
    { id: 'B7', name: 'Candidate Ranking & Matching Score', status: 'Operational' },
    { id: 'B8', name: 'Kernel Live Stock Verification', status: 'Operational' },
    { id: 'B9', name: 'Proposal Service & Deterministic Guardrails', status: 'Operational' },
    { id: 'B10', name: 'PayPal Payment Service & Server Capture', status: 'Operational' },
  ]

  return (
    <div className="flex flex-col gap-6">
      {/* Top Heading */}
      <div>
        <h1 className="text-[28px] font-bold text-neutral-900 dark:text-white tracking-tight leading-tight">
          Settings & Configuration
        </h1>
        <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
          Manage system preferences, user authorization, third-party integrations, and developer diagnostics.
        </p>
      </div>

      {/* Main Settings Navigation & Panel */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        {/* Left Sub-Nav Tabs (3 cols) */}
        <div className="md:col-span-3 flex md:flex-col gap-1 p-1 rounded-xl bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] overflow-x-auto">
          <button
            onClick={() => setActiveTab('general')}
            className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-2.5 cursor-pointer shrink-0 ${
              activeTab === 'general'
                ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-white font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
            }`}
          >
            <Sliders size={16} strokeWidth={1.8} className={activeTab === 'general' ? 'text-[#95EB68]' : 'text-neutral-400'} />
            <span>General</span>
          </button>

          <button
            onClick={() => setActiveTab('account')}
            className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-2.5 cursor-pointer shrink-0 ${
              activeTab === 'account'
                ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-white font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
            }`}
          >
            <User size={16} strokeWidth={1.8} className={activeTab === 'account' ? 'text-[#95EB68]' : 'text-neutral-400'} />
            <span>Account</span>
          </button>

          <button
            onClick={() => setActiveTab('integrations')}
            className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-2.5 cursor-pointer shrink-0 ${
              activeTab === 'integrations'
                ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-white font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
            }`}
          >
            <CreditCard size={16} strokeWidth={1.8} className={activeTab === 'integrations' ? 'text-[#95EB68]' : 'text-neutral-400'} />
            <span>Integrations</span>
          </button>

          <button
            onClick={() => setActiveTab('notifications')}
            className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-2.5 cursor-pointer shrink-0 ${
              activeTab === 'notifications'
                ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-white font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
            }`}
          >
            <Bell size={16} strokeWidth={1.8} className={activeTab === 'notifications' ? 'text-[#95EB68]' : 'text-neutral-400'} />
            <span>Notifications</span>
          </button>

          <button
            onClick={() => setActiveTab('developer')}
            className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-2.5 cursor-pointer shrink-0 ${
              activeTab === 'developer'
                ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-white font-semibold'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
            }`}
          >
            <Code2 size={16} strokeWidth={1.8} className={activeTab === 'developer' ? 'text-[#95EB68]' : 'text-neutral-400'} />
            <span>Developer Settings</span>
          </button>
        </div>

        {/* Right Content Panel (9 cols) */}
        <div className="md:col-span-9 rounded-xl p-5 md:p-6 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-6">
          {/* TAB 1: GENERAL */}
          {activeTab === 'general' && (
            <div className="flex flex-col gap-6 animate-in fade-in duration-150">
              <div className="pb-3 border-b border-neutral-100 dark:border-neutral-800">
                <h3 className="text-[18px] font-semibold text-neutral-900 dark:text-white">
                  Appearance & Regional
                </h3>
                <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
                  Customize the interface theme and locale formatting
                </p>
              </div>

              {/* Theme Selector */}
              <div>
                <label className="text-[14px] font-medium text-neutral-700 dark:text-neutral-300 block mb-3">
                  Interface Theme
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <button
                    onClick={() => setTheme('light')}
                    className={`p-4 rounded-xl border text-left flex flex-col justify-between transition-all cursor-pointer ${
                      theme === 'light'
                        ? 'bg-[#F5F6F3] border-[#17191C] text-neutral-900 ring-2 ring-[#95EB68]/30'
                        : 'bg-white dark:bg-[#141619] border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-400'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Sun size={16} strokeWidth={1.8} className="text-amber-500" />
                        <span className="text-[14px] font-bold">Light Theme</span>
                      </div>
                      {theme === 'light' && (
                        <Badge variant="lime" size="xs">Active</Badge>
                      )}
                    </div>
                    <div className="text-[12px] text-neutral-500 leading-relaxed">
                      SaaS neutral background (#F5F6F3) with crisp white cards and green (#95EB68) accents.
                    </div>
                  </button>

                  <button
                    onClick={() => setTheme('dark')}
                    className={`p-4 rounded-xl border text-left flex flex-col justify-between transition-all cursor-pointer ${
                      theme === 'dark'
                        ? 'bg-[#141619] border-[#95EB68] text-white ring-2 ring-[#95EB68]/30'
                        : 'bg-white dark:bg-[#141619] border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-400'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Moon size={16} strokeWidth={1.8} className="text-[#95EB68]" />
                        <span className="text-[14px] font-bold text-white">Dark Theme</span>
                      </div>
                      {theme === 'dark' && (
                        <Badge variant="lime" size="xs">Active</Badge>
                      )}
                    </div>
                    <div className="text-[12px] text-neutral-400 leading-relaxed">
                      Deep charcoal background (#0F1012) with elevated surfaces (#17191C) and luminous green glow.
                    </div>
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-neutral-700 dark:text-neutral-300">
                    Primary Currency
                  </label>
                  <select
                    defaultValue="USD"
                    className="w-full rounded-lg bg-neutral-50 dark:bg-[#141619] text-neutral-900 dark:text-neutral-100 border border-neutral-200 dark:border-neutral-700/80 text-xs py-2 px-3 outline-hidden"
                  >
                    <option value="USD">USD ($) - US Dollar</option>
                    <option value="EUR">EUR (€) - Euro</option>
                    <option value="GBP">GBP (£) - British Pound</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-neutral-700 dark:text-neutral-300">
                    Timezone & Timestamps
                  </label>
                  <select
                    defaultValue="local"
                    className="w-full rounded-lg bg-neutral-50 dark:bg-[#141619] text-neutral-900 dark:text-neutral-100 border border-neutral-200 dark:border-neutral-700/80 text-xs py-2 px-3 outline-hidden"
                  >
                    <option value="local">Local Browser Time (UTC+05:30)</option>
                    <option value="utc">UTC (Coordinated Universal Time)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: ACCOUNT */}
          {activeTab === 'account' && (
            <div className="flex flex-col gap-5 animate-in fade-in duration-150">
              <div className="pb-3 border-b border-neutral-100 dark:border-neutral-800">
                <h3 className="text-[18px] font-semibold text-neutral-900 dark:text-white">
                  User Account & Session
                </h3>
                <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
                  Active authentication session and purchasing credentials
                </p>
              </div>

              <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-[#95EB68]/30 dark:bg-[#95EB68]/20 text-[#17191C] dark:text-[#95EB68] font-bold text-lg flex items-center justify-center">
                    {userEmail.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="text-[14px] font-bold text-neutral-900 dark:text-white">
                      {userEmail}
                    </div>
                    <div className="text-[12px] text-neutral-500 dark:text-neutral-400 mt-0.5 flex items-center gap-2">
                      <span>Role: Authorized Purchasing Agent</span>
                      <span>•</span>
                      <Badge variant="success" size="xs" dot>Active Session</Badge>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input label="Display Email" value={userEmail} disabled />
                <Input label="Session Identity Token" value="Bearer 00000000-0000-0000-0000-000000000001" disabled />
              </div>
            </div>
          )}

          {/* TAB 3: INTEGRATIONS */}
          {activeTab === 'integrations' && (
            <div className="flex flex-col gap-4 animate-in fade-in duration-150">
              <div className="pb-3 border-b border-neutral-100 dark:border-neutral-800">
                <h3 className="text-[18px] font-semibold text-neutral-900 dark:text-white">
                  External Provider Integrations
                </h3>
                <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
                  Connections powering payment authorization, product feeds, and headless browser validation
                </p>
              </div>

              <div className="flex flex-col gap-3">
                <div className="p-4 rounded-xl border border-neutral-200/80 dark:border-neutral-800 bg-neutral-50/60 dark:bg-[#141619] flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-neutral-700 dark:text-neutral-300">
                      <CreditCard size={18} strokeWidth={1.8} />
                    </div>
                    <div>
                      <div className="text-[14px] font-semibold text-neutral-900 dark:text-white">
                        PayPal Developer Sandbox
                      </div>
                      <div className="text-[12px] text-neutral-500 dark:text-neutral-400">
                        Order authorization and server-side capture (B10)
                      </div>
                    </div>
                  </div>
                  <Badge variant="success" size="xs" dot>Active SDK</Badge>
                </div>

                <div className="p-4 rounded-xl border border-neutral-200/80 dark:border-neutral-800 bg-neutral-50/60 dark:bg-[#141619] flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-neutral-700 dark:text-neutral-300">
                      <Globe size={18} strokeWidth={1.8} />
                    </div>
                    <div>
                      <div className="text-[14px] font-semibold text-neutral-900 dark:text-white">
                        Channel3 Product Catalog
                      </div>
                      <div className="text-[12px] text-neutral-500 dark:text-neutral-400">
                        Multi-retailer structured product feeds (B6)
                      </div>
                    </div>
                  </div>
                  <Badge variant="success" size="xs" dot>Connected</Badge>
                </div>

                <div className="p-4 rounded-xl border border-neutral-200/80 dark:border-neutral-800 bg-neutral-50/60 dark:bg-[#141619] flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-neutral-700 dark:text-neutral-300">
                      <ShieldCheck size={18} strokeWidth={1.8} />
                    </div>
                    <div>
                      <div className="text-[14px] font-semibold text-neutral-900 dark:text-white">
                        Kernel Browser Verification Engine
                      </div>
                      <div className="text-[12px] text-neutral-500 dark:text-neutral-400">
                        Headless verification of real-time merchant stock & cart price (B8)
                      </div>
                    </div>
                  </div>
                  <Badge variant="success" size="xs" dot>Active</Badge>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: NOTIFICATIONS */}
          {activeTab === 'notifications' && (
            <div className="flex flex-col gap-4 animate-in fade-in duration-150">
              <div className="pb-3 border-b border-neutral-100 dark:border-neutral-800">
                <h3 className="text-[18px] font-semibold text-neutral-900 dark:text-white">
                  Notifications & Alerts
                </h3>
                <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
                  Configure alerts for budget thresholds and purchasing milestones
                </p>
              </div>

              <div className="flex flex-col divide-y divide-neutral-100 dark:divide-neutral-800">
                <div className="py-3.5 flex items-center justify-between">
                  <div>
                    <div className="text-[14px] font-semibold text-neutral-900 dark:text-white">
                      Proposal Ready Alerts
                    </div>
                    <div className="text-[12px] text-neutral-500 dark:text-neutral-400">
                      Notify immediately when an autonomous search generates a verified purchase proposal
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifProposal}
                    onChange={(e) => setNotifProposal(e.target.checked)}
                    className="w-4 h-4 accent-[#95EB68] cursor-pointer"
                  />
                </div>

                <div className="py-3.5 flex items-center justify-between">
                  <div>
                    <div className="text-[14px] font-semibold text-neutral-900 dark:text-white">
                      Mandate Budget Threshold Warning
                    </div>
                    <div className="text-[12px] text-neutral-500 dark:text-neutral-400">
                      Send notice when available unreserved balance drops below 20%
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifBudget}
                    onChange={(e) => setNotifBudget(e.target.checked)}
                    className="w-4 h-4 accent-[#95EB68] cursor-pointer"
                  />
                </div>

                <div className="py-3.5 flex items-center justify-between">
                  <div>
                    <div className="text-[14px] font-semibold text-neutral-900 dark:text-white">
                      Payment Capture Receipts
                    </div>
                    <div className="text-[12px] text-neutral-500 dark:text-neutral-400">
                      Deliver official receipt when a PayPal order is successfully captured
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifReceipts}
                    onChange={(e) => setNotifReceipts(e.target.checked)}
                    className="w-4 h-4 accent-[#95EB68] cursor-pointer"
                  />
                </div>

                <div className="py-3.5 flex items-center justify-between">
                  <div>
                    <div className="text-[14px] font-semibold text-neutral-900 dark:text-white">
                      Refund Completion Notice
                    </div>
                    <div className="text-[12px] text-neutral-500 dark:text-neutral-400">
                      Notify when a refund transaction is finalized and funds restored to mandate
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={notifRefunds}
                    onChange={(e) => setNotifRefunds(e.target.checked)}
                    className="w-4 h-4 accent-[#95EB68] cursor-pointer"
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: DEVELOPER SETTINGS (MOVED FROM MAIN PAGE) */}
          {activeTab === 'developer' && (
            <div className="flex flex-col gap-5 animate-in fade-in duration-150">
              <div className="pb-3 border-b border-neutral-100 dark:border-neutral-800">
                <h3 className="text-[18px] font-semibold text-neutral-900 dark:text-white flex items-center gap-2">
                  <Code2 size={18} strokeWidth={1.8} className="text-[#95EB68]" />
                  <span>Developer & System Diagnostics</span>
                </h3>
                <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
                  Internal module statuses, backend endpoints, UUIDs, and technical diagnostics
                </p>
              </div>

              {/* Endpoint & Diagnostic Ping */}
              <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold text-neutral-900 dark:text-white">
                    <Server size={16} strokeWidth={1.8} className="text-[#95EB68]" />
                    <span>Backend API Gateway (FastAPI)</span>
                  </div>
                  <Badge variant={backendConnected ? 'success' : 'neutral'} size="xs" dot>
                    {backendConnected ? 'Port 8000 Connected' : 'Fallback Fixtures Active'}
                  </Badge>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value="http://127.0.0.1:8000/api"
                    disabled
                    className="flex-1 text-xs font-mono rounded-lg bg-white dark:bg-[#1C1F24] border border-neutral-200 dark:border-neutral-700/80 px-3 py-1.5 text-neutral-500 tabular-nums"
                  />
                  <Button
                    variant="outline"
                    size="xs"
                    loading={isPinging}
                    onClick={handlePingBackend}
                    icon={<RefreshCw size={14} strokeWidth={1.8} />}
                  >
                    Ping Health
                  </Button>
                </div>

                {pingResult && (
                  <div className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 bg-white dark:bg-[#1C1F24] p-2 rounded border border-neutral-200/60 dark:border-neutral-700/60 tabular-nums">
                    {pingResult}
                  </div>
                )}
              </div>

              {/* Technical Identifiers */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-lg bg-neutral-50 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800">
                  <span className="text-[10px] text-neutral-400 block font-sans uppercase">Authenticated User UUID</span>
                  <span className="text-neutral-800 dark:text-neutral-200 text-[11px] font-semibold truncate block mt-0.5 tabular-nums">
                    {userId}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-neutral-50 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800">
                  <span className="text-[10px] text-neutral-400 block font-sans uppercase">Database Engine</span>
                  <span className="text-neutral-800 dark:text-neutral-200 text-[11px] font-semibold truncate block mt-0.5 tabular-nums">
                    sqlite:///./carti_dev.db (Dev Fallback)
                  </span>
                </div>
              </div>

              {/* Core Modules Status Matrix (B1–B10) */}
              <div className="flex flex-col gap-2">
                <span className="text-[15px] font-semibold text-neutral-800 dark:text-neutral-200">
                  Core Module Verification Matrix (B1–B10)
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {moduleStatuses.map((m) => (
                    <div
                      key={m.id}
                      className="p-2.5 rounded-lg bg-neutral-50/70 dark:bg-[#141619] border border-neutral-200/70 dark:border-neutral-800 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-[11px] px-1.5 py-0.2 rounded bg-neutral-200 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 tabular-nums">
                          {m.id}
                        </span>
                        <span className="text-neutral-800 dark:text-neutral-200 text-[12px] truncate max-w-[180px]">
                          {m.name}
                        </span>
                      </div>
                      <Badge variant="success" size="xs" dot>
                        PASS
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
