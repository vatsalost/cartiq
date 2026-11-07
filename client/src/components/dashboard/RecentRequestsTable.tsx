import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Clock } from 'lucide-react'
import { ShoppingRequest } from '../../api/types'
import { Badge } from '../common/Badge'

export const RecentRequestsTable: React.FC<{ requests: ShoppingRequest[] }> = ({ requests }) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success" size="sm">Completed</Badge>
      case 'proposal_ready':
        return <Badge variant="lime" size="sm">Proposal Ready</Badge>
      case 'searching':
      case 'planning':
      case 'comparing':
        return <Badge variant="info" size="sm">In Progress</Badge>
      case 'cancelled':
        return <Badge variant="neutral" size="sm">Cancelled</Badge>
      default:
        return <Badge variant="neutral" size="sm">{status}</Badge>
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between pb-2 border-b border-neutral-200/60 dark:border-neutral-800">
        <h3 className="text-sm font-bold text-neutral-900 dark:text-white">
          Recent Requests
        </h3>
        <Link
          to="/shopping"
          className="text-xs font-medium text-neutral-500 hover:text-neutral-900 dark:hover:text-white flex items-center gap-1 transition-colors"
        >
          <span>All Requests</span>
          <ArrowRight size={12} />
        </Link>
      </div>

      <div className="flex flex-col gap-2">
        {requests.length === 0 ? (
          <div className="p-6 text-center text-xs text-neutral-500 dark:text-neutral-400">
            No shopping requests yet.
          </div>
        ) : (
          requests.slice(0, 4).map((req) => (
            <div
              key={req.id}
              className="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 transition-colors gap-3"
            >
              <div className="min-w-0 flex-1">
                <div className="text-xs font-semibold text-neutral-900 dark:text-white truncate">
                  {req.prompt}
                </div>
                <div className="flex items-center gap-2 text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5">
                  <span>{req.normalized_category || 'General'}</span>
                  <span>•</span>
                  <span>{new Date(req.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {getStatusBadge(req.status)}
                {req.active_proposal_id && (
                  <Link
                    to="/proposals"
                    className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#98EC6A] dark:bg-[#2CE5B5] text-[#0A2610] dark:text-[#05261F] hover:brightness-105"
                  >
                    View
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
