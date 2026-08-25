import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { TooltipProvider } from '@/components/ui/tooltip'
import {
  Activity,
  BarChart3,
  ChevronDown,
  Command,
  Home,
  LogIn,
  LogOut,
  Menu,
  Moon,
  Settings2,
  Sun,
  UserRound,
  Users,
  X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { cn, initials } from '../lib/utils'
import CommandPalette from './CommandPalette'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

const navItems = [
  { to: '/', label: 'Overview', icon: Home, public: true },
  { to: '/stats', label: 'Network health', icon: BarChart3, public: true },
  { to: '/profile', label: 'Profile', icon: UserRound, auth: true },
  { to: '/admin', label: 'User operations', icon: Users, admin: true },
]

export default function AppShell({ children }) {
  const { user, isAuthenticated, isAdmin, logout } = useAuth()
  const { theme, setTheme } = useTheme()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [commandOpen, setCommandOpen] = useState(false)

  useEffect(() => setMobileOpen(false), [location.pathname])
  useEffect(() => {
    const key = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setCommandOpen(true)
      }
    }
    window.addEventListener('keydown', key)
    return () => window.removeEventListener('keydown', key)
  }, [])

  const visible = navItems.filter(
    (item) => item.public || (item.auth && isAuthenticated) || (item.admin && isAdmin),
  )
  const signOut = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <TooltipProvider delayDuration={200}>
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <div className="min-h-dvh bg-background text-foreground">
        <header className="bg-background/88 fixed inset-x-0 top-0 z-40 border-b border-border/70 backdrop-blur-xl">
          <div className="mx-auto flex h-16 max-w-[1480px] items-center gap-5 px-4 sm:px-6 lg:px-8">
            <button
              className="rounded-lg p-2 text-muted-foreground hover:bg-accent lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation"
            >
              <Menu className="h-5 w-5" />
            </button>
            <Link to="/" className="group flex items-center gap-2.5 text-foreground no-underline">
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-foreground shadow-sm transition group-hover:-rotate-3">
                <Activity className="h-4 w-4" />
              </span>
              <span className="text-[15px] font-semibold tracking-[-.02em]">Authdesk</span>
              <span className="hidden border-l border-border pl-2.5 text-xs text-muted-foreground sm:block">
                Identity operations
              </span>
            </Link>
            <nav className="ml-4 hidden items-center gap-1 lg:flex" aria-label="Primary navigation">
              {visible.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground no-underline transition hover:bg-accent hover:text-foreground',
                      isActive && 'bg-accent text-foreground',
                    )
                  }
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </NavLink>
              ))}
            </nav>
            <div className="ml-auto flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="hidden text-muted-foreground sm:flex"
                onClick={() => setCommandOpen(true)}
              >
                <Command className="h-3.5 w-3.5" />
                Quick open{' '}
                <kbd className="ml-2 rounded border border-border bg-muted px-1.5 font-mono text-[10px]">
                  ⌘K
                </kbd>
              </Button>
              {isAuthenticated ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="flex items-center gap-2 rounded-xl p-1.5 pr-2 text-left outline-none hover:bg-accent">
                      <span className="grid h-8 w-8 place-items-center rounded-lg bg-secondary text-xs font-semibold">
                        {initials(user)}
                      </span>
                      <span className="hidden max-w-32 sm:block">
                        <span className="block truncate text-xs font-semibold">
                          {user.first_name} {user.last_name}
                        </span>
                        <span className="block text-[10px] text-muted-foreground">{user.type}</span>
                      </span>
                      <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuContent
                      align="end"
                      className="z-50 min-w-52 rounded-xl border border-border bg-card p-1.5 shadow-soft"
                    >
                      <DropdownMenuLabel className="px-2 py-2 text-xs text-muted-foreground">
                        Signed in as
                        <br />
                        <span className="text-foreground">{user.email}</span>
                      </DropdownMenuLabel>
                      <DropdownMenuSeparator className="my-1 h-px bg-border" />
                      <DropdownMenuItem onSelect={() => navigate('/profile')} className="menu-item">
                        <Settings2 className="h-4 w-4" />
                        Account settings
                      </DropdownMenuItem>
                      <DropdownMenuSub>
                        <DropdownMenuSubTrigger className="menu-item">
                          <Sun className="h-4 w-4" />
                          Appearance
                        </DropdownMenuSubTrigger>
                        <DropdownMenuPortal>
                          <DropdownMenuSubContent className="z-50 min-w-36 rounded-xl border border-border bg-card p-1.5 shadow-soft">
                            {(['light', 'dark', 'system'] as const).map((value) => (
                              <DropdownMenuItem
                                key={value}
                                className="menu-item capitalize"
                                onSelect={() => setTheme(value)}
                              >
                                {theme === value ? '✓ ' : ''}
                                {value}
                              </DropdownMenuItem>
                            ))}
                          </DropdownMenuSubContent>
                        </DropdownMenuPortal>
                      </DropdownMenuSub>
                      <DropdownMenuSeparator className="my-1 h-px bg-border" />
                      <DropdownMenuItem onSelect={signOut} className="menu-item text-destructive">
                        <LogOut className="h-4 w-4" />
                        Sign out
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenuPortal>
                </DropdownMenu>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="hidden rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground sm:block"
                  >
                    Sign in
                  </Link>
                  <Link
                    to="/register"
                    className="rounded-lg bg-primary px-3.5 py-2 text-sm font-medium text-primary-foreground shadow-sm"
                  >
                    Create account
                  </Link>
                </>
              )}
            </div>
          </div>
        </header>

        {mobileOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <button
              className="absolute inset-0 bg-zinc-950/45 backdrop-blur-sm"
              onClick={() => setMobileOpen(false)}
              aria-label="Close navigation"
            />
            <aside className="absolute inset-y-0 left-0 w-[min(86vw,320px)] border-r border-border bg-background p-5 shadow-2xl">
              <div className="mb-8 flex items-center justify-between">
                <span className="flex items-center gap-2 font-semibold">
                  <Activity className="h-5 w-5 text-primary" />
                  Authdesk
                </span>
                <button
                  className="rounded-lg p-2 hover:bg-accent"
                  onClick={() => setMobileOpen(false)}
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <nav className="grid gap-1">
                {visible.map(({ to, label, icon: Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium text-muted-foreground',
                        isActive && 'bg-accent text-foreground',
                      )
                    }
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </NavLink>
                ))}
              </nav>
              {isAuthenticated && (
                <button
                  onClick={signOut}
                  className="absolute bottom-6 left-5 right-5 flex items-center gap-3 rounded-xl px-3 py-3 text-sm text-destructive hover:bg-destructive/10"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              )}
            </aside>
          </div>
        )}

        <main
          id="main-content"
          className="mx-auto min-h-dvh max-w-[1480px] px-4 pb-16 pt-24 sm:px-6 lg:px-8"
        >
          {children}
        </main>
        <footer className="border-t border-border/70">
          <div className="mx-auto flex max-w-[1480px] flex-col gap-3 px-6 py-6 text-xs text-muted-foreground sm:flex-row sm:items-center">
            <span>Authdesk · FastAPI identity operations</span>
            <span className="sm:ml-auto">Privacy · Terms · System status</span>
          </div>
        </footer>
        <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} items={visible} />
      </div>
    </TooltipProvider>
  )
}
