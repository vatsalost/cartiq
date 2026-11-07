import React from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from '../components/layout/AppLayout'
import { DashboardPage } from '../pages/DashboardPage'
import { ShoppingPage } from '../pages/ShoppingPage'
import { MandatePage } from '../pages/MandatePage'
import { ProposalsPage } from '../pages/ProposalsPage'
import { OrdersPage } from '../pages/OrdersPage'
import { HistoryPage } from '../pages/HistoryPage'
import { ActivityPage } from '../pages/ActivityPage'
import { SettingsPage } from '../pages/SettingsPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <ShoppingPage />,
      },
      {
        path: 'shopping',
        element: <ShoppingPage />,
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
        path: 'mandate',
        element: <MandatePage />,
      },
      {
        path: 'activity',
        element: <ActivityPage />,
      },
      {
        path: 'history',
        element: <Navigate to="/activity" replace />,
      },
      {
        path: 'overview',
        element: <DashboardPage />,
      },
      {
        path: 'dashboard',
        element: <Navigate to="/overview" replace />,
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
