import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react'

export type Theme = 'light' | 'dark' | 'system'
interface ThemeContextValue {
  theme: Theme
  setTheme: (theme: Theme) => void
}
const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem('authdesk_theme') as Theme) || 'system',
  )
  useEffect(() => {
    const dark =
      theme === 'dark' || (theme === 'system' && matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('authdesk_theme', theme)
  }, [theme])
  return (
    <ThemeContext.Provider value={useMemo(() => ({ theme, setTheme }), [theme])}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used inside <ThemeProvider>')
  return context
}
