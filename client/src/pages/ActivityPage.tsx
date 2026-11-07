import React, { useEffect, useState } from 'react'
import {
  History,
  FileText,
  Scale,
  ShoppingBag,
  Search,
  ExternalLink,
  CheckCircle2,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Copy,
  Check,
  Clock,
  Sparkles,
  GitCommit,
} from 'lucide-react'
import { api } from '../api/client'
import { ShoppingRequest, CandidateProduct, Order, AuditEvent } from '../api/types'
import {
  mockRequests,
  mockCandidateProducts,
  mockOrders,
  mockAuditTimeline,
} from '../api/mockData'
import { Badge } from '../components/common/Badge'
import { Button } from '../components/common/Button'

export const ActivityPage: React.FC = () => {
  const [requests, setRequests] = useState<ShoppingRequest[]>(mockRequests)
  const [candidates, setCandidates] = useState<CandidateProduct[]>(mockCandidateProducts)
  const [orders, setOrders] = useState<Order[]>(mockOrders)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>(mockAuditTimeline)

  const [activeTab, setActiveTab] = useState<'requests' | 'comparisons' | 'orders' | 'timeline'>('requests')
  const [selectedRequestId, setSelectedRequestId] = useState<string>(mockRequests[0]?.id || 'req_lamp_001')
  const [rightSubTab, setRightSubTab] = useState<'timeline' | 'details' | 'candidates'>('timeline')
  const [isRecordExpanded, setIsRecordExpanded] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [dateFilter, setDateFilter] = useState('30days')
  const [copiedHash, setCopiedHash] = useState<string | null>(null)

  useEffect(() => {
    async function loadHistory() {
      try {
        const [ordersRes, timelineRes] = await Promise.all([
          api.listOrders().catch(() => ({ items: mockOrders, total: mockOrders.length })),
          api.getAuditTimeline().catch(() => mockAuditTimeline),
        ])
        if (ordersRes.items && ordersRes.items.length > 0) {
          setOrders(ordersRes.items)
        }
        if (timelineRes && timelineRes.length > 0) {
          setAuditEvents(timelineRes)
        }
      } catch {
        // Fallback to mock state
      }
    }
    loadHistory()
  }, [])

  const selectedRequest = requests.find((r) => r.id === selectedRequestId) || requests[0]

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    setCopiedHash(label)
    setTimeout(() => setCopiedHash(null), 2000)
  }

  // Pre-configured realistic audit timeline events for selected request
  const requestTimelineEvents = [
    {
      title: 'Shopping request created',
      desc: `User submitted: "${selectedRequest?.prompt || 'Find me a warm-light desk lamp under $50 with a matte finish.'}"`,
      time: 'Nov 7, 11:06 AM',
      status: 'completed',
    },
    {
      title: 'Products discovered & compared',
      desc: 'Scanned retailer catalogs and evaluated 3 candidate products.',
      time: 'Nov 7, 11:06 AM',
      status: 'completed',
    },
    {
      title: 'Mandate validation passed',
      desc: 'Category, budget (≤ $60) and retailer rules verified.',
      time: 'Nov 7, 11:07 AM',
      status: 'completed',
    },
    {
      title: 'Stock verification',
      desc: 'Confirmed availability at target.com.',
      time: 'Nov 7, 11:07 AM',
      status: 'completed',
    },
    {
      title: 'Proposal generated',
      desc: 'Purchase proposal ready for your review and approval.',
      time: 'Nov 7, 11:07 AM',
      status: 'pending',
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      {/* Header section with Icon */}
      <div className="flex items-start gap-3.5">
        <div className="w-10 h-10 rounded-xl bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0">
          <History size={20} strokeWidth={1.8} />
        </div>
        <div>
          <h1 className="text-[28px] font-bold text-neutral-900 dark:text-white tracking-tight leading-tight">
            Activity & Audit
          </h1>
          <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
            Track every request, decision and transaction made by Carti.
          </p>
        </div>
      </div>

      {/* Filter Tabs & Search / Date bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        {/* Pills */}
        <div className="flex items-center gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab('requests')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'requests'
                ? 'bg-[#17191C] text-white dark:bg-white dark:text-[#17191C] shadow-xs'
                : 'bg-white dark:bg-[#17191C] text-neutral-600 dark:text-neutral-400 border border-[#E4E7E1] dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800'
            }`}
          >
            <FileText size={16} strokeWidth={1.8} />
            <span>Requests</span>
            <span className="text-[10px] opacity-75 tabular-nums">{requests.length}</span>
          </button>

          <button
            onClick={() => setActiveTab('comparisons')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'comparisons'
                ? 'bg-[#17191C] text-white dark:bg-white dark:text-[#17191C] shadow-xs'
                : 'bg-white dark:bg-[#17191C] text-neutral-600 dark:text-neutral-400 border border-[#E4E7E1] dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800'
            }`}
          >
            <Scale size={16} strokeWidth={1.8} />
            <span>Comparisons</span>
            <span className="text-[10px] opacity-75 tabular-nums">{candidates.length}</span>
          </button>

          <button
            onClick={() => setActiveTab('orders')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'orders'
                ? 'bg-[#17191C] text-white dark:bg-white dark:text-[#17191C] shadow-xs'
                : 'bg-white dark:bg-[#17191C] text-neutral-600 dark:text-neutral-400 border border-[#E4E7E1] dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800'
            }`}
          >
            <ShoppingBag size={16} strokeWidth={1.8} />
            <span>Orders</span>
            <span className="text-[10px] opacity-75 tabular-nums">{orders.length}</span>
          </button>

          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'timeline'
                ? 'bg-[#17191C] text-white dark:bg-white dark:text-[#17191C] shadow-xs'
                : 'bg-white dark:bg-[#17191C] text-neutral-600 dark:text-neutral-400 border border-[#E4E7E1] dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800'
            }`}
          >
            <History size={16} strokeWidth={1.8} />
            <span>Audit Timeline</span>
          </button>
        </div>

        {/* Right: Date selector + Search */}
        <div className="flex items-center gap-2.5">
          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="text-xs rounded-full bg-white dark:bg-[#17191C] border border-[#E4E7E1] dark:border-neutral-800 px-3.5 py-1.5 outline-hidden text-neutral-700 dark:text-neutral-300"
          >
            <option value="30days">Last 30 Days</option>
            <option value="7days">Last 7 Days</option>
            <option value="all">All Time</option>
          </select>

          <div className="relative w-48 sm:w-60">
            <Search size={16} strokeWidth={1.8} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search activity..."
              className="w-full text-xs rounded-full bg-white dark:bg-[#17191C] border border-[#E4E7E1] dark:border-neutral-800 pl-8.5 pr-3 py-1.5 outline-hidden text-neutral-900 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Main Two-Column Master-Detail View */}
      {activeTab === 'requests' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          {/* Left Column: Shopping Requests List (5 cols) */}
          <div className="lg:col-span-5 rounded-2xl p-5 bg-white dark:bg-[#17191C] border border-[#E4E7E1] dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-3">
            <div>
              <h3 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
                Shopping Requests ({requests.length})
              </h3>
              <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
                All purchase requests and their current status.
              </p>
            </div>

            <div className="flex flex-col gap-2.5 mt-1">
              {requests
                .filter(
                  (r) =>
                    !searchQuery ||
                    r.prompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    r.id.toLowerCase().includes(searchQuery.toLowerCase())
                )
                .map((req) => {
                  const isSelected = selectedRequestId === req.id
                  return (
                    <div
                      key={req.id}
                      onClick={() => setSelectedRequestId(req.id)}
                      className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                        isSelected
                          ? 'bg-[#ECFADF] dark:bg-[#142617] border-[#95EB68]/60 dark:border-[#95EB68]/40 shadow-xs'
                          : 'bg-white dark:bg-[#141619] border-[#E4E7E1] dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div
                          className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                            isSelected
                              ? 'bg-white dark:bg-[#17191C] text-[#1D4A18] dark:text-[#95EB68]'
                              : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400'
                          }`}
                        >
                          <Sparkles size={16} strokeWidth={1.8} />
                        </div>
                        <div className="min-w-0">
                          <div className="text-xs font-semibold text-neutral-900 dark:text-white truncate">
                            {req.prompt}
                          </div>
                          <div className="flex items-center gap-1.5 text-[11px] text-neutral-400 mt-0.5 font-mono tabular-nums">
                            <span>{req.id}</span>
                            <ExternalLink size={12} strokeWidth={1.8} />
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <div className="text-right">
                          <Badge
                            variant={req.status === 'proposal_ready' ? 'lime' : req.status === 'completed' ? 'success' : 'neutral'}
                            size="xs"
                          >
                            {req.status === 'proposal_ready' ? 'Proposal Ready' : req.status === 'completed' ? 'Completed' : req.status}
                          </Badge>
                          <div className="text-[10px] text-neutral-400 mt-1 font-mono tabular-nums">
                            {new Date(req.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                        <ChevronRight size={16} strokeWidth={1.8} className="text-neutral-400" />
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>

          {/* Right Column: Request Details & Audit Timeline (7 cols) */}
          <div className="lg:col-span-7 flex flex-col gap-4">
            {/* Top Detail Card */}
            <div className="rounded-2xl p-6 bg-white dark:bg-[#17191C] border border-[#E4E7E1] dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-5">
              <div className="flex items-start justify-between gap-3 pb-3 border-b border-neutral-100 dark:border-neutral-800">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-xl bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0 mt-0.5">
                    <Sparkles size={18} strokeWidth={1.8} />
                  </div>
                  <div>
                    <h3 className="text-[18px] font-semibold text-neutral-900 dark:text-white leading-snug">
                      {selectedRequest?.prompt}
                    </h3>
                    <div className="flex items-center gap-1.5 text-xs text-neutral-500 font-mono mt-1 tabular-nums">
                      <span>Request ID: {selectedRequest?.id}</span>
                      <ExternalLink size={12} strokeWidth={1.8} />
                    </div>
                  </div>
                </div>

                <Badge variant="lime" size="xs">
                  Proposal Ready
                </Badge>
              </div>

              {/* Sub-tab pills */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setRightSubTab('timeline')}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition-colors ${
                    rightSubTab === 'timeline'
                      ? 'bg-[#17191C] text-white dark:bg-white dark:text-[#17191C]'
                      : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400'
                  }`}
                >
                  <GitCommit size={16} strokeWidth={1.8} />
                  <span>Audit Timeline</span>
                </button>

                <button
                  onClick={() => setRightSubTab('details')}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition-colors ${
                    rightSubTab === 'details'
                      ? 'bg-[#17191C] text-white dark:bg-white dark:text-[#17191C]'
                      : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400'
                  }`}
                >
                  <FileText size={16} strokeWidth={1.8} />
                  <span>Details</span>
                </button>

                <button
                  onClick={() => setRightSubTab('candidates')}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition-colors ${
                    rightSubTab === 'candidates'
                      ? 'bg-[#17191C] text-white dark:bg-white dark:text-[#17191C]'
                      : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400'
                  }`}
                >
                  <Scale size={16} strokeWidth={1.8} />
                  <span>Candidate Comparison</span>
                </button>
              </div>

              {/* Chronological Timeline */}
              {rightSubTab === 'timeline' && (
                <div className="relative pl-6 space-y-5 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-neutral-200 dark:before:bg-neutral-800">
                  {requestTimelineEvents.map((evt, idx) => (
                    <div key={idx} className="relative flex items-start justify-between gap-3 text-xs">
                      {/* Timeline dot icon */}
                      <span className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-white dark:bg-[#17191C] border border-neutral-200 dark:border-neutral-700 flex items-center justify-center">
                        {evt.status === 'completed' ? (
                          <CheckCircle2 size={14} strokeWidth={2} className="text-emerald-500 fill-emerald-100 dark:fill-emerald-950/40" />
                        ) : (
                          <span className="w-2 h-2 rounded-full border border-neutral-400" />
                        )}
                      </span>

                      <div>
                        <div className="text-[14px] font-semibold text-neutral-900 dark:text-white">
                          {evt.title}
                        </div>
                        <div className="text-[12px] text-neutral-500 dark:text-neutral-400 mt-0.5">
                          {evt.desc}
                        </div>
                      </div>

                      <div className="text-[11px] text-neutral-400 font-mono tabular-nums shrink-0">
                        {evt.time}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {rightSubTab === 'details' && (
                <div className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-[#E4E7E1] dark:border-neutral-800 text-xs font-mono text-neutral-600 dark:text-neutral-400">
                  <pre className="overflow-x-auto text-[11px] tabular-nums">
                    {JSON.stringify(selectedRequest, null, 2)}
                  </pre>
                </div>
              )}

              {rightSubTab === 'candidates' && (
                <div className="flex flex-col gap-2 text-xs">
                  {candidates.map((c) => (
                    <div key={c.id} className="p-3 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
                      <div>
                        <span className="text-[14px] font-semibold text-neutral-900 dark:text-white">{c.title}</span>
                        <div className="text-[11px] text-neutral-400 tabular-nums">Score: {c.rank_score} • {c.offers.length} stores</div>
                      </div>
                      <Badge variant="lime" size="xs">Best Match</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Bottom Card: Verification & Audit Record */}
            <div className="rounded-2xl p-5 bg-white dark:bg-[#17191C] border border-[#E4E7E1] dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-3">
              <div
                onClick={() => setIsRecordExpanded(!isRecordExpanded)}
                className="flex items-center justify-between cursor-pointer"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-[#ECFADF] dark:bg-[#142617] text-[#1D4A18] dark:text-[#95EB68] flex items-center justify-center shrink-0">
                    <ShieldCheck size={16} strokeWidth={1.8} />
                  </div>
                  <div>
                    <h4 className="text-[15px] font-semibold text-neutral-900 dark:text-white">
                      Verification & Audit Record
                    </h4>
                    <p className="text-[12px] text-neutral-400">
                      Cryptographic proof and ledger information for this request.
                    </p>
                  </div>
                </div>

                <button className="text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200">
                  {isRecordExpanded ? <ChevronUp size={16} strokeWidth={1.8} /> : <ChevronDown size={16} strokeWidth={1.8} />}
                </button>
              </div>

              {isRecordExpanded && (
                <div className="pt-2 border-t border-neutral-100 dark:border-neutral-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-2 flex-wrap font-mono text-[11px] tabular-nums">
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700">
                      <span className="text-neutral-500 font-sans">Event Hash</span>
                      <span className="text-neutral-800 dark:text-neutral-200 font-bold tabular-nums">3f4a6e9c7b2d1e8f...</span>
                      <button
                        onClick={() => handleCopy('3f4a6e9c7b2d1e8f990142', 'event')}
                        className="text-neutral-400 hover:text-neutral-700 dark:hover:text-white ml-1 cursor-pointer"
                      >
                        {copiedHash === 'event' ? <Check size={14} strokeWidth={1.8} className="text-emerald-500" /> : <Copy size={14} strokeWidth={1.8} />}
                      </button>
                    </div>

                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700">
                      <span className="text-neutral-500 font-sans">Prev Hash</span>
                      <span className="text-neutral-800 dark:text-neutral-200 font-bold tabular-nums">8c1e2d4f9a0b7d3c...</span>
                      <button
                        onClick={() => handleCopy('8c1e2d4f9a0b7d3c114589', 'prev')}
                        className="text-neutral-400 hover:text-neutral-700 dark:hover:text-white ml-1 cursor-pointer"
                      >
                        {copiedHash === 'prev' ? <Check size={14} strokeWidth={1.8} className="text-emerald-500" /> : <Copy size={14} strokeWidth={1.8} />}
                      </button>
                    </div>
                  </div>

                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 text-xs font-semibold self-start sm:self-auto">
                    <CheckCircle2 size={14} strokeWidth={1.8} /> Verified
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Comparisons Tab */}
      {activeTab === 'comparisons' && (
        <div className="rounded-2xl p-5 bg-white dark:bg-[#17191C] border border-[#E4E7E1] dark:border-neutral-800">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-800 text-neutral-400 uppercase text-[10px] tracking-wider font-semibold">
                <th className="py-2.5 px-3">Product Name</th>
                <th className="py-2.5 px-3">Retailer</th>
                <th className="py-2.5 px-3">Price</th>
                <th className="py-2.5 px-3">Stock</th>
                <th className="py-2.5 px-3">Guardrail Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {candidates.flatMap((cand) =>
                cand.offers.map((off) => (
                  <tr key={off.id} className="hover:bg-neutral-50/60 dark:hover:bg-neutral-800/40">
                    <td className="py-3 px-3 font-semibold text-neutral-900 dark:text-white">{cand.title}</td>
                    <td className="py-3 px-3">{off.domain}</td>
                    <td className="py-3 px-3 font-bold font-mono tabular-nums">${off.price_amount}</td>
                    <td className="py-3 px-3 text-emerald-600 font-medium">{off.availability}</td>
                    <td className="py-3 px-3">
                      <Badge variant={off.is_eligible ? 'success' : 'danger'} size="xs">
                        {off.is_eligible ? 'Passed' : 'Ineligible'}
                      </Badge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Orders Tab */}
      {activeTab === 'orders' && (
        <div className="rounded-2xl p-5 bg-white dark:bg-[#17191C] border border-[#E4E7E1] dark:border-neutral-800">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-800 text-neutral-400 uppercase text-[10px] tracking-wider font-semibold">
                <th className="py-2.5 px-3">Order ID</th>
                <th className="py-2.5 px-3">Product Title</th>
                <th className="py-2.5 px-3">Amount</th>
                <th className="py-2.5 px-3">PayPal Capture ID</th>
                <th className="py-2.5 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {orders.map((o) => (
                <tr key={o.id} className="hover:bg-neutral-50/60 dark:hover:bg-neutral-800/40">
                  <td className="py-3 px-3 font-mono font-medium tabular-nums">{o.id}</td>
                  <td className="py-3 px-3 font-semibold">{o.product_title || 'Item'}</td>
                  <td className="py-3 px-3 font-bold font-mono tabular-nums">${o.amount} {o.currency}</td>
                  <td className="py-3 px-3 font-mono text-emerald-600 tabular-nums">{o.paypal_capture_id || 'CAP-SIMULATED'}</td>
                  <td className="py-3 px-3 text-right">
                    <Badge variant="success" size="xs">Completed</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Audit Timeline Tab */}
      {activeTab === 'timeline' && (
        <div className="rounded-2xl p-5 bg-white dark:bg-[#17191C] border border-[#E4E7E1] dark:border-neutral-800 flex flex-col gap-3">
          {auditEvents.map((ev) => (
            <div key={ev.id} className="p-3.5 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 size={16} strokeWidth={1.8} className="text-emerald-500" />
                <div>
                  <span className="font-bold text-neutral-900 dark:text-white uppercase tracking-wider">{ev.event_type.replace(/_/g, ' ')}</span>
                  <div className="text-[11px] text-neutral-400">{ev.reason}</div>
                </div>
              </div>
              <span className="text-[11px] text-neutral-400 font-mono tabular-nums">{new Date(ev.created_at).toLocaleString()}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
