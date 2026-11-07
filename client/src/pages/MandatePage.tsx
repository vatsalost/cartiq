import React, { useState } from 'react'
import { Edit3, RotateCcw } from 'lucide-react'
import { MandateCard } from '../components/mandate/MandateCard'
import { MandateForm } from '../components/mandate/MandateForm'
import { Button } from '../components/common/Button'
import { useAuth } from '../context/AuthContext'
import { mockMandate } from '../api/mockData'

export const MandatePage: React.FC = () => {
  const { mandate, breakdown } = useAuth()
  const [isEditing, setIsEditing] = useState(false)

  const activeMandate = mandate || mockMandate

  return (
    <div className="flex flex-col gap-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-white tracking-tight">
            Spending Controls
          </h1>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
            Autonomous purchasing authority, budget allocation, and category guardrails.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {!isEditing ? (
            <Button
              variant="outline"
              size="sm"
              icon={<Edit3 size={14} />}
              onClick={() => setIsEditing(true)}
            >
              Edit Mandate
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              icon={<RotateCcw size={14} />}
              onClick={() => setIsEditing(false)}
            >
              Cancel Edit
            </Button>
          )}
        </div>
      </div>

      {/* Main View: Card vs. Form */}
      {!isEditing ? (
        <MandateCard mandate={activeMandate} breakdown={breakdown} />
      ) : (
        <div className="rounded-xl p-5 md:p-6 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-5 animate-in fade-in duration-150">
          <div className="pb-3 border-b border-neutral-100 dark:border-neutral-800">
            <h3 className="text-base font-bold text-neutral-900 dark:text-white">
              Create New Mandate Revision (v{activeMandate.version + 1})
            </h3>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
              Revisions supersede current parameters. In-flight reservations retain their locked version snapshot.
            </p>
          </div>
          <MandateForm
            currentMandate={activeMandate}
            breakdown={breakdown}
            onSuccess={() => setIsEditing(false)}
          />
        </div>
      )}
    </div>
  )
}
