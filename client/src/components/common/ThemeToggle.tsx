import React from 'react'
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'

export const ThemeToggle: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className={`relative w-10 h-10 rounded-full flex items-center justify-center border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-[#1A1D23] text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800/80 transition-all shadow-[1px_2px_0px_rgba(0,0,0,0.06)] dark:shadow-none cursor-pointer ${className}`}
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
      aria-label="Toggle theme"
    >
      {theme === 'light' ? (
        <Moon size={18} className="text-neutral-800 transition-transform rotate-0 hover:-rotate-12" />
      ) : (
        <Sun size={18} className="text-amber-400 transition-transform rotate-0 hover:rotate-45" />
      )}
    </button>
  )
}
