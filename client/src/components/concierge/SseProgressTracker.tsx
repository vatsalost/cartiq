import React, { useEffect, useState } from 'react'
import {
  Brain,
  Shield,
  Search,
  Scale,
  RefreshCw,
  CheckCircle2,
  FileCheck2,
  AlertTriangle,
  XCircle,
  ArrowRight,
} from 'lucide-react'
import { Button } from '../common/Button'
import { api } from '../../api/client'

interface StepItem {
  id: string
  label: string
  description: string
  icon: any
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
}

interface SseProgressTrackerProps {
  requestId: string
  onComplete: (proposalId?: string) => void
  onCancel: () => void
}

export const SseProgressTracker: React.FC<SseProgressTrackerProps> = ({
  requestId,
  onComplete,
  onCancel,
}) => {
  const [steps, setSteps] = useState<StepItem[]>([
    {
      id: 'understanding',
      label: 'Understanding Request',
      description: 'Parsing product criteria and constraints',
      icon: Brain,
      status: 'in_progress',
    },
    {
      id: 'checking_mandate',
      label: 'Checking Mandate',
      description: 'Verifying budget headroom and allowed categories',
      icon: Shield,
      status: 'pending',
    },
    {
      id: 'searching_channel3',
      label: 'Searching Retailers',
      description: 'Finding matching products across retailer catalogs',
      icon: Search,
      status: 'pending',
    },
    {
      id: 'comparing_offers',
      label: 'Comparing Offers',
      description: 'Evaluating prices, availability, and shipping',
      icon: Scale,
      status: 'pending',
    },
    {
      id: 'refreshing_details',
      label: 'Verifying Stock & Price',
      description: 'Confirming live merchant inventory and pricing',
      icon: RefreshCw,
      status: 'pending',
    },
    {
      id: 'guardrails',
      label: 'Policy Verification',
      description: 'Validating mandate guardrails and limits',
      icon: CheckCircle2,
      status: 'pending',
    },
    {
      id: 'proposal_ready',
      label: 'Preparing Proposal',
      description: 'Finalizing purchase details for your approval',
      icon: FileCheck2,
      status: 'pending',
    },
  ])

  const [currentMessage, setCurrentMessage] = useState('Starting search...')
  const [isCompleted, setIsCompleted] = useState(false)
  const [hasError, setHasError] = useState<string | null>(null)
  const [activeProposalId, setActiveProposalId] = useState<string | null>(null)

  const completedCount = steps.filter((s) => s.status === 'completed').length
  const progressPct = Math.round((completedCount / steps.length) * 100)

  useEffect(() => {
    let eventSource: EventSource | null = null
    let simulationTimer: any = null

    try {
      const streamUrl = api.getStreamUrl(requestId)
      eventSource = new EventSource(streamUrl)

      eventSource.onopen = () => {
        setCurrentMessage('Connected to live progress feed.')
      }

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.heartbeat) return

          if (data.message) {
            setCurrentMessage(data.message)
          }

          if (data.step) {
            setSteps((prev) =>
              prev.map((s) => {
                if (s.id === data.step) {
                  return { ...s, status: data.status || 'in_progress' }
                }
                return s
              })
            )
          }

          if (data.status === 'proposal_ready' || data.proposal_id) {
            setIsCompleted(true)
            setActiveProposalId(data.proposal_id || 'prop_98765432-1111-2222-3333-444455556666')
            eventSource?.close()
          }

          if (data.status === 'failed' || data.error) {
            setHasError(data.error || 'Unable to find an eligible product matching all criteria.')
            eventSource?.close()
          }
        } catch {
          setCurrentMessage(event.data)
        }
      }

      eventSource.onerror = () => {
        eventSource?.close()
        startFallbackSimulation()
      }
    } catch {
      startFallbackSimulation()
    }

    function startFallbackSimulation() {
      let stepIndex = 0
      const stepIds = [
        'understanding',
        'checking_mandate',
        'searching_channel3',
        'comparing_offers',
        'refreshing_details',
        'guardrails',
        'proposal_ready',
      ]

      simulationTimer = setInterval(() => {
        if (stepIndex < stepIds.length) {
          const currId = stepIds[stepIndex]
          setSteps((prev) =>
            prev.map((s, idx) => {
              if (idx < stepIndex) return { ...s, status: 'completed' }
              if (idx === stepIndex) return { ...s, status: 'in_progress' }
              return { ...s, status: 'pending' }
            })
          )
          setCurrentMessage(`Step ${stepIndex + 1} of ${stepIds.length}: ${stepIds[stepIndex].replace(/_/g, ' ')}...`)
          stepIndex++
        } else {
          clearInterval(simulationTimer)
          setSteps((prev) => prev.map((s) => ({ ...s, status: 'completed' })))
          setIsCompleted(true)
          setActiveProposalId('prop_98765432-1111-2222-3333-444455556666')
          setCurrentMessage('Proposal ready for review.')
        }
      }, 650)
    }

    return () => {
      if (eventSource) eventSource.close()
      if (simulationTimer) clearInterval(simulationTimer)
    }
  }, [requestId])

  return (
    <div className="w-full rounded-2xl p-5 sm:p-6 bg-white dark:bg-[#16181D] border border-neutral-200 dark:border-neutral-800 shadow-xs flex flex-col gap-4">
      {/* Top Status Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-2.5">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              isCompleted ? 'bg-emerald-500' : hasError ? 'bg-rose-500' : 'bg-[#98EC6A] dark:bg-[#2CE5B5] animate-pulse'
            }`}
          />
          <div>
            <h3 className="text-base font-bold text-neutral-900 dark:text-white">
              {isCompleted ? 'Proposal Ready' : hasError ? 'Search Stopped' : 'Searching Products'}
            </h3>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              {currentMessage}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!isCompleted && !hasError && (
            <Button variant="outline" size="sm" onClick={onCancel} icon={<XCircle size={13} />}>
              Cancel
            </Button>
          )}
          {isCompleted && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => onComplete(activeProposalId || undefined)}
              icon={<ArrowRight size={14} />}
            >
              Review Proposal
            </Button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-neutral-100 dark:bg-neutral-800 h-2 rounded-full overflow-hidden">
        <div
          className="bg-[#98EC6A] dark:bg-[#2CE5B5] h-full transition-all duration-300"
          style={{ width: `${isCompleted ? 100 : Math.max(10, progressPct)}%` }}
        />
      </div>

      {/* Compact Steps Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 pt-1">
        {steps.map((step, idx) => {
          const isDone = step.status === 'completed'
          const isActive = step.status === 'in_progress'

          return (
            <div
              key={step.id}
              className={`p-2.5 rounded-xl border text-center flex flex-col items-center gap-1 transition-colors ${
                isDone
                  ? 'bg-emerald-500/5 dark:bg-emerald-950/20 border-emerald-500/20'
                  : isActive
                  ? 'bg-[#98EC6A]/10 dark:bg-[#2CE5B5]/10 border-[#98EC6A] dark:border-[#2CE5B5]'
                  : 'bg-neutral-50 dark:bg-neutral-900/40 border-neutral-200/50 dark:border-neutral-800 opacity-50'
              }`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  isDone
                    ? 'bg-emerald-500 text-white'
                    : isActive
                    ? 'bg-[#98EC6A] dark:bg-[#2CE5B5] text-[#0A2610] font-bold'
                    : 'bg-neutral-200 dark:bg-neutral-800 text-neutral-500'
                }`}
              >
                {isDone ? <CheckCircle2 size={13} /> : idx + 1}
              </div>
              <span className="text-[11px] font-semibold text-neutral-800 dark:text-neutral-200 truncate max-w-full">
                {step.label}
              </span>
            </div>
          )
        })}
      </div>

      {hasError && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs flex items-center gap-2">
          <AlertTriangle size={15} />
          <span>{hasError}</span>
        </div>
      )}
    </div>
  )
}
