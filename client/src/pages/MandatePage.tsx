import React, { useState } from 'react'
import { Shield, Edit3, CheckCircle, RotateCcw } from 'lucide-react'
import { MandateCard } from '../components/mandate/MandateCard'
import { MandateForm } from '../components/mandate/MandateForm'
import { Button } from '../components/common/Button'
import { useAuth } from '../context/AuthContext'
import { mockMandate } from '../api/mockData'

export const MandatePage: React.FC = () => {
  const { mandate, breakdown, refreshMandate } = useAuth()
  const [isEditing, setIsEditing] = useState(false)

  const activeMandate = mandate || mockMandate

  return (
    <div className="flex flex-col gap-6">
      {/* Top Controls Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg md:text-xl font-bold text-neutral-900 dark:text-white tracking-tight">
            Spending Mandate
          </h2>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
            Set your budget limits, per-item spending caps, and retailer rules
          </p>
        </div>

        <div className="flex items-center gap-2">
          {!isEditing ? (
            <Button
              variant="primary"
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
        <div className="rounded-[28px] p-6 md:p-8 bg-white dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800 shadow-[0_4px_24px_rgba(0,0,0,0.03)]">
          <div className="pb-4 mb-6 border-b border-neutral-100 dark:border-neutral-800">
            <h3 className="text-lg font-bold text-neutral-900 dark:text-white">
              Create New Mandate Version (v{activeMandate.version + 1})
            </h3>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
              Changes supersede previous versions. In-flight orders retain their locked version snapshot.
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
