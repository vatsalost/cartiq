import React, { useState } from 'react'
import { Plus, X, Save, AlertCircle } from 'lucide-react'
import { Mandate, BudgetBreakdown } from '../../api/types'
import { Button } from '../common/Button'
import { Input } from '../common/Input'
import { api } from '../../api/client'
import { useAuth } from '../../context/AuthContext'

export const MandateForm: React.FC<{
  currentMandate: Mandate
  breakdown: BudgetBreakdown | null
  onSuccess: () => void
}> = ({ currentMandate, breakdown, onSuccess }) => {
  const { refreshMandate } = useAuth()
  const [totalBudget, setTotalBudget] = useState(currentMandate.total_budget)
  const [perItemCap, setPerItemCap] = useState(currentMandate.per_item_cap)
  const [currency, setCurrency] = useState(currentMandate.currency || 'USD')
  const [maxQuantity, setMaxQuantity] = useState(currentMandate.max_quantity_per_product || 2)
  const [priceTolerance, setPriceTolerance] = useState(currentMandate.price_tolerance_pct || 10)

  const [allowedCategories, setAllowedCategories] = useState<string[]>([
    ...currentMandate.allowed_categories,
  ])
  const [newCatInput, setNewCatInput] = useState('')

  const [allowedRetailers, setAllowedRetailers] = useState<string[]>([
    ...currentMandate.allowed_retailers,
  ])
  const [newRetailerInput, setNewRetailerInput] = useState('')

  const [blockedCategories, setBlockedCategories] = useState<string[]>([
    ...currentMandate.blocked_categories,
  ])
  const [newBlockedInput, setNewBlockedInput] = useState('')

  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const handleAddCategory = () => {
    if (newCatInput.trim() && !allowedCategories.includes(newCatInput.trim())) {
      setAllowedCategories([...allowedCategories, newCatInput.trim()])
      setNewCatInput('')
    }
  }

  const handleRemoveCategory = (cat: string) => {
    setAllowedCategories(allowedCategories.filter((c) => c !== cat))
  }

  const handleAddRetailer = () => {
    if (newRetailerInput.trim() && !allowedRetailers.includes(newRetailerInput.trim().toLowerCase())) {
      setAllowedRetailers([...allowedRetailers, newRetailerInput.trim().toLowerCase()])
      setNewRetailerInput('')
    }
  }

  const handleRemoveRetailer = (ret: string) => {
    setAllowedRetailers(allowedRetailers.filter((r) => r !== ret))
  }

  const handleAddBlocked = () => {
    if (newBlockedInput.trim() && !blockedCategories.includes(newBlockedInput.trim())) {
      setBlockedCategories([...blockedCategories, newBlockedInput.trim()])
      setNewBlockedInput('')
    }
  }

  const handleRemoveBlocked = (cat: string) => {
    setBlockedCategories(blockedCategories.filter((c) => c !== cat))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessMessage(null)

    const budgetNum = parseFloat(totalBudget)
    const capNum = parseFloat(perItemCap)

    if (isNaN(budgetNum) || budgetNum <= 0) {
      setError('Total budget must be a positive number.')
      return
    }

    if (isNaN(capNum) || capNum <= 0) {
      setError('Per-item cap must be a positive number.')
      return
    }

    if (capNum > budgetNum) {
      setError('Per-item cap cannot exceed total mandate budget.')
      return
    }

    // Committed spend check from B3
    const captured = parseFloat(breakdown?.captured_spending || '0')
    const reserved = parseFloat(breakdown?.active_reservations || '0')
    const committed = captured + reserved
    if (budgetNum < committed) {
      setError(
        `Cannot set total budget ($${budgetNum.toFixed(2)}) below active committed spend ($${committed.toFixed(2)}).`
      )
      return
    }

    try {
      setIsSubmitting(true)
      await api.saveMandate({
        total_budget: budgetNum.toFixed(2),
        per_item_cap: capNum.toFixed(2),
        currency,
        allowed_categories: allowedCategories,
        blocked_categories: blockedCategories,
        allowed_retailers: allowedRetailers,
        max_quantity_per_product: Number(maxQuantity),
        price_tolerance_pct: Number(priceTolerance),
      })
      await refreshMandate()
      setSuccessMessage('Spending mandate version updated successfully.')
      setTimeout(() => {
        onSuccess()
      }, 1000)
    } catch (err: any) {
      setError(err?.message || 'Failed to update spending mandate.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-sm flex items-center gap-2">
          <AlertCircle size={18} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-sm font-semibold">
          {successMessage}
        </div>
      )}

      {/* Main Numerical Limits */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Input
          label="Total Budget ($)"
          type="number"
          step="0.01"
          min="1"
          value={totalBudget}
          onChange={(e) => setTotalBudget(e.target.value)}
          required
        />
        <Input
          label="Per-Item Cap ($)"
          type="number"
          step="0.01"
          min="1"
          value={perItemCap}
          onChange={(e) => setPerItemCap(e.target.value)}
          required
        />
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold tracking-wide uppercase text-neutral-600 dark:text-neutral-400">
            Currency
          </label>
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className="w-full rounded-full bg-white dark:bg-[#1C1E24] text-neutral-900 dark:text-neutral-100 border border-neutral-200 dark:border-neutral-700 text-sm py-2.5 px-4 outline-hidden"
          >
            <option value="USD">USD ($)</option>
            <option value="EUR">EUR (€)</option>
            <option value="GBP">GBP (£)</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Input
          label="Max Quantity per Item"
          type="number"
          min="1"
          max="10"
          value={maxQuantity}
          onChange={(e) => setMaxQuantity(Number(e.target.value))}
          required
        />
        <Input
          label="Price Change Tolerance (± %)"
          type="number"
          min="0"
          max="50"
          value={priceTolerance}
          onChange={(e) => setPriceTolerance(Number(e.target.value))}
          helperText="Allows minor price fluctuations at retailer checkout"
          required
        />
      </div>

      {/* Allowed Categories Tag Editor */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold tracking-wide uppercase text-neutral-600 dark:text-neutral-400">
          Allowed Shopping Categories
        </label>
        <div className="flex flex-wrap gap-2 mb-2">
          {allowedCategories.map((cat) => (
            <span
              key={cat}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 border border-neutral-200 dark:border-neutral-700"
            >
              {cat}
              <button
                type="button"
                onClick={() => handleRemoveCategory(cat)}
                className="text-neutral-400 hover:text-neutral-700 dark:hover:text-white"
              >
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <Input
            placeholder="Add category (e.g. Lighting, Electronics)"
            value={newCatInput}
            onChange={(e) => setNewCatInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                handleAddCategory()
              }
            }}
          />
          <Button type="button" variant="outline" size="sm" onClick={handleAddCategory}>
            <Plus size={14} /> Add
          </Button>
        </div>
      </div>

      {/* Allowed Retailers Tag Editor */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold tracking-wide uppercase text-neutral-600 dark:text-neutral-400">
          Approved Retailer Domains
        </label>
        <div className="flex flex-wrap gap-2 mb-2">
          {allowedRetailers.map((ret) => (
            <span
              key={ret}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 border border-neutral-200 dark:border-neutral-700"
            >
              {ret}
              <button
                type="button"
                onClick={() => handleRemoveRetailer(ret)}
                className="text-neutral-400 hover:text-neutral-700 dark:hover:text-white"
              >
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <Input
            placeholder="Add retailer domain (e.g. target.com, bestbuy.com)"
            value={newRetailerInput}
            onChange={(e) => setNewRetailerInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                handleAddRetailer()
              }
            }}
          />
          <Button type="button" variant="outline" size="sm" onClick={handleAddRetailer}>
            <Plus size={14} /> Add
          </Button>
        </div>
      </div>

      {/* Blocked Categories Tag Editor */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold tracking-wide uppercase text-neutral-600 dark:text-neutral-400">
          Strictly Blocked Categories
        </label>
        <div className="flex flex-wrap gap-2 mb-2">
          {blockedCategories.map((cat) => (
            <span
              key={cat}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/20"
            >
              ✕ {cat}
              <button
                type="button"
                onClick={() => handleRemoveBlocked(cat)}
                className="text-rose-400 hover:text-rose-700 dark:hover:text-rose-300"
              >
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <Input
            placeholder="Add blocked category (e.g. Alcohol, Tobacco)"
            value={newBlockedInput}
            onChange={(e) => setNewBlockedInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                handleAddBlocked()
              }
            }}
          />
          <Button type="button" variant="outline" size="sm" onClick={handleAddBlocked}>
            <Plus size={14} /> Add
          </Button>
        </div>
      </div>

      <div className="flex items-center justify-end gap-3 pt-4 border-t border-neutral-100 dark:border-neutral-800">
        <Button type="button" variant="ghost" onClick={onSuccess}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" loading={isSubmitting} icon={<Save size={16} />}>
          Save Mandate Changes
        </Button>
      </div>
    </form>
  )
}
