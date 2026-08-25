import { ArrowRight, Database, Fingerprint, KeyRound, Radio, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function HomePage() {
  const { isAuthenticated, isAdmin, user } = useAuth()
  return (
    <div className="space-y-24 pb-12">
      <section className="grid min-h-[68dvh] items-center gap-12 py-12 lg:grid-cols-[1.05fr_.95fr]">
        <div className="max-w-3xl">
          <p className="eyebrow">Identity infrastructure, made visible</p>
          <h1 className="mt-5 text-5xl font-semibold leading-[.98] tracking-[-.065em] sm:text-6xl lg:text-7xl">
            Know who has access.
            <br />
            <span className="text-muted-foreground">Control what happens next.</span>
          </h1>
          <p className="mt-7 max-w-xl text-base leading-7 text-muted-foreground sm:text-lg">
            A focused operations layer for secure accounts, permissions, lifecycle controls, and
            real-time population insight.
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            {isAuthenticated ? (
              <>
                <Link
                  className="inline-flex h-11 items-center gap-2 rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground"
                  to={isAdmin ? '/admin' : '/profile'}
                >
                  {isAdmin ? 'Open operations' : 'Open my account'}
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  className="inline-flex h-11 items-center rounded-lg border border-border px-5 text-sm font-medium"
                  to="/stats"
                >
                  View network health
                </Link>
              </>
            ) : (
              <>
                <Link
                  className="inline-flex h-11 items-center gap-2 rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground"
                  to="/register"
                >
                  Create an account
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  className="inline-flex h-11 items-center rounded-lg border border-border px-5 text-sm font-medium"
                  to="/login"
                >
                  Sign in
                </Link>
              </>
            )}
          </div>
        </div>
        <div className="relative mx-auto w-full max-w-xl">
          <div className="absolute -inset-5 -z-10 rounded-[2rem] bg-primary/5 blur-2xl" />
          <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <span className="flex items-center gap-2 text-xs font-semibold">
                <Radio className="h-3.5 w-3.5 text-emerald-500" />
                Identity signal
              </span>
              <span className="font-mono text-[10px] text-muted-foreground">LIVE / API</span>
            </div>
            <div className="grid grid-cols-[72px_1fr]">
              <div className="border-r border-border bg-muted/30 py-6">
                {[Fingerprint, KeyRound, Database, ShieldCheck].map((Icon, i) => (
                  <div
                    key={i}
                    className={`mx-auto mb-4 grid h-9 w-9 place-items-center rounded-lg ${i === 0 ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                ))}
              </div>
              <div className="p-6 sm:p-8">
                <p className="text-xs text-muted-foreground">CURRENT SESSION</p>
                <p className="mt-2 text-2xl font-semibold tracking-tight">
                  {user ? `${user.first_name} ${user.last_name}` : 'Secure by default'}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {user
                    ? user.email
                    : 'Every protected request resolves identity against the source of truth.'}
                </p>
                <div className="my-7 h-px bg-border" />
                <div className="space-y-5">
                  {[
                    ['Token signature', 'Verified at request time'],
                    ['Role authority', 'Re-read from MongoDB'],
                    ['Account state', 'Active users only'],
                  ].map(([a, b], i) => (
                    <div key={a} className="flex items-start gap-3">
                      <span className="mt-1 grid h-5 w-5 place-items-center rounded-full bg-primary/10 text-[10px] font-bold text-primary">
                        {i + 1}
                      </span>
                      <div>
                        <p className="text-sm font-medium">{a}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">{b}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="section-rule grid gap-8 pt-10 lg:grid-cols-[.7fr_1.3fr]">
        <div>
          <p className="eyebrow">A smaller security surface</p>
          <h2 className="mt-4 text-3xl font-semibold tracking-[-.04em]">
            The controls that matter, connected.
          </h2>
        </div>
        <div className="grid gap-px overflow-hidden rounded-2xl border border-border bg-border sm:grid-cols-3">
          {[
            ['01', 'Authenticate', 'Argon2id password storage and expiring JWT access.'],
            ['02', 'Authorize', 'Database-backed role checks stop stale privilege.'],
            ['03', 'Operate', 'Search, update, deactivate, restore, and measure.'],
          ].map(([n, t, d]) => (
            <article key={n} className="bg-card p-6">
              <span className="font-mono text-xs text-primary">{n}</span>
              <h3 className="mt-10 text-lg font-semibold">{t}</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{d}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
