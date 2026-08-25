import { Activity, MapPin, ScanFace, UsersRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import FeedbackAlert from '../components/FeedbackAlert'
import { Skeleton } from '@/components/ui/skeleton'

export default function StatsPage() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    Promise.all([api.statsCount(), api.statsAverageAge(), api.statsTopCities()])
      .then(([c, a, t]) =>
        setStats({ total: c.total_users, averageAge: a.average_age, cities: t.cities }),
      )
      .catch((e) => setError(e.message))
  }, [])
  if (error) return <FeedbackAlert>{error}</FeedbackAlert>
  if (!stats) return <StatsSkeleton />
  const max = Math.max(1, ...stats.cities.map((c) => c.count))
  const covered = stats.cities.reduce((n, c) => n + c.count, 0)
  return (
    <div className="space-y-14">
      <header>
        <p className="eyebrow">Public network health</p>
        <h1 className="page-title mt-4">A live view of active identities.</h1>
        <p className="page-copy">
          Only active accounts are included. Deactivated users disappear from every measure
          immediately.
        </p>
      </header>
      <section className="grid gap-10 border-y border-border py-9 md:grid-cols-3">
        <Metric
          icon={UsersRound}
          value={stats.total}
          label="Active identities"
          copy="Accounts currently permitted to authenticate."
        />
        <Metric
          icon={ScanFace}
          value={stats.averageAge}
          label="Average age"
          copy="Mean profile age across the active population."
        />
        <Metric
          icon={MapPin}
          value={stats.cities.length}
          label="Leading locations"
          copy={`${covered} identities represented in the top city ranking.`}
        />
      </section>
      <section className="grid gap-10 lg:grid-cols-[.8fr_1.2fr]">
        <div>
          <p className="eyebrow">Geographic distribution</p>
          <h2 className="mt-4 text-2xl font-semibold tracking-tight">Where the network lives</h2>
          <p className="mt-3 max-w-md text-sm leading-6 text-muted-foreground">
            A compact comparison of the three most represented cities. The longest line establishes
            the relative baseline.
          </p>
          <div className="mt-8 flex items-center gap-2 text-xs text-muted-foreground">
            <Activity className="h-4 w-4 text-emerald-500" />
            Computed directly from MongoDB
          </div>
        </div>
        <div className="space-y-7">
          {stats.cities.length ? (
            stats.cities.map((c, i) => (
              <div key={c.city} className="group grid grid-cols-[2rem_1fr_auto] items-center gap-4">
                <span className="font-mono text-xs text-muted-foreground">0{i + 1}</span>
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium">{c.city}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-sm bg-muted">
                    <span
                      className="block h-full origin-left rounded-sm bg-primary transition duration-700 group-hover:bg-primary/80"
                      style={{ width: `${(c.count / max) * 100}%` }}
                    />
                  </div>
                </div>
                <span className="data-number text-2xl font-semibold">{c.count}</span>
              </div>
            ))
          ) : (
            <p className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
              No active identities to measure yet.
            </p>
          )}
        </div>
      </section>
    </div>
  )
}
function Metric({ icon: Icon, value, label, copy }) {
  return (
    <article className="flex gap-4">
      <span className="mt-1 grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
        <Icon className="h-5 w-5" />
      </span>
      <div>
        <p className="data-number text-4xl font-semibold">{value}</p>
        <p className="mt-1 text-sm font-semibold">{label}</p>
        <p className="mt-1 max-w-xs text-xs leading-5 text-muted-foreground">{copy}</p>
      </div>
    </article>
  )
}
function StatsSkeleton() {
  return (
    <div className="space-y-12">
      <Skeleton className="h-10 w-96 max-w-full" />
      <div className="grid gap-8 md:grid-cols-3">
        {[1, 2, 3].map((x) => (
          <Skeleton key={x} className="h-28" />
        ))}
      </div>
      <Skeleton className="h-72" />
    </div>
  )
}
