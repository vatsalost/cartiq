import React, { useState } from 'react'
import { Plus, X, Save, AlertCircle, CheckCircle2 } from 'lucide-react'
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
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      {error && (
        <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 dark:bg-rose-500/10 dark:border-rose-500/20 dark:text-rose-400 text-xs flex items-center gap-2">
          <AlertCircle size={16} strokeWidth={1.8} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-500/20 dark:text-emerald-400 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 size={16} strokeWidth={1.8} className="shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Main Numerical Limits */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
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
          <label className="text-xs font-medium text-neutral-700 dark:text-neutral-300">
            Currency
          </label>
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className="w-full rounded-lg bg-white dark:bg-[#1C1F24] text-neutral-900 dark:text-neutral-100 border border-neutral-200 dark:border-neutral-700/80 text-xs py-2 px-3 outline-hidden"
          >
            <option value="USD">USD ($)</option>
            <option value="EUR">EUR (€)</option>
            <option value="GBP">GBP (£)</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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

      {/* Category & Retailer Tag Editors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        {/* Allowed Categories */}
        <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 flex flex-col gap-2.5">
          <label className="text-xs font-semibold text-neutral-800 dark:text-neutral-200">
            Allowed Categories
          </label>
          <div className="flex flex-wrap gap-1.5 min-h-[40px]">
            {allowedCategories.map((cat) => (
              <span
                key={cat}
                className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-medium bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-800 dark:text-neutral-200"
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
          <div className="flex items-center gap-2 mt-1">
            <input
              type="text"
              placeholder="Add category (e.g. Electronics)"
              value={newCatInput}
              onChange={(e) => setNewCatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddCategory())}
              className="flex-1 text-xs rounded-lg bg-white dark:bg-[#1C1F24] border border-neutral-200 dark:border-neutral-700/80 px-3 py-1.5 outline-hidden text-neutral-900 dark:text-white"
            />
            <Button type="button" variant="outline" size="xs" onClick={handleAddCategory}>
              Add
            </Button>
          </div>
        </div>

        {/* Approved Retailers */}
        <div className="p-4 rounded-xl bg-neutral-50 dark:bg-[#141619] border border-neutral-200/80 dark:border-neutral-800 flex flex-col gap-2.5">
          <label className="text-xs font-semibold text-neutral-800 dark:text-neutral-200">
            Approved Retailers
          </label>
          <div className="flex flex-wrap gap-1.5 min-h-[40px]">
            {allowedRetailers.map((ret) => (
              <span
                key={ret}
                className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-medium bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-800 dark:text-neutral-200"
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
          <div className="flex items-center gap-2 mt-1">
            <input
              type="text"
              placeholder="Add domain (e.g. amazon.com)"
              value={newRetailerInput}
              onChange={(e) => setNewRetailerInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddRetailer())}
              className="flex-1 text-xs rounded-lg bg-white dark:bg-[#1C1F24] border border-neutral-200 dark:border-neutral-700/80 px-3 py-1.5 outline-hidden text-neutral-900 dark:text-white"
            />
            <Button type="button" variant="outline" size="xs" onClick={handleAddRetailer}>
              Add
            </Button>
          </div>
        </div>
      </div>

      {/* Blocked Categories */}
      <div className="p-4 rounded-xl bg-rose-50/40 dark:bg-rose-950/10 border border-rose-200/60 dark:border-rose-900/30 flex flex-col gap-2.5">
        <label className="text-xs font-semibold text-rose-800 dark:text-rose-300">
          Strictly Blocked Categories
        </label>
        <div className="flex flex-wrap gap-1.5 min-h-[36px]">
          {blockedCategories.map((cat) => (
            <span
              key={cat}
              className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-medium bg-white dark:bg-neutral-900 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-400"
            >
              {cat}
              <button
                type="button"
                onClick={() => handleRemoveBlocked(cat)}
                className="text-rose-400 hover:text-rose-700"
              >
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <input
            type="text"
            placeholder="Add blocked category (e.g. Alcohol)"
            value={newBlockedInput}
            onChange={(e) => setNewBlockedInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddBlocked())}
            className="flex-1 text-xs rounded-lg bg-white dark:bg-[#1C1F24] border border-rose-200 dark:border-rose-900/50 px-3 py-1.5 outline-hidden text-neutral-900 dark:text-white"
          />
          <Button type="button" variant="outline" size="xs" onClick={handleAddBlocked}>
            Block
          </Button>
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex items-center justify-end gap-3 pt-3 border-t border-neutral-100 dark:border-neutral-800">
        <Button type="submit" variant="primary" size="md" loading={isSubmitting} icon={<Save size={16} strokeWidth={1.8} />}>
          Save New Mandate Version
        </Button>
      </div>
    </form>
  )
}
