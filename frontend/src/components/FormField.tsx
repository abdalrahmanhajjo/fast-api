import type { ReactNode } from 'react'

import { Label } from '@/components/ui/label'

interface FormFieldProps {
  label: string
  error?: string
  hint?: string
  children: ReactNode
}

export default function FormField({ label, error, hint, children }: FormFieldProps) {
  return (
    <Label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      {children}
      {error ? (
        <span className="text-xs text-destructive">{error}</span>
      ) : hint ? (
        <span className="text-xs leading-relaxed text-muted-foreground">{hint}</span>
      ) : null}
    </Label>
  )
}
