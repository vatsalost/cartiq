import React from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from '../components/layout/AppLayout'
import { DashboardPage } from '../pages/DashboardPage'
import { ShoppingPage } from '../pages/ShoppingPage'
import { MandatePage } from '../pages/MandatePage'
import { ProposalsPage } from '../pages/ProposalsPage'
import { OrdersPage } from '../pages/OrdersPage'
import { HistoryPage } from '../pages/HistoryPage'
import { SettingsPage } from '../pages/SettingsPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'shopping',
        element: <ShoppingPage />,
      },
      {
        path: 'mandate',
        element: <MandatePage />,
      },
      {
        path: 'proposals',
        element: <ProposalsPage />,
      },
      {
        path: 'orders',
        element: <OrdersPage />,
      },
      {
        path: 'history',
        element: <HistoryPage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
])
