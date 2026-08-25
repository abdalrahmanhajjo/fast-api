import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import SimpleSelect from './SimpleSelect'
export default function Pagination({ page, totalPages, total, limit, onPage, onLimit }) {
  return (
    <div className="flex flex-col gap-4 border-t border-border px-4 py-4 sm:flex-row sm:items-center">
      <p className="text-xs text-muted-foreground">
        {total
          ? `${total} matching identit${total === 1 ? 'y' : 'ies'} · page ${page} of ${totalPages}`
          : 'No identities match this view'}
      </p>
      <div className="ml-auto flex items-center gap-2">
        <SimpleSelect
          ariaLabel="Rows per page"
          className="h-9 w-24"
          value={String(limit)}
          onValueChange={(value) => onLimit(Number(value))}
          options={[5, 10, 25, 50].map((number) => ({
            value: String(number),
            label: `${number} rows`,
          }))}
        />
        <Button
          variant="outline"
          size="icon"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          disabled={page >= totalPages}
          onClick={() => onPage(page + 1)}
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
