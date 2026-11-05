import React from 'react'
import { CheckCircle2, XCircle, ShieldCheck } from 'lucide-react'
import { GuardrailResult } from '../../api/types'

export const VerificationChecksPanel: React.FC<{
  guardrailResult: GuardrailResult
}> = ({ guardrailResult }) => {
  return (
    <div className="rounded-2xl p-5 sm:p-6 bg-white dark:bg-[#16181D] border border-neutral-200 dark:border-neutral-800 shadow-xs flex flex-col gap-3">
      <div className="flex items-center justify-between pb-2 border-b border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-2">
          <ShieldCheck size={16} className="text-[#98EC6A] dark:text-[#2CE5B5]" />
          <h3 className="text-sm font-bold text-neutral-900 dark:text-white">
            Mandate Verification Checks
          </h3>
        </div>
        <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
          All Passed
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
        {guardrailResult.checks.map((check, idx) => (
          <div
            key={idx}
            className={`p-2.5 rounded-xl border transition-colors flex items-start gap-2.5 ${
              check.passed
                ? 'bg-neutral-50/60 dark:bg-[#191B21] border-neutral-200/70 dark:border-neutral-800'
                : 'bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-400'
            }`}
          >
            <div className="shrink-0 mt-0.5">
              {check.passed ? (
                <CheckCircle2 size={15} className="text-emerald-500" />
              ) : (
                <XCircle size={15} className="text-rose-500" />
              )}
            </div>
            <div>
              <div className="text-xs font-semibold text-neutral-900 dark:text-white capitalize">
                {check.rule.replace(/_/g, ' ')}
              </div>
              <div className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5">
                {check.reason}
              </div>
              {(check.actual || check.limit) && (
                <div className="text-[10px] text-neutral-400 font-mono mt-0.5">
                  {check.actual && `Actual: ${check.actual}`}
                  {check.limit && ` | Limit: ${check.limit}`}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
