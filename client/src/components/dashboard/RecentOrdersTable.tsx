import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { Order } from '../../api/types'
import { Badge } from '../common/Badge'

export const RecentOrdersTable: React.FC<{ orders: Order[] }> = ({ orders }) => {
  const getOrderBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success" size="sm">Completed</Badge>
      case 'buyer_approved':
        return <Badge variant="lavender" size="sm">Pending Capture</Badge>
      case 'created':
        return <Badge variant="info" size="sm">Created</Badge>
      case 'refunded':
        return <Badge variant="warning" size="sm">Refunded</Badge>
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
          Recent Orders
        </h3>
        <Link
          to="/orders"
          className="text-xs font-medium text-neutral-500 hover:text-neutral-900 dark:hover:text-white flex items-center gap-1 transition-colors"
        >
          <span>All Orders</span>
          <ArrowRight size={12} />
        </Link>
      </div>

      <div className="flex flex-col gap-2">
        {orders.length === 0 ? (
          <div className="p-6 text-center text-xs text-neutral-500 dark:text-neutral-400">
            No orders captured yet.
          </div>
        ) : (
          orders.slice(0, 4).map((order) => (
            <div
              key={order.id}
              className="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-[#1A1D23] border border-neutral-200/70 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 transition-colors gap-3"
            >
              <div className="min-w-0 flex-1">
                <div className="text-xs font-semibold text-neutral-900 dark:text-white truncate">
                  {order.product_title || `Order ${order.id.slice(0, 8)}`}
                </div>
                <div className="flex items-center gap-2 text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5">
                  <span>{order.retailer_domain || 'Retailer'}</span>
                  <span>•</span>
                  <span>{new Date(order.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <div className="text-right">
                  <div className="text-xs font-bold text-neutral-900 dark:text-white">
                    ${order.amount}
                  </div>
                </div>
                {getOrderBadge(order.status)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
