import { ArrowLeft, Waypoints } from 'lucide-react'
import { Link } from 'react-router-dom'
export default function NotFoundPage() {
  return (
    <section className="grid min-h-[60dvh] place-items-center text-center">
      <div>
        <span className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-primary/10 text-primary">
          <Waypoints className="h-7 w-7" />
        </span>
        <p className="eyebrow mt-7">404 / Route missing</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          This path is outside the network.
        </h1>
        <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-muted-foreground">
          The page may have moved, or the address may be incomplete.
        </p>
        <Link
          to="/"
          className="mt-7 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to overview
        </Link>
      </div>
    </section>
  )
}
