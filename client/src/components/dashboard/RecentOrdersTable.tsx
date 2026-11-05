import React from 'react'
import { Link } from 'react-router-dom'
import { ShoppingBag, ArrowRight, ExternalLink } from 'lucide-react'
import { Order } from '../../api/types'
import { Badge } from '../common/Badge'

export const RecentOrdersTable: React.FC<{ orders: Order[] }> = ({ orders }) => {
  const getOrderBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success">Completed</Badge>
      case 'buyer_approved':
        return <Badge variant="lavender">Awaiting Capture</Badge>
      case 'created':
        return <Badge variant="info">Created</Badge>
      case 'refunded':
        return <Badge variant="warning">Refunded</Badge>
      case 'cancelled':
        return <Badge variant="neutral">Cancelled</Badge>
      default:
        return <Badge variant="neutral">{status}</Badge>
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-extrabold text-neutral-900 dark:text-white tracking-tight flex items-center gap-2">
          <span>Recent PayPal Checkout Orders</span>
        </h3>
        <Link
          to="/orders"
          className="text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white flex items-center gap-1 transition-colors"
        >
          <span>View All</span>
          <ArrowRight size={14} />
        </Link>
      </div>

      <div className="flex flex-col gap-2">
        {orders.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200/60 dark:border-neutral-800 text-sm text-neutral-500">
            No orders captured yet.
          </div>
        ) : (
          orders.slice(0, 4).map((order) => (
            <div
              key={order.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 px-4 rounded-2xl bg-white dark:bg-[#191B21] border border-neutral-200/80 dark:border-neutral-800 hover:border-neutral-400 dark:hover:border-neutral-700 transition-all shadow-[1px_2px_0px_rgba(0,0,0,0.03)] dark:shadow-none gap-3"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-neutral-700 dark:text-neutral-300 shrink-0">
                  <ShoppingBag size={14} />
                </div>
                <div>
                  <div className="text-sm font-bold text-neutral-900 dark:text-white truncate max-w-xs md:max-w-md">
                    {order.product_title || `Order ${order.id.slice(0, 8)}`}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                    <span>Retailer: {order.retailer_domain || 'Online'}</span>
                    <span>•</span>
                    <span className="font-mono text-[11px] text-neutral-400">
                      {order.paypal_capture_id || order.paypal_order_id}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 justify-between sm:justify-end">
                <div className="text-right">
                  <div className="text-sm font-black text-neutral-900 dark:text-white">
                    ${order.amount} {order.currency}
                  </div>
                  <div className="text-[11px] text-neutral-400">
                    {order.captured_at
                      ? new Date(order.captured_at).toLocaleDateString()
                      : new Date(order.created_at).toLocaleDateString()}
                  </div>
                </div>
                {getOrderBadge(order.status)}
                {order.retailer_buy_url && (
                  <a
                    href={order.retailer_buy_url}
                    target="_blank"
                    rel="noreferrer"
                    className="p-1.5 text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
                    title="Visit Retailer"
                  >
                    <ExternalLink size={14} />
                  </a>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
