import React, { useState } from 'react'
import { Edit3, RotateCcw, Trash2, ShieldCheck, Sparkles } from 'lucide-react'
import { MandateCard } from '../components/mandate/MandateCard'
import { MandateForm } from '../components/mandate/MandateForm'
import { Button } from '../components/common/Button'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'

export const MandatePage: React.FC = () => {
  const { mandate, breakdown, refreshMandate } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [isResetting, setIsResetting] = useState(false)

  const handleReset = async () => {
    if (window.confirm('Are you sure you want to reset your spending mandate? All limits, categories, and pending proposals will be cleared so you can configure everything from scratch.')) {
      try {
        setIsResetting(true)
        await api.resetMandate()
        await refreshMandate()
        setIsEditing(false)
      } catch (e) {
        console.error('Reset failed:', e)
      } finally {
        setIsResetting(false)
      }
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-[28px] font-bold text-neutral-900 dark:text-white tracking-tight leading-tight">
            Spending Controls
          </h1>
          <p className="text-[12px] font-normal text-neutral-500 dark:text-neutral-400 mt-0.5">
            {mandate
              ? `Autonomous purchasing authority (v${mandate.version}), budget allocation, and guardrails.`
              : 'Define your autonomous purchasing authority and policy boundaries from scratch.'}
          </p>
        </div>

        {mandate && (
          <div className="flex items-center gap-2">
            {!isEditing ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  icon={<Edit3 size={15} strokeWidth={1.8} />}
                  onClick={() => setIsEditing(true)}
                >
                  Edit Mandate
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  loading={isResetting}
                  icon={<Trash2 size={15} strokeWidth={1.8} className="text-rose-500" />}
                  onClick={handleReset}
                  className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/20"
                >
                  Reset
                </Button>
              </>
            ) : (
              <Button
                variant="outline"
                size="sm"
                icon={<RotateCcw size={15} strokeWidth={1.8} />}
                onClick={() => setIsEditing(false)}
              >
                Cancel Edit
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Main View: Fresh Creation vs. Active Card vs. Revision Form */}
      {!mandate ? (
        <div className="rounded-2xl p-6 md:p-8 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-6 animate-in fade-in duration-150">
          <div className="flex flex-col gap-1 pb-4 border-b border-neutral-100 dark:border-neutral-800">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 w-fit">
              <Sparkles size={14} />
              Set Up Your Custom Mandate
            </div>
            <h2 className="text-xl font-bold text-neutral-900 dark:text-white mt-2">
              Configure Your Spending Boundaries
            </h2>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 leading-relaxed max-w-2xl">
              You have full autonomy over your Carti parameters. Set your total budget, maximum per-item cap,
              approved retailers, and allowed categories. Carti will strictly enforce these boundaries before proposing any purchase.
            </p>
          </div>

          <MandateForm
            currentMandate={null}
            breakdown={null}
            onSuccess={() => setIsEditing(false)}
          />
        </div>
      ) : !isEditing ? (
        <MandateCard mandate={mandate} breakdown={breakdown} onReset={handleReset} />
      ) : (
        <div className="rounded-xl p-5 md:p-6 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-5 animate-in fade-in duration-150">
          <div className="pb-3 border-b border-neutral-100 dark:border-neutral-800">
            <h3 className="text-base font-bold text-neutral-900 dark:text-white">
              Create New Mandate Revision (v{mandate.version + 1})
            </h3>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
              Revisions supersede current parameters. In-flight reservations retain their locked version snapshot.
            </p>
          </div>
          <MandateForm
            currentMandate={mandate}
            breakdown={breakdown}
            onSuccess={() => setIsEditing(false)}
          />
        </div>
      )}
    </div>
  )
}
