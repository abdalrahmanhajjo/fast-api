import { CheckCircle2, X, XCircle } from 'lucide-react'
import type { ReactNode } from 'react'

import { Alert, AlertDescription } from '@/components/ui/alert'

interface FeedbackAlertProps {
  kind?: 'error' | 'success'
  children?: ReactNode
  onClose?: () => void
}

export default function FeedbackAlert({ kind = 'error', children, onClose }: FeedbackAlertProps) {
  if (!children) return null

  const Icon = kind === 'success' ? CheckCircle2 : XCircle

  return (
    <Alert variant={kind === 'error' ? 'destructive' : 'default'}>
      <Icon className="h-4 w-4" />
      <AlertDescription className="whitespace-pre-line pr-6">{children}</AlertDescription>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="absolute right-3 top-3 rounded p-1 hover:bg-foreground/5"
          aria-label="Dismiss message"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </Alert>
  )
}
