import React from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Header } from './Header'

export const AppLayout: React.FC = () => {
  const location = useLocation()

  const getPageTitle = (pathname: string): string => {
    if (pathname === '/') return 'Dashboard'
    if (pathname.startsWith('/shopping')) return 'Shopping'
    if (pathname.startsWith('/mandate')) return 'Spending Mandate'
    if (pathname.startsWith('/proposals')) return 'Purchase Proposals'
    if (pathname.startsWith('/orders')) return 'Orders & Receipts'
    if (pathname.startsWith('/history')) return 'History & Audit'
    if (pathname.startsWith('/settings')) return 'Settings'
    return 'Carti'
  }

  return (
    <div className="min-h-screen w-full bg-[#EAECEF] dark:bg-[#0B0C0E] transition-colors duration-200 py-3 md:py-6 px-3 sm:px-4 md:px-8 flex flex-col justify-between pb-12">
      <div className="w-full max-w-[1400px] mx-auto rounded-3xl bg-white dark:bg-[#14161B] border border-neutral-200/90 dark:border-neutral-800 shadow-sm p-5 md:p-8 transition-colors">
        <Header pageTitle={getPageTitle(location.pathname)} />
        <main className="pt-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
