import { Skeleton } from '@/components/ui/skeleton'
export default function Spinner({ label = 'Loading…' }) {
  return (
    <div className="space-y-4 py-8" role="status">
      <span className="sr-only">{label}</span>
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-36 w-full" />
      <Skeleton className="h-36 w-full" />
    </div>
  )
}
