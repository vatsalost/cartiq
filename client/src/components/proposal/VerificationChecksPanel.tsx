import React from 'react'
import { CheckCircle2, XCircle, ShieldCheck } from 'lucide-react'
import { GuardrailResult } from '../../api/types'
import { Badge } from '../common/Badge'

export const VerificationChecksPanel: React.FC<{
  guardrailResult: GuardrailResult
}> = ({ guardrailResult }) => {
  const allPassed = guardrailResult.passed || guardrailResult.checks.every((c) => c.passed)

  return (
    <div className="rounded-xl p-5 bg-white dark:bg-[#17191C] border border-neutral-200/90 dark:border-neutral-800 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-3">
      <div className="flex items-center justify-between pb-3 border-b border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-2">
          <ShieldCheck size={16} strokeWidth={1.8} className="text-[#95EB68]" />
          <h3 className="text-[12px] font-semibold text-neutral-900 dark:text-white uppercase tracking-wider">
            Deterministic Purchase Guardrails (8-Point Policy Audit)
          </h3>
        </div>
        <Badge variant={allPassed ? 'success' : 'danger'} size="xs" dot>
          {allPassed ? '8/8 Passed' : 'Policy Blocked'}
        </Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 mt-1">
        {guardrailResult.checks.map((check, idx) => (
          <div
            key={idx}
            className={`p-3 rounded-lg border text-left transition-all ${
              check.passed
                ? 'bg-neutral-50/70 dark:bg-[#141619] border-neutral-200/70 dark:border-neutral-800'
                : 'bg-rose-50/60 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/40 text-rose-700 dark:text-rose-400'
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              {check.passed ? (
                <CheckCircle2 size={14} strokeWidth={2} className="text-emerald-500 shrink-0" />
              ) : (
                <XCircle size={14} strokeWidth={2} className="text-rose-500 shrink-0" />
              )}
              <span className="text-xs font-semibold text-neutral-800 dark:text-neutral-200 capitalize truncate">
                {check.rule.replace(/_/g, ' ')}
              </span>
            </div>
            <p className="text-[11px] text-neutral-500 dark:text-neutral-400 line-clamp-2 leading-relaxed">
              {check.reason}
            </p>
            {(check.actual || check.limit) && (
              <div className="text-[10px] text-neutral-400 font-mono mt-1 pt-1 border-t border-neutral-200/40 dark:border-neutral-800/60 tabular-nums">
                {check.actual && `Actual: ${check.actual}`}
                {check.limit && ` | Cap: ${check.limit}`}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
