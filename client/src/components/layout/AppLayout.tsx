import React, { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'

export const AppLayout: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()

  const getPageTitle = (pathname: string): string => {
    if (pathname === '/') return 'Overview'
    if (pathname.startsWith('/shopping')) return 'AI Shopping Assistant'
    if (pathname.startsWith('/mandate')) return 'Spending Mandate'
    if (pathname.startsWith('/proposals')) return 'Purchase Proposals'
    if (pathname.startsWith('/orders')) return 'Orders & Transactions'
    if (pathname.startsWith('/history')) return 'Activity & Audit Trail'
    if (pathname.startsWith('/settings')) return 'Settings'
    return 'Carti'
  }

  return (
    <div className="min-h-screen w-full bg-[#F5F6F3] dark:bg-[#0F1012] flex transition-colors duration-150">
      {/* Fixed Left Sidebar */}
      <Sidebar isOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        <Header
          pageTitle={getPageTitle(location.pathname)}
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
        />
        <main className="flex-1 p-4 sm:p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
