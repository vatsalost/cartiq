import React from 'react'
import { CheckCircle2, XCircle, ShieldCheck } from 'lucide-react'
import { GuardrailResult } from '../../api/types'

export const VerificationChecksPanel: React.FC<{
  guardrailResult: GuardrailResult
}> = ({ guardrailResult }) => {
  return (
    <div className="rounded-[28px] p-6 bg-white dark:bg-[#16181D] border border-neutral-200/80 dark:border-neutral-800 shadow-[0_4px_24px_rgba(0,0,0,0.03)] flex flex-col gap-4">
      <div className="flex items-center justify-between pb-3 border-b border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-2">
          <ShieldCheck size={18} className="text-[#98EC6A] dark:text-[#2CE5B5]" />
          <h3 className="text-base font-extrabold text-neutral-900 dark:text-white">
            Deterministic Purchase Guardrails
          </h3>
        </div>
        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
          Backend Evaluated
        </span>
      </div>

      <p className="text-xs text-neutral-500 dark:text-neutral-400">
        Every proposal undergoes independent server-side verification before PayPal order creation is allowed.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1">
        {guardrailResult.checks.map((check, idx) => (
          <div
            key={idx}
            className={`p-3.5 rounded-2xl border transition-colors flex items-start gap-2.5 ${
              check.passed
                ? 'bg-neutral-50/60 dark:bg-[#191B21] border-neutral-200/60 dark:border-neutral-800'
                : 'bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-400'
            }`}
          >
            <div className="shrink-0 mt-0.5">
              {check.passed ? (
                <CheckCircle2 size={16} className="text-emerald-500" />
              ) : (
                <XCircle size={16} className="text-rose-500" />
              )}
            </div>
            <div>
              <div className="text-xs font-bold text-neutral-900 dark:text-white capitalize">
                {check.rule.replace(/_/g, ' ')}
              </div>
              <div className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5">
                {check.reason}
              </div>
              {(check.actual || check.limit) && (
                <div className="text-[10px] text-neutral-400 font-mono mt-1">
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
