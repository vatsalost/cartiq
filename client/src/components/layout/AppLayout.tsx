import React from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Header } from './Header'
import { BottomDock } from './BottomDock'

export const AppLayout: React.FC = () => {
  const location = useLocation()

  const getPageTitle = (pathname: string): string => {
    if (pathname === '/') return 'Dashboard'
    if (pathname.startsWith('/shopping')) return 'AI Shopping Concierge'
    if (pathname.startsWith('/mandate')) return 'Spending Mandate & Budgets'
    if (pathname.startsWith('/proposals')) return 'Purchase Proposals & Review'
    if (pathname.startsWith('/orders')) return 'Orders & Verified Receipts'
    if (pathname.startsWith('/history')) return 'Audit Timeline & History'
    if (pathname.startsWith('/settings')) return 'Settings & Integration'
    return 'Carti Concierge'
  }

  return (
    <div className="min-h-screen w-full bg-[#EAECEF] dark:bg-[#0B0C0E] transition-colors duration-200 py-3 md:py-6 px-3 sm:px-4 md:px-8 flex flex-col justify-between pb-28">
      {/* Main Container Card matching reference screenshots */}
      <div className="w-full max-w-[1440px] mx-auto rounded-[32px] bg-white dark:bg-[#14161B] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_20px_60px_rgba(0,0,0,0.04)] dark:shadow-[0_20px_60px_rgba(0,0,0,0.45)] p-5 md:p-8 transition-colors">
        <Header pageTitle={getPageTitle(location.pathname)} />
        <main className="pt-6">
          <Outlet />
        </main>
      </div>

      {/* Floating Bottom Dock Bar */}
      <BottomDock />
    </div>
  )
}
