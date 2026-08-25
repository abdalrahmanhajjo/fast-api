import { ArrowLeft, LockKeyhole } from 'lucide-react'
import { Link } from 'react-router-dom'
export default function ForbiddenPage() {
  return (
    <section className="grid min-h-[60dvh] place-items-center text-center">
      <div>
        <span className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-destructive/10 text-destructive">
          <LockKeyhole className="h-7 w-7" />
        </span>
        <p className="eyebrow mt-7">403 / Access boundary</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          This workspace requires admin access.
        </h1>
        <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-muted-foreground">
          Your identity is valid, but its current role does not permit user operations.
        </p>
        <Link
          to="/profile"
          className="mt-7 inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-medium"
        >
          <ArrowLeft className="h-4 w-4" />
          Return to profile
        </Link>
      </div>
    </section>
  )
}
