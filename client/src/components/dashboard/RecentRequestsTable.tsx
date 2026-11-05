import React from 'react'
import { Link } from 'react-router-dom'
import { Sparkles, ArrowRight, Clock } from 'lucide-react'
import { ShoppingRequest } from '../../api/types'
import { Badge } from '../common/Badge'

export const RecentRequestsTable: React.FC<{ requests: ShoppingRequest[] }> = ({ requests }) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success">Completed</Badge>
      case 'proposal_ready':
        return <Badge variant="lime">Proposal Ready</Badge>
      case 'searching':
      case 'planning':
      case 'comparing':
        return <Badge variant="lavender">AI Active</Badge>
      case 'cancelled':
        return <Badge variant="neutral">Cancelled</Badge>
      default:
        return <Badge variant="info">{status}</Badge>
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-extrabold text-neutral-900 dark:text-white tracking-tight flex items-center gap-2">
          <span>Recent AI Shopping Requests</span>
        </h3>
        <Link
          to="/shopping"
          className="text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white flex items-center gap-1 transition-colors"
        >
          <span>View All</span>
          <ArrowRight size={14} />
        </Link>
      </div>

      <div className="flex flex-col gap-2">
        {requests.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200/60 dark:border-neutral-800 text-sm text-neutral-500">
            No shopping requests yet. Start your first AI search!
          </div>
        ) : (
          requests.slice(0, 4).map((req) => (
            <div
              key={req.id}
              className="group flex flex-col sm:flex-row sm:items-center justify-between p-3.5 px-4 rounded-2xl bg-white dark:bg-[#191B21] border border-neutral-200/80 dark:border-neutral-800 hover:border-neutral-400 dark:hover:border-neutral-700 transition-all shadow-[1px_2px_0px_rgba(0,0,0,0.03)] dark:shadow-none gap-3"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-neutral-700 dark:text-neutral-300 shrink-0">
                  <Sparkles size={14} />
                </div>
                <div>
                  <div className="text-sm font-bold text-neutral-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-teal-400 transition-colors">
                    {req.prompt}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                    <span>Category: {req.normalized_category || 'General'}</span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock size={11} />
                      {new Date(req.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 justify-end">
                {getStatusBadge(req.status)}
                {req.active_proposal_id ? (
                  <Link
                    to="/proposals"
                    className="px-3 py-1 rounded-full text-xs font-bold bg-[#98EC6A] dark:bg-[#2CE5B5] text-[#0A2610] dark:text-[#05261F] hover:brightness-105"
                  >
                    Review
                  </Link>
                ) : (
                  <Link
                    to="/shopping"
                    className="p-1.5 text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
                  >
                    <ArrowRight size={14} />
                  </Link>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
