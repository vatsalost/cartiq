import React from 'react'
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'

export const ThemeToggle: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className={`w-8 h-8 rounded-lg flex items-center justify-center border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#17191C] text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors cursor-pointer ${className}`}
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
      aria-label="Toggle theme"
    >
      {theme === 'light' ? (
        <Moon size={15} />
      ) : (
        <Sun size={15} className="text-amber-400" />
      )}
    </button>
  )
}
